from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from allauth.socialaccount.models import SocialAccount


from .models import Issue, Type, Severity, Status, Priority, Watch, Assigned, Comments, Attachment, UserProfile
from .forms import EditParamsForm, CommentForm, BulkIssueForm, EditBioForm

from .filters import IssueFilter

from django.utils import timezone

from django.db.models import Max
from django.db.models import F, Subquery, OuterRef 
from django.contrib import messages

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from .serializers import (
    AttachmentSerializer, IssueSerializer, PrioritySerializer, TypeSerializer, StatusSerializer, SeveritySerializer, 
    UserProfileSerializer, IssueWithCommentsSerializer, BulkTitlesSerializer, UserProfileDetailSerializer,
    UserBioSerializer
)



@login_required
def showAllIssues(request):
    bulkForm = BulkIssueForm()
    
    sort_by = request.GET.get('sort_by', '-modified') 
    show_filters = request.GET.get('show_filters') == '1'
    valid_sort_fields = ['type__position', 'severity__position', 'priority__position', 'status__position', 'modified_at']
    if sort_by.lstrip('-') not in valid_sort_fields:
        sort_by = '-modified_at'

    order_by_field = f'{sort_by.lstrip("-")}'
    if sort_by.startswith('-'):
        order_by_field = f'-{order_by_field}'

    issues = IssueFilter(request.GET, queryset=Issue.objects.all().order_by(order_by_field))

    if request.method == "POST":
        form = BulkIssueForm(request.POST)
        if form.is_valid():
            crearIssues(request, form)
            return redirect("/issues")  
    else:
        form = BulkIssueForm()

    return render(request, "showAllIssues.html", {'issues': issues.qs, 'filter': issues, 'bulkForm': bulkForm, 'show_filters': show_filters})
    
def crearIssues(request, form):
    lines = form.cleaned_data["bulk_text"].splitlines()
    issues = [Issue(subject=line.strip(), status=Status.objects.order_by('positon').first(), type=Type.objects.order_by('positon').first(),
                    severity=Severity.objects.order_by('positon').first(), priority=Priority.objects.order_by('positon').first(), 
                    created_by=SocialAccount.objects.filter(user=request.user, provider="google").first()) for line in lines if line.strip()]
    Issue.objects.bulk_create(issues)

@login_required
def createIssue(request):
    if request.method == 'POST':
        # Obtener valores del formulario
        subject = request.POST.get('Subject')
        description = request.POST.get('description')
        priority_name = request.POST.get('priority')
        type_name = request.POST.get('type')
        severity_name = request.POST.get('severity')
        status_name = request.POST.get('status')
        deadline = request.POST.get('deadline')
        attachments_description = request.POST.get('attachments_description', '')

        # Recuperar objetos de la base de datos
        priority = Priority.objects.get(name=priority_name)
        typeT = Type.objects.get(name=type_name)
        severity = Severity.objects.get(name=severity_name)
        status = Status.objects.get(name=status_name)

        # Crear y guardar el issue
        new_issue = Issue(
            subject=subject,
            description=description,
            priority=priority,
            type=typeT,
            severity=severity,
            status=status,
            deadline=deadline or None,
            created_by= SocialAccount.objects.filter(user=request.user, provider="google").first() 
        )
        new_issue.save()

        # Procesar archivos adjuntos
        files = request.FILES.getlist('attachments')
        for file in files:
            filesize = file.size
            attachment = Attachment(
                issue=new_issue,
                file=file,
                filename=file.name,
                filesize=filesize,
                description=attachments_description,
            )
            attachment.save()

        return redirect('/issues')  

    # Obtener datos para los selectores
    priorities = Priority.objects.all()
    types = Type.objects.all()
    severities = Severity.objects.all()
    status = Status.objects.all()
    
    # Pasar los datos al contexto del template
    return render(request, 'createIssue.html', {
        'priorities': priorities,
        'types': types,
        'severities': severities,
        'status' : status
    })
    
@login_required
def issueDetail(request, id):
    issue = Issue.objects.get(id=id)
    watchers = list(Watch.objects.filter(issue=issue))
    is_watching = Watch.objects.filter(watcher=SocialAccount.objects.filter(user=request.user, provider="google").first(), issue=issue).exists()
    assigneds = list(Assigned.objects.filter(issue=issue))
    is_assigned = Assigned.objects.filter(assigned=SocialAccount.objects.filter(user=request.user, provider="google").first(), issue=issue).exists()
    users = SocialAccount.objects.all()
    
    comments = Comments.objects.filter(issue=issue)
    commentForm = CommentForm()

    attachments = Attachment.objects.filter(issue=issue)
    
    paramform = EditParamsForm(initial={
        "priority": issue.priority.name,
        "type": issue.type.name,
        "severity": issue.severity.name,
        "status": issue.status.name,
        # Quitamos la deadline de aquí para evitar edición duplicada
    })

    if request.method == "POST":
        if 'back' in request.POST:
            return redirect('/issues')
        elif 'edit_params' in request.POST:
            form = EditParamsForm(request.POST)
            print(request.POST)
            if form.is_valid():
                # Guardar los cambios en la base de datos
                issue.priority = form.cleaned_data['priority']
                issue.type = form.cleaned_data['type']
                issue.severity = form.cleaned_data['severity']
                issue.status = form.cleaned_data['status']
                # No guardamos deadline aquí, se maneja por separado
                issue.save()
            return redirect(reverse("issueDetail", args=[issue.id]))
        
        elif 'subject' in request.POST:    
            issue.subject = request.POST.get("subject", issue.subject)
            issue.save()
            return redirect(reverse("issueDetail", args=[issue.id])) 
        
        elif 'description' in request.POST:
            issue.description = request.POST.get("description", issue.description)
            issue.save()
            return redirect(reverse("issueDetail", args=[issue.id]))

        elif 'deadline' in request.POST:
            deadline = request.POST.get("deadline", "")
            issue.deadline = deadline if deadline else None
            issue.save()
            return redirect(reverse("issueDetail", args=[issue.id]))

        elif 'delete' in request.POST:
            issue.delete()
            return redirect('/issues')
        
        elif 'setWatcher' in request.POST:
            watcher = SocialAccount.objects.filter(user=request.user, provider="google").first()
            if not Watch.objects.filter(watcher=watcher, issue=issue).exists():
                watch = Watch(watcher=watcher, issue=issue)
                watch.save()
            return redirect(reverse("issueDetail", args=[issue.id]))
        
        elif 'unsetWatcher' in request.POST:
            watcher = SocialAccount.objects.filter(user=request.user, provider="google").first()
            watch = Watch.objects.filter(watcher=watcher, issue=issue).first()
            if watch:
                watch.delete()
            return redirect(reverse("issueDetail", args=[issue.id]))
        
        elif 'setAssigned' in request.POST:
            assigned = SocialAccount.objects.filter(user=request.user, provider="google").first()
            if not Assigned.objects.filter(assigned=assigned, issue=issue).exists():
                assign = Assigned(assigned=assigned, issue=issue)
                assign.save()
            return redirect(reverse("issueDetail", args=[issue.id]))

        elif 'unsetAssigned' in request.POST:
            assigned = SocialAccount.objects.filter(user=request.user, provider="google").first()
            assign = Assigned.objects.filter(assigned=assigned, issue=issue).first()
            if assign:
                assign.delete()
            return redirect(reverse("issueDetail", args=[issue.id]))
        
        elif 'addAssigned' in request.POST:
            assigned_id = request.POST.get("assigned_user")
            assigned = SocialAccount.objects.filter(id=assigned_id).first()
            if not Assigned.objects.filter(assigned=assigned, issue=issue).exists():
                assign = Assigned(assigned=assigned, issue=issue)
                assign.save()
            return redirect(reverse("issueDetail", args=[issue.id]))
        
        elif 'watcher_user' in request.POST:
            watcher_id = request.POST.get("watcher_user")
            watcher = SocialAccount.objects.filter(id=watcher_id).first()
            if not Watch.objects.filter(watcher=watcher, issue=issue).exists():
                watch = Watch(watcher=watcher, issue=issue)
                watch.save()
            return redirect(reverse("issueDetail", args=[issue.id]))
        
        elif 'deleteWatcher' in request.POST:
            watcher_id = request.POST.get('delete_watcher_id')
            watcher = Watch.objects.filter(id=watcher_id)
            if watcher:
                watcher.delete()
            return redirect(reverse("issueDetail", args=[issue.id]))
        
        elif 'deleteAssigned' in request.POST:
            assigned_id = request.POST.get('delete_assigned_id')
            assigned = Assigned.objects.filter(id=assigned_id)
            if assigned:
                assigned.delete()
            return redirect(reverse("issueDetail", args=[issue.id]))

        elif 'upload_attachment' in request.POST:
            files = request.FILES.getlist('new_attachments')
            description = request.POST.get('attachment_description', '')
            
            for file in files:
                filesize = file.size
                attachment = Attachment(
                    issue=issue,
                    file=file,
                    filename=file.name,
                    filesize=filesize,
                    description=description,
                )
                attachment.save()
            return redirect(reverse("issueDetail", args=[issue.id]))
            
        elif 'delete_attachment' in request.POST:
            attachment_id = request.POST.get('attachment_id')
            try:
                attachment = Attachment.objects.get(id=attachment_id, issue=issue)
                attachment.file.delete()
                attachment.delete()
            except Attachment.DoesNotExist:
                pass
            return redirect(reverse("issueDetail", args=[issue.id]))
            
        elif 'add_comment' in request.POST:
            commentForm = CommentForm(request.POST)
            if commentForm.is_valid():
                com = Comments(comment = commentForm.cleaned_data['comment'], issue = issue)
                com = commentForm.save(commit=False)
                com.user = SocialAccount.objects.filter(user=request.user, provider="google").first()
                com.issue = issue
                print(timezone.now())
                com.save()
        return redirect(reverse("issueDetail", args=[issue.id]))

    return render(request, "issueDetail.html", {"issue": issue, "paramform": paramform, 
                                                "assigneds": assigneds, "is_assigned": is_assigned,
                                                "watchers": watchers, "is_watching" : is_watching,
                                                "users": users, 'comments':comments, 'commentForm':commentForm,
                                                "attachments": attachments })

def login(request):
    return render(request, "login.html")

@login_required
def settings(request):
    return render(request, 'settings.html')

@login_required
def user_profiles(request):
    users = SocialAccount.objects.all()
    return render(request, 'user_profiles.html', {'users': users})

@login_required
def user_profile(request, id):
    user = SocialAccount.objects.get(id=id)
    profile, created = UserProfile.objects.get_or_create(user_id=id)
    token = Token.objects.get(user=user.user)
    active_tab = request.GET.get('tab', 'assigned-issues') 
    sort_by = request.GET.get('sort_by', '-modified_at') 
    edit_bio = request.GET.get('edit_bio', 'false') == 'true'

    valid_sort_fields = ['type__position', 'severity__position', 'priority__position', 'status__position', 'modified_at']
    if sort_by.lstrip('-') not in valid_sort_fields:
        sort_by = '-modified_at'

    order_by_field = f'issue__{sort_by.lstrip("-")}'
    if sort_by.startswith('-'):
        order_by_field = f'-{order_by_field}'

    if request.method == 'POST':
        # Handle avatar upload
        if 'upload_avatar' in request.POST and request.FILES.get('avatar'):
            try:
                if profile.avatar:
                    profile.delete_avatar()  # Delete old avatar if it exists
                profile.avatar = request.FILES['avatar']
                profile.save()
                messages.success(request, 'Avatar uploaded successfully!')
            except Exception as e:
                messages.error(request, f'Error uploading avatar: {str(e)}')
            return redirect('user_profile', id=id)
            
        # Handle avatar deletion
        elif 'delete_avatar' in request.POST:
            profile.delete_avatar()
            messages.success(request, 'Avatar removed')
            return redirect('user_profile', id=id)
            
        # Handle bio form
        form = EditBioForm(request.POST, instance=profile)
        if form.is_valid():
            profile.bio = form.cleaned_data['bio']
            form.save()
            return redirect('user_profile', id=id)
    else:
        form = EditBioForm(instance=profile)

    assigned_issues = Assigned.objects.filter(assigned=user, issue__status__isClosed=False).select_related('issue').order_by(order_by_field)
    watched_issues = Watch.objects.filter(watcher=user).select_related('issue').order_by(order_by_field)
    comments = Comments.objects.filter(user_id=id).select_related('issue').order_by(f'-created_at')

    context = {
        'username': user.user.username,
        'email': user.user.email,
        'full_name': f"{user.user.first_name} {user.user.last_name}",
        'watched_issues': watched_issues,
        'assigned_issues': assigned_issues,
        'comments': comments,
        'Numassigned_issues': len(assigned_issues),
        'Numwatched_issues': len(watched_issues),
        'Numcomments': len(comments),
        'bio': profile.bio,
        'profile': profile,
        'form': form,
        'active_tab': active_tab,
        'edit_bio': edit_bio,
        'messages': messages.get_messages(request),
        'token': token.key,
        'is_own_profile': request.user.id == user.user.id,
    }
    return render(request, 'user_profile.html', context)

@login_required
def priorities_settings(request):
    priorities = Priority.objects.all().order_by('position')
    if request.method == "POST":
        action = request.POST.get('action')
        print(f"Action: {action}")
        if action not in( 'add_new', 'edit_name', 'start_editting', 'new_color'):
            priority_name = request.POST.get('priority_name')
            priority = Priority.objects.get(name=priority_name)

        if action == 'delete_priority':
            priority.delete()

            if "write a name for the new element" not in priority_name.lower():
                messages.success(request, f'Priority "{priority_name}" succesfully deleted')
            return redirect('priorities')  

        elif action == 'add_new':
            max_position = priorities.aggregate(Max('position'))['position__max'] or 0
            new_name = f"New Priority {max_position + 1}"

            if not Priority.objects.filter(name=new_name).exists():
                Priority.objects.create(
                    name="Write a name for the new element",
                    color="#808080", 
                    position=max_position + 1
                )

            return redirect('priorities')

        elif action == 'edit_name':
            original_name = request.POST.get('original_name')
            new_name = request.POST.get('new_name')
            if new_name.strip():
                priority = Priority.objects.get(name=original_name)
                priority.name = new_name.strip()

                priority.save()
                #logica per eliminar els elements editats antics, perque como es primary key no es pot editar
                if  new_name.strip() != original_name:
                    prioritytoDelete = Priority.objects.get(name=original_name)
                    prioritytoDelete.delete()

                Priority.objects.filter(name="Write a name for the new element").exclude(pk=priority.pk).delete()
                if original_name == "Write a name for the new element": 
                    messages.success(request, f'Priority "{new_name}" succesfully created')
                else: 
                    messages.success(request, f'Priority "{new_name}" succesfully modified')

            return redirect('priorities')

        elif action == 'new_color':
            
            original_name = request.POST.get('original_name')
            new_color = request.POST.get('new_color')
        
            priority = Priority.objects.get(name=original_name)
            priority.color = new_color
            priority.save()
            return redirect('priorities')

        elif action == 'start_editting':

            prioName = request.POST.get('priority_name')

            # Este contexto extra indica a la plantilla que estamos editando ese nombre
            priority = Priority.objects.get(name=prioName)
            return render(request, 'priorities.html', {
            'priorities': Priority.objects.all().order_by('position'),
            'editing_name': priority.name,
            'messages': messages.get_messages(request),
            })

        elif "moveUp" in request.POST:

            if priority.position > 1:  
                previous_priority = Priority.objects.get(position=priority.position - 1)
                priority.position -= 1
                previous_priority.position += 1
                priority.save()
                previous_priority.save()
            print("Moved up")

        elif "move_down" in request.POST:

            if priority.position < len(priorities):
                    next_priority = Priority.objects.get(position=priority.position + 1)
                    # Intercambiar las posiciones
                    priority.position += 1
                    next_priority.position -= 1
                    priority.save()
                    next_priority.save()
            print("Moved down")

        return redirect("priorities")  

    return render(request, 'priorities.html', {'priorities': priorities})

@login_required
def statuses_settings(request):
    statuses = Status.objects.all().order_by('position')
    if request.method == "POST":
        action = request.POST.get('action')
        print(f"Action: {action}")
        if action not in( 'add_new', 'edit_name', 'start_editting', 'new_color'):
            status_name = request.POST.get('status_name')
            status = Status.objects.get(name=status_name)

        if action == 'delete_status':
            status.delete()

            if "write a name for the new element" not in status_name.lower():
                messages.success(request, f'Status "{status_name}" succesfully deleted')
            return redirect('statuses')  

        elif action == 'add_new':
            max_position = statuses.aggregate(Max('position'))['position__max'] or 0
            new_name = f"New Status {max_position + 1}"

            if not Status.objects.filter(name=new_name).exists():
                Status.objects.create(
                    name="Write a name for the new element",
                    color="#808080", 
                    position=max_position + 1
                )

            return redirect('statuses')

        elif action == 'edit_name':
            original_name = request.POST.get('original_name')
            new_name = request.POST.get('new_name')
            if new_name.strip():
                status = Status.objects.get(name=original_name)
                status.name = new_name.strip()

                status.save()
                #logica per eliminar els elements editats antics, perque como es primary key no es pot editar
                if  new_name.strip() != original_name:
                    statustoDelete = Status.objects.get(name=original_name)
                    statustoDelete.delete()

                Status.objects.filter(name="Write a name for the new element").exclude(pk=status.pk).delete()

                messages.success(request, f'Status "{new_name}" succesfully modified')

            return redirect('statuses')

        elif action == 'new_color':
            
            original_name = request.POST.get('original_name')
            new_color = request.POST.get('new_color')
        
            status = Status.objects.get(name=original_name)
            status.color = new_color
            status.save()
            return redirect('statuses')

        elif action == 'start_editting':

            statusName = request.POST.get('status_name')

            # Este contexto extra indica a la plantilla que estamos editando ese nombre
            status = Status.objects.get(name=statusName)
            return render(request, 'statuses.html', {
            'statuses': Status.objects.all().order_by('position'),
            'editing_name': status.name,
            'messages': messages.get_messages(request),
            })

        elif "moveUp" in request.POST:

            if status.position > 1:  
                previous_status = Status.objects.get(position=status.position - 1)
                status.position -= 1
                previous_status.position += 1
                status.save()
                previous_status.save()
            print("Moved up")

        elif "move_down" in request.POST:

            if status.position < len(statuses):
                    next_status = Status.objects.get(position=status.position + 1)
                    # Intercambiar las posiciones
                    status.position += 1
                    next_status.position -= 1
                    status.save()
                    next_status.save()
            print("Moved down")

        return redirect("statuses")  

    return render(request, 'statuses.html', {'statuses': statuses})

@login_required
def severities_settings(request):
    severities = Severity.objects.all().order_by('position')
    if request.method == "POST":
        action = request.POST.get('action')
        print(f"Action: {action}")
        if action not in( 'add_new', 'edit_name', 'start_editting', 'new_color'):
            severity_name = request.POST.get('severity_name')
            severity = Severity.objects.get(name=severity_name)

        if action == 'delete_severity':
            severity.delete()

            if "write a name for the new element" not in severity_name.lower():
                messages.success(request, f'Status "{severity_name}" succesfully deleted')
            return redirect('severities')  

        elif action == 'add_new':
            max_position = severities.aggregate(Max('position'))['position__max'] or 0
            new_name = f"New Status {max_position + 1}"

            if not Severity.objects.filter(name=new_name).exists():
                Severity.objects.create(
                    name="Write a name for the new element",
                    color="#808080", 
                    position=max_position + 1
                )

            return redirect('severities')

        elif action == 'edit_name':
            original_name = request.POST.get('original_name')
            new_name = request.POST.get('new_name')
            if new_name.strip():
                severity = Severity.objects.get(name=original_name)
                severity.name = new_name.strip()

                severity.save()
                #logica per eliminar els elements editats antics, perque como es primary key no es pot editar
                if  new_name.strip() != original_name:
                    severitytoDelete = Severity.objects.get(name=original_name)
                    severitytoDelete.delete()

                Severity.objects.filter(name="Write a name for the new element").exclude(pk=severity.pk).delete()

                messages.success(request, f'Severity "{new_name}" succesfully modified')

            return redirect('severities')

        elif action == 'new_color':
            
            original_name = request.POST.get('original_name')
            new_color = request.POST.get('new_color')
        
            severity = Severity.objects.get(name=original_name)
            severity.color = new_color
            severity.save()
            return redirect('severities')

        elif action == 'start_editting':

            severityName = request.POST.get('severity_name')

            # Este contexto extra indica a la plantilla que estamos editando ese nombre
            severity = Severity.objects.get(name=severityName)
            return render(request, 'severities.html', {
            'severities': Severity.objects.all().order_by('position'),
            'editing_name': severity.name,
            'messages': messages.get_messages(request),
            })

        elif "moveUp" in request.POST:

            if severity.position > 1:  
                previous_severity = Severity.objects.get(position=severity.position - 1)
                severity.position -= 1
                previous_severity.position += 1
                severity.save()
                previous_severity.save()
            print("Moved up")

        elif "move_down" in request.POST:

            if severity.position < len(severities):
                    next_severity = Severity.objects.get(position=severity.position + 1)
                    # Intercambiar las posiciones
                    severity.position += 1
                    next_severity.position -= 1
                    severity.save()
                    next_severity.save()
            print("Moved down")

        return redirect("severities")  

    return render(request, 'severities.html', {'severities': severities})

@login_required
def types_settings(request):
    types = Type.objects.all().order_by('position')
    if request.method == "POST":
        action = request.POST.get('action')
        print(f"Action: {action}")
        if action not in( 'add_new', 'edit_name', 'start_editting', 'new_color'):
            type_name = request.POST.get('type_name')
            type = Type.objects.get(name=type_name)

        if action == 'delete_type':
            type.delete()

            if "write a name for the new element" not in type_name.lower():
                messages.success(request, f'Type "{type_name}" succesfully deleted')
            return redirect('types')  

        elif action == 'add_new':
            max_position = types.aggregate(Max('position'))['position__max'] or 0
            new_name = f"New Type {max_position + 1}"

            if not Type.objects.filter(name=new_name).exists():
                Type.objects.create(
                    name="Write a name for the new element",
                    color="#808080", 
                    position=max_position + 1
                )

            return redirect('types')

        elif action == 'edit_name':
            original_name = request.POST.get('original_name')
            new_name = request.POST.get('new_name')
            if new_name.strip():
                type = Type.objects.get(name=original_name)
                type.name = new_name.strip()

                type.save()
                #logica per eliminar els elements editats antics, perque como es primary key no es pot editar
                if  new_name.strip() != original_name:
                    typetoDelete = Type.objects.get(name=original_name)
                    typetoDelete.delete()

                Type.objects.filter(name="Write a name for the new element").exclude(pk=type.pk).delete()

                messages.success(request, f'Type "{new_name}" succesfully modified')

            return redirect('types')

        elif action == 'new_color':
            
            original_name = request.POST.get('original_name')
            new_color = request.POST.get('new_color')
        
            type = Type.objects.get(name=original_name)
            type.color = new_color
            type.save()
            return redirect('types')

        elif action == 'start_editting':

            prioName = request.POST.get('type_name')

            # Este contexto extra indica a la plantilla que estamos editando ese nombre
            type = Type.objects.get(name=prioName)
            return render(request, 'types.html', {
            'types': Type.objects.all().order_by('position'),
            'editing_name': type.name,
            'messages': messages.get_messages(request),
            })

        elif "moveUp" in request.POST:

            if type.position > 1:  
                previous_type = Type.objects.get(position=type.position - 1)
                type.position -= 1
                previous_type.position += 1
                type.save()
                previous_type.save()
            print("Moved up")

        elif "move_down" in request.POST:

            if type.position < len(types):
                    next_type = Type.objects.get(position=type.position + 1)
                    # Intercambiar las posiciones
                    type.position += 1
                    next_type.position -= 1
                    type.save()
                    next_type.save()
            print("Moved down")

        return redirect("types") 

    return render(request, 'types.html', {'types': types})

@login_required
def confirm_delete_priority(request):
    priority_name = request.GET.get('priority_name')
    priority_to_delete = get_object_or_404(Priority, name=priority_name)
    other_priorities = Priority.objects.exclude(name=priority_name).order_by('position')

    if request.method == 'POST':
        new_priority_id = request.POST.get('new_priority_id')
        new_priority = get_object_or_404(Priority, name=new_priority_id)

        # Cambiar issues a la nueva prioridad
        issues = Issue.objects.filter(priority=priority_to_delete)
        issues.update(priority=new_priority)

        # Guardar la posición de la prioridad que se va a borrar
        deleted_position = priority_to_delete.position

        # Eliminar la prioridad
        priority_to_delete.delete()

        # Reordenar prioridades
        priorities_to_update = Priority.objects.filter(position__gt=deleted_position)
        for p in priorities_to_update:
            p.position -= 1
            p.save()

        messages.success(request, f'Priority "{priority_name}" deleted and issues changed to  "{new_priority.name}".')
        return redirect('priorities')

    return render(request, 'confirm_delete_priority.html', {
        'priority': priority_to_delete,
        'other_priorities': other_priorities,
    })

@login_required
def confirm_delete_status(request):
    status_name = request.GET.get('status_name')
    status_to_delete = get_object_or_404(Status, name=status_name)
    other_statuses = Status.objects.exclude(name=status_name).order_by('position')

    if request.method == 'POST':
        new_status_id = request.POST.get('new_status_id')
        new_status = get_object_or_404(Status, name=new_status_id)

        issues = Issue.objects.filter(status=status_to_delete)
        issues.update(status=new_status)

        status_to_delete.delete()

        messages.success(request, f'Status "{status_name}" deleted and issues changed to "{new_status.name}".')
        return redirect('statuses')

    return render(request, 'confirm_delete_status.html', {
        'status': status_to_delete,
        'other_statuses': other_statuses,
    })

@login_required
def confirm_delete_severity(request):
    severity_name = request.GET.get('severity_name')
    severity_to_delete = get_object_or_404(Severity, name=severity_name)
    other_severities = Severity.objects.exclude(name=severity_name).order_by('position')
    
    if request.method == 'POST':
        new_severity_id = request.POST.get('new_severity_id')
        new_severity = get_object_or_404(Severity, name=new_severity_id)

        issues = Issue.objects.filter(severity=severity_to_delete)
        issues.update(severity=new_severity)

        severity_to_delete.delete()

        messages.success(request, f'Severity "{severity_name}" deleted and issues changed to "{new_severity.name}".')
        return redirect('severities')

    return render(request, 'confirm_delete_severity.html', {
        'severity': severity_to_delete,
        'other_severities': other_severities,
    })

@login_required
def confirm_delete_type(request):
    type_name = request.GET.get('type_name')
    type_to_delete = get_object_or_404(Type, name=type_name)
    other_types = Type.objects.exclude(name=type_name).order_by('position')
   
   
    if request.method == 'POST':
        new_type_id = request.POST.get('new_type_id')
        new_type = get_object_or_404(Type, name=new_type_id)
        issues = Issue.objects.filter(type=type_to_delete)
        issues.update(type=new_type)
        type_to_delete.delete()

        messages.success(request, f'Type "{type_name}" deleted and issues changed to  "{new_type.name}".')
        return redirect('types')

    return render(request, 'confirm_delete_type.html', {
        'type': type_to_delete,
        'other_types': other_types,
    })

#API STUFF

class IssueListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        valid_sort_fields = {
            'status': 'status__position', 
            'priority': 'priority__position', 
            'type': 'type__position', 
            'severity': 'severity__position', 
            'modified': 'modified_at',
            'assigned': 'assigned_user_id',
        }

        # Obtener parámetros de ordenación
        sort_by = request.GET.get('sortBy', '-created_at')
        sort_order = request.GET.get('sortOrder', 'desc')
        created_by = request.GET.get('created_by', None)
        assigned_to = request.GET.get('assigned_to', None)

        priority = request.GET.get('priority')
        type_ = request.GET.get('type')
        severity = request.GET.get('severity')
        issue_status = request.GET.get('status')

        def is_valid_choice(model, value):
            return model.objects.filter(name__iexact=value).exists()

        # Validación de filtros
        if priority and not is_valid_choice(Priority, priority):
            return Response({"error": f"Invalid priority: '{priority}'"}, status=status.HTTP_400_BAD_REQUEST)

        if type_ and not is_valid_choice(Type, type_):
            return Response({"error": f"Invalid type: '{type_}'"}, status=status.HTTP_400_BAD_REQUEST)

        if severity and not is_valid_choice(Severity, severity):
            return Response({"error": f"Invalid severity: '{severity}'"}, status=status.HTTP_400_BAD_REQUEST)

        if issue_status and not is_valid_choice(Status, issue_status):
            return Response({"error": f"Invalid status: '{issue_status}'"}, status=status.HTTP_400_BAD_REQUEST)

        if created_by and not UserProfile.objects.filter(user_id=created_by).exists():
            return Response({"error": f"Invalid user ID: '{created_by}'"}, status=status.HTTP_400_BAD_REQUEST)
        
        if assigned_to and not UserProfile.objects.filter(user_id=assigned_to).exists():
            return Response({"error": f"Invalid user ID: '{assigned_to}'"}, status=status.HTTP_400_BAD_REQUEST)
        


        issues = Issue.objects.all()

        # Filtro de 'assigned_to'
        if assigned_to:
            if assigned_to == '0':
                # Si se solicita asignados vacíos
                issues = issues.exclude(id__in=Assigned.objects.values('issue'))
            else:
                # Filtrar por asignado si el usuario existe, sino dejar vacío
                assigned_issues = Assigned.objects.filter(assigned__user_id=assigned_to).values_list('issue', flat=True)
                issues = issues.filter(id__in=assigned_issues)

        # Ordenación
        if sort_by.lstrip('-') not in valid_sort_fields:
            sort_by = '-created_at'

        order_by_field = valid_sort_fields.get(sort_by.lstrip('-'), 'created_at')

        if sort_order == 'asc':
            order_by_field = order_by_field.lstrip('-')
        elif sort_order == 'desc':
            order_by_field = f'-{order_by_field}'

        assigned_user_subquery = Assigned.objects.filter(issue_id=OuterRef('id')).values('assigned__user_id')[:1]

        # Realizar la subconsulta para agregar el 'assigned_user_id' al queryset
        issues = issues.annotate(
            assigned_user_id=Subquery(assigned_user_subquery)
        )

        # Filtrar y ordenar los issues
        filtered_issues = IssueFilter(request.GET, queryset=issues.order_by(order_by_field))

        # Construcción de la respuesta con los campos específicos
        response_data = []
        for issue in filtered_issues.qs:
            # Obtener el usuario asignado si existe
            assigned = Assigned.objects.filter(issue=issue).first()
            if assigned:
                user_profile = UserProfile.objects.filter(user_id=assigned.assigned.id).first()
                if user_profile:
                    assigned_data = {
                        'id': user_profile.user.id,
                        'name': user_profile.user.get_full_name(),
                        'avatar': user_profile.avatar.url if user_profile.avatar else None
                    }
                else:
                    assigned_data = None
            else:
                assigned_data = None

            issue_data = {
                'id': issue.id,
                'subject': issue.subject,
                'deadline': issue.deadline,
                'modified_at': issue.modified_at,
                'status': issue.status.name if issue.status else None,
                'type': issue.type.name if issue.type else None,
                'severity': issue.severity.name if issue.severity else None,
                'priority': issue.priority.name if issue.priority else None,
                'assigned': assigned_data
            }
            response_data.append(issue_data)

        return Response(response_data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = IssueInputSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user

            social_account = getattr(user, 'socialaccount_set', None)
            if not social_account.exists():
                return Response(
                    {'created_by': ['No se pudo determinar el creador del issue.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            issue = serializer.save(created_by=social_account.first())
            files = request.FILES.getlist('attachments')
            for f in files:
                Attachment.objects.create(
                    issue=issue,
                    file=f,
                    filename=f.name,
                    filesize=f.size,
                    uploaded_by=social_account.first()
                )
                
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class BulkCreateIssuesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            subjects = request.data.get('issues', [])
            if not isinstance(subjects, list):
                return Response({"detail": "Se requiere una lista de objetos con los títulos."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                default_priority = Priority.objects.get(position=1)
                default_type = Type.objects.get(position=1)
                default_status = Status.objects.get(position=1)
                default_severity = Severity.objects.get(position=1)
            except (Priority.DoesNotExist, Type.DoesNotExist, Status.DoesNotExist, Severity.DoesNotExist) as e:
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            social_account = getattr(request.user, 'socialaccount_set', None)
            if not social_account.exists():
                return Response(
                    {'created_by': ['No se pudo determinar el creador del issue.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            created_issues = Issue.objects.bulk_create([
                Issue(
                    subject=subject,
                    description="",
                    priority=default_priority,
                    type=default_type,
                    status=default_status,
                    severity=default_severity,
                    created_by=social_account.first(),
                )
                for subject in subjects
            ])

            serializer = IssueSerializer(created_issues, many=True)

            return Response({"created_issues": serializer.data}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Error al crear los issues: {e}")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    

class IssueDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:

            try:
                # Intentar obtener el issue por ID
                issue = Issue.objects.get(id=id)
            except Issue.DoesNotExist:
                return Response({"detail": "There's no issue with this id"}, status=status.HTTP_404_NOT_FOUND)

            # Obtener los watchers del issue 
            watchers = [
                {
                    "id": w.watcher.id,  # ID del SocialAccount
                    "name": w.watcher.extra_data.get('name', 'No Name'),
                    "avatar": (
                        UserProfile.objects.filter(user=w.watcher.user).values_list('avatar', flat=True).first()
                    )
                }
                for w in Watch.objects.filter(issue_id=id).select_related('watcher')
            ]
            for w in watchers:
                if w['avatar']:
                    user_profile = UserProfile.objects.filter(user_id=w['id']).first()
                    if user_profile and user_profile.avatar:
                        w['avatar'] = user_profile.avatar.url
                    else:
                        w['avatar'] = None

            # Obtener los assigned del issue
            assigned = [
                    {
                        "id": a.assigned.id,
                        "name": a.assigned.extra_data.get('name', 'No Name'),
                        "avatar": (
                            UserProfile.objects.filter(user=a.assigned.user).values_list('avatar', flat=True).first()
                        )
                    }
                    for a in Assigned.objects.filter(issue_id=id).select_related('assigned')
                ]
            for assignee in assigned:
                if assignee['avatar']:
                    user_profile = UserProfile.objects.filter(user_id=assignee['id']).first()
                    if user_profile and user_profile.avatar:
                        assignee['avatar'] = user_profile.avatar.url
                    else:
                        assignee['avatar'] = None

            #Obtener los attachments del issue
            attachments = Attachment.objects.filter(issue_id=id).values(
                'filename', 'filesize', 'description'
            )
            attachments_data = [
                {
                    'filename': attachment['filename'],
                    'filesize': attachment['filesize'],
                    'description': attachment['description'],
                }
                for attachment in attachments
            ]

            # Obtener los comentarios del issue
            comments = Comments.objects.filter(issue_id=id).select_related('user')

            comments_data = []
            for comment in comments:
                social_account = comment.user  # Directamente el objeto SocialAccount

                if social_account:
                    # Intentar obtener el perfil asociado para la foto
                    user_profile = UserProfile.objects.filter(user=social_account.user).first()

                    user_data = {
                        "id": social_account.id,
                        "name": social_account.extra_data.get('name', 'No Name'),
                        "picture": user_profile.avatar.url if user_profile and user_profile.avatar else None
                    }
                else:
                    user_data = {
                        "id": None,
                        "name": "Usuario Desconocido",
                        "picture": None
                    }

                comments_data.append({
                    'comment': comment.comment,
                    'user': user_data,
                    'created_at': comment.created_at
                })
            # Serializar el issue
            serializer = IssueSerializer(issue)

            # Añadir los campos adicionales de watchers y assigned
            data = serializer.data
            data['watchers'] = watchers
            data['assigned'] = assigned
            data['attachments'] = attachments_data
            data['comments'] = comments_data

            return Response(data, status=status.HTTP_200_OK)
        except Http404:
            return Response({"detail": "There's no issue with this id"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error al obtener el issue: {e}")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, id):
        try:
            issue = Issue.objects.get(id=id)
            issue.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404:
            return Response({"detail": "Issue not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error deleting issue: {e}")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, id):
        try:
            issue = Issue.objects.get(pk=id)
            serializer = IssueSerializer(issue, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()

                user_id = request.data.get('add_assigned')
                if user_id is not None:
                    if not UserProfile.objects.filter(user_id=user_id).exists():
                        return Response({"detail": f"L'usuari amb ID {user_id} no existeix."}, status=status.HTTP_400_BAD_REQUEST)
                    Assigned.objects.get_or_create(issue=issue, assigned_id=user_id)

                user_id = request.data.get('remove_assigned')
                if user_id is not None:
                    Assigned.objects.filter(issue=issue, assigned_id=user_id).delete()

                user_id = request.data.get('add_watchers')
                if user_id is not None:
                    if not UserProfile.objects.filter(user_id=user_id).exists():
                        return Response({"detail": f"L'usuari amb ID {user_id} no existeix."}, status=status.HTTP_400_BAD_REQUEST)
                    Watch.objects.get_or_create(issue=issue, watcher_id=user_id)

                user_id = request.data.get('remove_watchers')
                if user_id is not None:
                    Watch.objects.filter(issue=issue, watcher_id=user_id).delete()

                comment = request.data.get('comment')
                if comment:
                    Comments.objects.create(issue=issue, user=request.user.socialaccount_set.first(), comment=comment)
                    
                serializer = IssueSerializer(issue)
                serializer.data['watchers'] = [watcher.id for watcher in Watch.objects.filter(issue=issue)]
                serializer.data['assigned'] = [assigned.id for assigned in Assigned.objects.filter(issue=issue)]
                serializer.data['attachments'] = [attachment.filename for attachment in Attachment.objects.filter(issue=issue)]
                serializer.data['comments'] = [comment.comment for comment in Comments.objects.filter(issue=issue)] 

                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Issue.DoesNotExist:
            return Response({"detail": "Issue not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class IssueAttachmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            issue = Issue.objects.get(pk=id)
            file = request.FILES.get('attachment')

            if not file:
                return Response({"detail": "No se ha enviado ningún archivo."}, status=400)

            description = request.data.get('attachment_description', '')
            Attachment.objects.create(
                issue=issue,
                file=file,
                filename=file.name,
                filesize=file.size,
                description=description,
                uploaded_by=request.user.socialaccount_set.first()
            )

            return Response({"detail": "Archivo subido correctamente."}, status=201)

        except Issue.DoesNotExist:
            return Response({"detail": "Issue no encontrado."}, status=404)
        except Exception as e:
            import traceback
            traceback.print_exc()  # imprime en consola
            return Response({"detail": str(e)}, status=500)

class IssueAttachmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id, attachment_id):
        try:
            issue = Issue.objects.get(pk=id)
            attachment = Attachment.objects.get(pk=attachment_id, issue=issue)
            attachment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Issue.DoesNotExist:
            return Response({"detail": "Issue not found."}, status=status.HTTP_404_NOT_FOUND)
        except Attachment.DoesNotExist:
            return Response({"detail": "Attachment not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error al eliminar el archivo adjunto: {e}")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PriorityListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        priorities = Priority.objects.all().order_by('position')
        serializer = PrioritySerializer(priorities, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = PrioritySerializer(data=request.data)
        if serializer.is_valid():
            max_position = Priority.objects.aggregate(Max('position'))['position__max'] or 0
            serializer.save(position=max_position + 1)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PriorityDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, name):
        return get_object_or_404(Priority, name=name)

    def put(self, request, name):
        try:
            instance = self.get_object(name)
            serializer = PrioritySerializer(instance, data=request.data, partial=False)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Http404:
            return Response({"detail": "Prioridad no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error al actualizar la prioridad: {e}")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def delete(self, request, name):
        new_priority_name = request.data.get('new_priority')
        if not new_priority_name:
            return Response({"detail": "Debe proporcionar 'new_priority' en el cuerpo de la solicitud."},
                            status=status.HTTP_400_BAD_REQUEST)
        if name == new_priority_name:
            return Response({"detail": "La nueva prioridad no puede ser la misma que la que se desea eliminar."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            priority = self.get_object(name)
            deleted_position = priority.position

            try:
                new_priority = Priority.objects.get(name=new_priority_name)
            except Priority.DoesNotExist:
                return Response({"detail": f"La nueva prioridad '{new_priority_name}' no existe."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Actualizar todos los issues que usaban esta prioridad
            issues_to_update = Issue.objects.filter(priority=priority)
            for issue in issues_to_update:
                issue.priority = new_priority
                issue.save()

            # Eliminar la prioridad
            priority.delete()

            # Reordenar las prioridades restantes
            priorities_to_update = Priority.objects.filter(position__gt=deleted_position)
            for p in priorities_to_update:
                p.position -= 1
                p.save()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Http404:
            return Response({"detail": "Prioridad no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error al eliminar la prioridad: {e}")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MovePriorityUpView(APIView):
    def post(self, request, name):
        # Obtener la prioridad que queremos mover
        priority = get_object_or_404(Priority, name=name)

        # Verificar si la prioridad no está en la primera posición
        if priority.position > 1:
            # Obtener la prioridad que está justo por encima de esta
            higher_priority = Priority.objects.filter(position__lt=priority.position).order_by('-position').first()

            if higher_priority:
                # Intercambiar las posiciones
                higher_priority.position, priority.position = priority.position, higher_priority.position
                higher_priority.save()
                priority.save()

                return Response(
                    {"message": "Prioridad movida hacia arriba con éxito"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"detail": "No se puede mover más arriba"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"detail": "La prioridad ya está en la parte superior"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
class MovePriorityDownView(APIView):
    def post(self, request, name):
        # Obtener la prioridad que queremos mover
        priority = get_object_or_404(Priority, name=name)

        # Verificar si la prioridad no está en la última posición
        highest_position = Priority.objects.all().aggregate(Max('position'))['position__max']

        if priority.position < highest_position:
            # Obtener la prioridad que está justo por debajo de esta
            lower_priority = Priority.objects.filter(position__gt=priority.position).order_by('position').first()

            if lower_priority:
                # Intercambiar las posiciones
                lower_priority.position, priority.position = priority.position, lower_priority.position
                lower_priority.save()
                priority.save()

                return Response(
                    {"message": "Prioridad movida hacia abajo con éxito"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"detail": "No se puede mover más abajo"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"detail": "La prioridad ya está en la parte inferior"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
class TypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        types = Type.objects.all().order_by('position')
        serializer = TypeSerializer(types, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = TypeSerializer(data=request.data)
        if serializer.is_valid():
            max_position = Type.objects.aggregate(Max('position'))['position__max'] or 0
            serializer.save(position=max_position + 1)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class TypeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, name):
        return get_object_or_404(Type, name=name)   

    def delete(self, request, name):
        new_type_name = request.data.get('new_type')
        if not new_type_name:
            return Response({"detail": "Debe proporcionar 'new_type' en el cuerpo de la solicitud."},
                            status=status.HTTP_400_BAD_REQUEST)
        if name == new_type_name:
            return Response({"detail": "La nueva tipo no puede ser la misma que la que se desea eliminar."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            type = self.get_object(name)
            deleted_position = type.position

            try:
                new_type = Type.objects.get(name=new_type_name)
            except Type.DoesNotExist:
                return Response({"detail": f"La nueva tipo '{new_type_name}' no existe."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Actualizar todos los issues que usaban este tipo
            issues_to_update = Issue.objects.filter(type=type)
            for issue in issues_to_update:
                issue.type = new_type
                issue.save()

            # Eliminar el tipo
            type.delete()

            # Reordenar los tipos restantes
            types_to_update = Type.objects.filter(position__gt=deleted_position)
            for t in types_to_update:
                t.position -= 1
                t.save()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Http404:
            return Response({"detail": "Tipo no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error al eliminar el tipo: {e}")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, name):
        try:
            instance = self.get_object(name)
            serializer = TypeSerializer(instance, data=request.data, partial=False)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Http404:
            return Response({"detail": "Tipo no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error al actualizar el tipo: {e}")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        
class MoveTypeUpView(APIView):
    def post(self, request, name):
        # Obtener el tipo que queremos mover
        type = get_object_or_404(Type, name=name)

        # Verificar si el tipo no está en la primera posición
        if type.position > 1:
            # Obtener el tipo que está justo por encima de este
            higher_type = Type.objects.filter(position__lt=type.position).order_by('-position').first()

            if higher_type:
                # Intercambiar las posiciones
                higher_type.position, type.position = type.position, higher_type.position
                higher_type.save()
                type.save()

                return Response(
                    {"message": "Tipo movido hacia arriba con éxito"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"detail": "No se puede mover más arriba"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"detail": "El tipo ya está en la parte superior"},
                status=status.HTTP_400_BAD_REQUEST
            )

class MoveTypeDownView(APIView):
    def post(self, request, name):
        # Obtener el tipo que queremos mover
        type = get_object_or_404(Type, name=name)

        # Verificar si el tipo no está en la última posición
        highest_position = Type.objects.all().aggregate(Max('position'))['position__max']

        if type.position < highest_position:
            # Obtener el tipo que está justo por debajo de este
            lower_type = Type.objects.filter(position__gt=type.position).order_by('position').first()

            if lower_type:
                # Intercambiar las posiciones
                lower_type.position, type.position = type.position, lower_type.position
                lower_type.save()
                type.save()

                return Response(
                    {"message": "Tipo movido hacia abajo con éxito"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"detail": "No se puede mover más abajo"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"detail": "El tipo ya está en la parte inferior"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
class StatusListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        statuses = Status.objects.all().order_by('position')
        serializer = StatusSerializer(statuses, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = StatusSerializer(data=request.data)
        if serializer.is_valid():
            max_position = Status.objects.aggregate(Max('position'))['position__max'] or 0
            serializer.save(position=max_position + 1)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class StatusDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, name):
        return get_object_or_404(Status, name=name)   

    def delete(self, request, name):
        new_status_name = request.data.get('new_status')
        if not new_status_name:
            return Response({"detail": "Debe proporcionar 'new_status' en el cuerpo de la solicitud."},
                            status=status.HTTP_400_BAD_REQUEST)
        if name == new_status_name:
            return Response({"detail": "La nueva estado no puede ser la misma que la que se desea eliminar."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            status_obj = self.get_object(name)
            deleted_position = status_obj.position

            try:
                new_status = Status.objects.get(name=new_status_name)
            except Status.DoesNotExist:
                return Response({"detail": f"La nueva estado '{new_status_name}' no existe."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Actualizar todos los issues que usaban esta estado
            issues_to_update = Issue.objects.filter(status=status_obj)
            for issue in issues_to_update:
                issue.status = new_status
                issue.save()

            # Eliminar la estado
            status_obj.delete()

            # Reordenar las estados restantes
            statuses_to_update = Status.objects.filter(position__gt=deleted_position)
            for s in statuses_to_update:
                s.position -= 1
                s.save()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Http404:
            return Response({"detail": "Estado no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error al eliminar el estado: {e}")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, name):
        try:
            instance = self.get_object(name)
            serializer = StatusSerializer(instance, data=request.data, partial=False)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Http404:
            return Response({"detail": "Estado no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error al actualizar el estado: {e}")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ToggleStatusClosedView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, name):
        try:
            status_obj = Status.objects.get(name=name)
        except Status.DoesNotExist:
            return Response({'detail': 'Status not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Alternar booleano directamente
        status_obj.isClosed = not status_obj.isClosed
        status_obj.save()

        return Response({'is_closed': status_obj.isClosed}, status=status.HTTP_200_OK)

class MoveStatusUpView(APIView):
    def post(self, request, name):
        # Obtener el estado que queremos mover
        status_obj = get_object_or_404(Status, name=name)

        # Verificar si el estado no está en la primera posición
        if status_obj.position > 1:
            # Obtener el estado que está justo por encima de este
            higher_state = Status.objects.filter(position__lt=status_obj.position).order_by('-position').first()

            if higher_state:
                # Intercambiar las posiciones
                higher_state.position, status_obj.position = status_obj.position, higher_state.position
                higher_state.save()
                status_obj.save()

                return Response(
                    {"message": "Estado movido hacia arriba con éxito"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"detail": "No se puede mover más arriba"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"detail": "El estado ya está en la parte superior"},
                status=status.HTTP_400_BAD_REQUEST
            )

class MoveStatusDownView(APIView):
    def post(self, request, name):
        # Obtener el estado que queremos mover
        status_obj = get_object_or_404(Status, name=name)

        # Verificar si el estado no está en la última posición
        highest_position = Status.objects.all().aggregate(Max('position'))['position__max']

        if status_obj.position < highest_position:
            # Obtener el estado que está justo por debajo de este
            lower_status = Status.objects.filter(position__gt=status_obj.position).order_by('position').first()

            if lower_status:
                # Intercambiar las posiciones
                lower_status.position, status_obj.position = status_obj.position, lower_status.position
                lower_status.save()
                status_obj.save()

                return Response(
                    {"message": "Estado movido hacia abajo con éxito"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"detail": "No se puede mover más abajo"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"detail": "El estado ya está en la parte inferior"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
class SeverityListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        severities = Severity.objects.all().order_by('position')
        serializer = SeveritySerializer(severities, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SeveritySerializer(data=request.data)
        if serializer.is_valid():
            max_position = Severity.objects.aggregate(Max('position'))['position__max'] or 0
            serializer.save(position=max_position + 1)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
    
class SeverityDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, name):
        return get_object_or_404(Severity, name=name)   

    def delete(self, request, name):
        new_severity_name = request.data.get('new_severity')
        if not new_severity_name:
            return Response({"detail": "Debe proporcionar 'new_severity' en el cuerpo de la solicitud."},
                            status=status.HTTP_400_BAD_REQUEST)
        if name == new_severity_name:
            return Response({"detail": "La nueva severidad no puede ser la misma que la que se desea eliminar."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            severity = self.get_object(name)
            deleted_position = severity.position

            try:
                new_severity = Severity.objects.get(name=new_severity_name)
            except Severity.DoesNotExist:
                return Response({"detail": f"La nueva severidad '{new_severity_name}' no existe."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Actualizar todos los issues que usaban esta severidad
            issues_to_update = Issue.objects.filter(status=severity)
            for issue in issues_to_update:
                issue.status = new_severity
                issue.save()

            # Eliminar la severidad
            severity.delete()

            # Reordenar las severidades restantes
            severities_to_update = Severity.objects.filter(position__gt=deleted_position)
            for s in severities_to_update:
                s.position -= 1
                s.save()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Http404:
            return Response({"detail": "Severidad no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error al eliminar la severidad: {e}")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, name):
        try:
            instance = self.get_object(name)
            serializer = SeveritySerializer(instance, data=request.data, partial=False)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Http404:
            return Response({"detail": "Severidad no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error al actualizar la severidad: {e}")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class MoveSeverityUpView(APIView):
    def post(self, request, name):
        severity = get_object_or_404(Severity, name=name)

        if severity.position > 1:
            higher_severity = Severity.objects.filter(position__lt=severity.position).order_by('-position').first()

            if higher_severity:
                higher_severity.position, severity.position = severity.position, higher_severity.position
                higher_severity.save()
                severity.save()

                return Response(
                    {"message": "Severity moved up successfully."},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"detail": "No higher severity to move."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"detail": "Severity is already at the top."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
class MoveSeverityDownView(APIView):
    def post(self, request, name):
        severity = get_object_or_404(Severity, name=name)

        highest_position = Severity.objects.all().aggregate(Max('position'))['position__max']

        if severity.position < highest_position:
            lower_severity = Severity.objects.filter(position__gt=severity.position).order_by('position').first()

            if lower_severity:
                lower_severity.position, severity.position = severity.position, lower_severity.position
                lower_severity.save()
                severity.save()

                return Response(
                    {"message": "Severity moved down successfully."},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"detail": "No lower severity to move."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"detail": "Severity is already at the bottom."},
                status=status.HTTP_400_BAD_REQUEST
            )

class AssignedIssuesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = SocialAccount.objects.get(pk=user_id)
        except SocialAccount.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        valid_sort_fields = {
        'status': 'issue__status__position', 
        'priority': 'issue__priority__position', 
        'type': 'issue__type__position', 
        'severity': 'issue__severity__position', 
        'modified': 'issue__modified_at'
        }

        # Obtenir els parámetres d'ordenació
        sort_by = request.GET.get('sortBy', 'created')
        sort_order = request.GET.get('sortOrder', 'desc')

        sort_field = valid_sort_fields.get(sort_by, 'issue__created_at')
        if sort_order == 'desc':
            sort_field = f'-{sort_field}'

        assigned_qs = Assigned.objects.filter(
            assigned_id=user,
            issue__status__isClosed=False
        ).select_related('issue').order_by(sort_field)

        issues = [a.issue for a in assigned_qs]
        serializer = IssueSerializer(issues, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class WatchedIssuesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = SocialAccount.objects.get(pk=user_id)
        except SocialAccount.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        valid_sort_fields = {
        'status': 'issue__status__position', 
        'priority': 'issue__priority__position', 
        'type': 'issue__type__position', 
        'severity': 'issue__severity__position', 
        'modified': 'issue__modified_at'
        }

        # Obtenir els parámetres d'ordenació
        sort_by = request.GET.get('sortBy', 'created')
        sort_order = request.GET.get('sortOrder', 'desc')

        sort_field = valid_sort_fields.get(sort_by, 'issue__created_at')
        if sort_order == 'desc':
            sort_field = f'-{sort_field}'

        assigned_qs = Watch.objects.filter(
            watcher_id=user,
        ).select_related('issue').order_by(sort_field)

        issues = [a.issue for a in assigned_qs]
        serializer = IssueSerializer(issues, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class UserProfileListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_profiles = UserProfile.objects.all()
        serializer = UserProfileSerializer(user_profiles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = UserProfile.objects.get(pk=user_id)
        except UserProfile.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileDetailSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def post(self, request, user_id):
        # Verificar si el perfil a modificar pertenece al usuario actual
 
        if request.user.id != user_id:
            return Response({"detail": "No tiene permisos para modificar este perfil."}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = UserProfile.objects.get(pk=user_id)
        except UserProfile.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if 'avatar' in request.FILES:
            try:
                if user.avatar:
                    user.delete_avatar()
                user.avatar = request.FILES['avatar']
                user.save()
                return Response({"message": "Avatar uploaded successfully!"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if 'bio' in request.data:
            serializer = UserBioSerializer(user, data=request.data)
            if serializer.is_valid():
                user.bio = serializer.validated_data['bio']
                user.save()
                return Response({"message": "Bio updated successfully!"}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "No valid data provided."}, status=status.HTTP_400_BAD_REQUEST)

class UserCommentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = SocialAccount.objects.get(pk=user_id)
        except SocialAccount.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        comments_qs = Comments.objects.filter(user_id=user).select_related('issue')
        issues = set(comment.issue for comment in comments_qs)

        serializer = IssueWithCommentsSerializer(issues, many=True, context={'user': user})
        return Response(serializer.data, status=status.HTTP_200_OK)
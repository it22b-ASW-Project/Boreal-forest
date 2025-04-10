from django.http import HttpResponse
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

from django.contrib import messages

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
            return redirect("/issues")  # Cambia a tu vista/listado real
    else:
        form = BulkIssueForm()

    return render(request, "showAllIssues.html", {'issues': issues.qs, 'filter': issues, 'bulkForm': bulkForm, 'show_filters': show_filters})
    
def crearIssues(request, form):
    lines = form.cleaned_data["bulk_text"].splitlines()
    issues = [Issue(subject=line.strip(), status=Status.objects.order_by('name').first(), type=Type.objects.order_by('name').first(),
                    severity=Severity.objects.order_by('name').first(), priority=Priority.objects.order_by('name').first(), 
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
            created_by= SocialAccount.objects.filter(user=request.user, provider="google").first()  # Asignar el usuario que crea el issue
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

        return redirect('/issues')  # Redirige a la página principal

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
            return redirect(reverse("issueDetail", args=[issue.id])) # Redirige a la misma página
        
        elif 'description' in request.POST:
            issue.description = request.POST.get("description", issue.description)
            issue.save()
            return redirect(reverse("issueDetail", args=[issue.id]))

        elif 'deadline' in request.POST:
            deadline = request.POST.get("deadline", "")
            # Si se deja en blanco, establecemos a None
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
def user_settings(request):
    user = request.user
    context = {
        'username': user.username,
        'email': user.email,
        'full_name': f"{user.first_name} {user.last_name}",
        'language': 'English (US)',
        'theme': 'dark',
        'bio': 'Computer Engineering student',
    }
    return render(request, 'user_settings.html', context)

@login_required
def user_profile(request, id):
    user = SocialAccount.objects.get(id=id)
    profile, created = UserProfile.objects.get_or_create(user_id=id)
    active_tab = request.GET.get('tab', 'assigned-issues')  # Tab activo por defecto
    sort_by = request.GET.get('sort_by', '-modified_at')  # Por defecto, ordenar por 'modified'
    edit_bio = request.GET.get('edit_bio', 'false') == 'true' 

    valid_sort_fields = ['type__position', 'severity__position', 'priority__position', 'status__position', 'modified_at']
    if sort_by.lstrip('-') not in valid_sort_fields:
        sort_by = '-modified_at'

    order_by_field = f'issue__{sort_by.lstrip("-")}'
    if sort_by.startswith('-'):
        order_by_field = f'-{order_by_field}'
    
    if request.method == 'POST':
        form = EditBioForm(request.POST, instance=profile)
        if form.is_valid():
            profile.bio = form.cleaned_data['bio']
            form.save()
            return redirect('user_profile', id=id)  # Redirige a la misma página después de guardar
    else:
        form = EditBioForm(instance=profile)

    assigned_issues = Assigned.objects.filter(assigned=user, issue__status__name__in=['New', 'In progress', 'Ready for test', 'Needs info', 'Rejected', 'Postponed']).select_related('issue').order_by(order_by_field)
    watched_issues = Watch.objects.filter(watcher=user).select_related('issue').order_by(order_by_field)
    comments = Comments.objects.filter(user=user).select_related('issue').order_by(f'-created_at')

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
        'form': form,
        'active_tab': active_tab,
        'edit_bio': edit_bio,
    }
    return render(request, 'user_profile.html', context)


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
            return redirect('priorities')  # Redirecciona de vuelta a la misma página

        elif action == 'add_new':
            max_position = priorities.aggregate(Max('position'))['position__max'] or 0
            new_name = f"New Priority {max_position + 1}"

            if not Priority.objects.filter(name=new_name).exists():
                Priority.objects.create(
                    name="Write a name for the new element",
                    color="#808080", #gris por defecto
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

        return redirect("priorities")  # Redirigir después de la acción

    return render(request, 'priorities.html', {'priorities': priorities})


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
            return redirect('statuses')  # Redirecciona de vuelta a la misma página

        elif action == 'add_new':
            max_position = statuses.aggregate(Max('position'))['position__max'] or 0
            new_name = f"New Status {max_position + 1}"

            if not Status.objects.filter(name=new_name).exists():
                Status.objects.create(
                    name="Write a name for the new element",
                    color="#808080", #gris por defecto
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

        return redirect("statuses")  # Redirigir después de la acción

    return render(request, 'statuses.html', {'statuses': statuses})

def severities_settings(request):
    severities = Severity.objects.all().order_by('position')
    if request.method == "POST":
        action = request.POST.get('action')
        print(f"Action: {action}")
        if action not in( 'add_new', 'edit_name', 'start_editting', 'new_color'):
            severity_name = request.POST.get('severity_name')
            severity = Status.objects.get(name=severity_name)

        if action == 'delete_severity':
            severity.delete()

            if "write a name for the new element" not in severity_name.lower():
                messages.success(request, f'Status "{severity_name}" succesfully deleted')
            return redirect('severities')  # Redirecciona de vuelta a la misma página

        elif action == 'add_new':
            max_position = severities.aggregate(Max('position'))['position__max'] or 0
            new_name = f"New Status {max_position + 1}"

            if not Severity.objects.filter(name=new_name).exists():
                Severity.objects.create(
                    name="Write a name for the new element",
                    color="#808080", #gris por defecto
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
        
            severity = Status.objects.get(name=original_name)
            severity.color = new_color
            severity.save()
            return redirect('severities')

        elif action == 'start_editting':

            severityName = request.POST.get('severity_name')

            # Este contexto extra indica a la plantilla que estamos editando ese nombre
            severity = Status.objects.get(name=severityName)
            return render(request, 'severities.html', {
            'severities': Status.objects.all().order_by('position'),
            'editing_name': severity.name,
            'messages': messages.get_messages(request),
            })

        elif "moveUp" in request.POST:

            if severity.position > 1:  
                previous_severity = Status.objects.get(position=severity.position - 1)
                severity.position -= 1
                previous_severity.position += 1
                severity.save()
                previous_severity.save()
            print("Moved up")

        elif "move_down" in request.POST:

            if severity.position < len(severities):
                    next_severity = Status.objects.get(position=severity.position + 1)
                    # Intercambiar las posiciones
                    severity.position += 1
                    next_severity.position -= 1
                    severity.save()
                    next_severity.save()
            print("Moved down")

        return redirect("severities")  # Redirigir después de la acción

    return render(request, 'severities.html', {'severities': severities})

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
            return redirect('types')  # Redirecciona de vuelta a la misma página

        elif action == 'add_new':
            max_position = types.aggregate(Max('position'))['position__max'] or 0
            new_name = f"New Type {max_position + 1}"

            if not Type.objects.filter(name=new_name).exists():
                Type.objects.create(
                    name="Write a name for the new element",
                    color="#808080", #gris por defecto
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

        return redirect("types")  # Redirigir después de la acción

    return render(request, 'types.html', {'types': types})

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

        # Eliminar la prioridad
        priority_to_delete.delete()

        messages.success(request, f'Priority "{priority_name}" deleted and issues changed to  "{new_priority.name}".')
        return redirect('priorities')

    return render(request, 'confirm_delete_priority.html', {
        'priority': priority_to_delete,
        'other_priorities': other_priorities,
    })

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

def confirm_delete_type(request):
    type_name = request.GET.get('type_name')
    type_to_delete = get_object_or_404(Type, name=type_name)
    other_types = Type.objects.exclude(name=type_name).order_by('position')
   
   
    if request.method == 'POST':
        new_type_id = request.POST.get('new_type_id')
        new_type = get_object_or_404(Type, name=new_type_id)

        # Cambiar issues a la nueva prioridad
        issues = Issue.objects.filter(type=type_to_delete)
        issues.update(type=new_type)

        # Eliminar la prioridad
        type_to_delete.delete()

        messages.success(request, f'Type "{type_name}" deleted and issues changed to  "{new_type.name}".')
        return redirect('types')

    return render(request, 'confirm_delete_type.html', {
        'type': type_to_delete,
        'other_types': other_types,
    })
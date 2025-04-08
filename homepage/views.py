from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from allauth.socialaccount.models import SocialAccount

from .models import Issue, Type, Severity, Status, Priority, Watch, Assigned, Comments, Attachment, UserProfile
from .forms import EditParamsForm, CommentForm, BulkIssueForm, EditBioForm

from .filters import IssueFilter

from django.utils import timezone

def showAllIssues(request):
    bulkForm = BulkIssueForm()
    issues = IssueFilter(request.GET, queryset=Issue.objects.all().order_by('-id'))

    if request.method == "POST":
        form = BulkIssueForm(request.POST)
        if form.is_valid():
            crearIssues(request, form)
            return redirect("/")  # Cambia a tu vista/listado real
    else:
        form = BulkIssueForm()

    return render(request, "showAllIssues.html", {'issues': issues.qs, 'filter': issues, 'bulkForm': bulkForm})
    
def crearIssues(request, form):
    lines = form.cleaned_data["bulk_text"].splitlines()
    issues = [Issue(subject=line.strip(), status=Status.objects.order_by('id').first(), type=Type.objects.order_by('id').first(),
                    severity=Severity.objects.order_by('id').first(), priority=Priority.objects.order_by('id').first(), 
                    created_by=SocialAccount.objects.filter(user=request.user, provider="google").first()) for line in lines if line.strip()]
    Issue.objects.bulk_create(issues)


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
        if 'close' in request.POST: 
            form = EditParamsForm(request.POST)
            if form.is_valid():
                # Guardar los cambios en la base de datos
                issue.priority = form.cleaned_data['priority']
                issue.type = form.cleaned_data['type']
                issue.severity = form.cleaned_data['severity']
                issue.status = form.cleaned_data['status']
                # No guardamos deadline aquí, se maneja por separado
                issue.save()
            return redirect('/issues')
        
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

def settings(request):
    return render(request, 'settings.html')

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

def user_profile(request, id):
    user = SocialAccount.objects.get(id=id)
    profile, created = UserProfile.objects.get_or_create(user_id=id)
    active_tab = request.GET.get('tab', 'assigned-issues')  # Tab activo por defecto
    sort_by = request.GET.get('sort_by', '-modified')  # Por defecto, ordenar por 'modified'
    edit_bio = request.GET.get('edit_bio', 'false') == 'true' 

    valid_sort_fields = ['type__name', 'severity__name', 'priority__name', 'status', 'modified_at']
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

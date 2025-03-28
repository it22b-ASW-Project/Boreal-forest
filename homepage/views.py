from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse

from .models import Issue
from .models import Priority
from .forms import EditParamsForm

from django_filters.views import FilterView
from .filters import IssueFilter


def showAllIssues(request):
    issues = IssueFilter(request.GET, queryset=Issue.objects.all().order_by('-id'))
    return render(request, "showAllIssues.html", {'issues': issues.qs, 'filter': issues})
    
def createIssue(request):
    if request.method == 'POST':
        # Procesa los datos del formulario aquí
        subject = request.POST.get('Subject')
        description = request.POST.get('description')
        # Guarda el nuevo issue en la base de datos
        new_issue = Issue(subject=subject, description=description)
        new_issue.save()
        # ...
        return redirect('/')  # Redirige a la página principal después de crear el issue
    return render(request, 'createIssue.html')

def issueDetail(request, id):
    issue = Issue.objects.get(id=id)
    paramform = EditParamsForm(initial={
        "priority": issue.priority.name,
        "type": issue.type.name,
        "severity": issue.severity.name,
        "status": issue.status.name
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
                issue.save()
            return redirect('/')
        
        else:     
            issue.subject = request.POST.get("subject", issue.subject)
            issue.save()
            return redirect(reverse("issueDetail", args=[issue.id])) # Redirige a la misma página


    return render(request, "issueDetail.html", {"issue": issue, "paramform": paramform})

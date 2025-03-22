from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import redirect

from .models import Issue

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

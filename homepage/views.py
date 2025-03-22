from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse

from .models import Issue

def showAllIssues(request):
    issues = Issue.objects.all().order_by('-id')
    return render(request, "showAllIssues.html", {'issues': issues})

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

    if request.method == "POST":
        issue.subject = request.POST.get("subject", issue.subject)
        issue.save()
        return redirect(reverse("issueDetail", args=[issue.id])) # Redirige a la misma página

    return render(request, "issueDetail.html", {"issue": issue})



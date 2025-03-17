from django.http import HttpResponse
from django.shortcuts import render

from .models import Issue

def showAllIssues(request):
    issues = Issue.objects.all()
    return render(request, "showAllIssues.html", {'issues': issues})
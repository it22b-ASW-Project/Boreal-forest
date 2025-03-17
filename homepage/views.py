from django.http import HttpResponse
from django.shortcuts import render

from .models import Issue

def showAllIssues(request):
    issues = Issue.objects.all().order_by('-id')
    return render(request, "showAllIssues.html", {'issues': issues})
from django.contrib import admin
from django.urls import include,path

from . import views

urlpatterns = [
    path('', views.showAllIssues),
    path('new/', views.createIssue),
    path('issue/<int:id>/', views.issueDetail, name='issueDetail')
]
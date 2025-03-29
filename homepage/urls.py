from django.contrib import admin
from django.urls import include,path

from . import views

urlpatterns = [
    path('issues/', views.showAllIssues),
    path('', views.login), 
    path('issues/new/', views.createIssue),
    path('issue/<int:id>/', views.issueDetail, name='issueDetail')
]
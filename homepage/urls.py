from django.contrib import admin
from django.urls import include,path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('settings/', views.settings, name='settings'),  # Ruta para 'settings'
    path('settings/user-settings/', views.user_settings, name='user_settings'),
    path('user-profile/<int:id>/', views.user_profile, name='user_profile'),
    path('issues/', views.showAllIssues),
    path('', views.login), 
    path('issues/new/', views.createIssue),
    path('issue/<int:id>/', views.issueDetail, name='issueDetail')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

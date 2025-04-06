from django.contrib import admin
from django.urls import include,path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('settings/', views.settings, name='settings'),  # Ruta para 'settings'
    path('settings/user-settings/', views.user_settings, name='user_settings'),
    path('settings/change-password/', views.change_password, name='change_password'),
    path('settings/email-notifications/', views.email_notifications, name='email_notifications'),
    path('settings/desktop-notifications/', views.desktop_notifications, name='desktop_notifications'),
    path('settings/events/', views.events, name='events'),
    path('issues/', views.showAllIssues),
    path('', views.login), 
    path('issues/new/', views.createIssue),
    path('issue/<int:id>/', views.issueDetail, name='issueDetail')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

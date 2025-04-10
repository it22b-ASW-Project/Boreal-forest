from django.contrib import admin
from django.urls import include,path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    
    path('settings/', RedirectView.as_view(pattern_name='statuses', permanent=False)),
    
    path('settings/priorities/delete/', views.confirm_delete_priority, name='confirm_delete_priority'),
    path('settings/statuses/delete/', views.confirm_delete_status, name='confirm_delete_status'),
    path('settings/severities/delete/', views.confirm_delete_severity, name='confirm_delete_severity'),
    path('settings/types/delete/', views.confirm_delete_type, name='confirm_delete_type'),
    
    path('settings/priorities/', views.priorities_settings, name='priorities'),
    path('settings/statuses/', views.statuses_settings, name='statuses'),
    path('settings/severities/', views.severities_settings, name='severities'),
    path('settings/types/', views.types_settings, name='types'),
    
    path('user-profile/<int:id>/', views.user_profile, name='user_profile'),
    path('issues/', views.showAllIssues),
    path('', views.login), 
    path('issues/new/', views.createIssue),
    path('issue/<int:id>/', views.issueDetail, name='issueDetail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

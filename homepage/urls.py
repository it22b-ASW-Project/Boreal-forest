from django.contrib import admin
from django.urls import include,path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from . import views
from .views import IssueDetailView

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Issue Tracker API",
        default_version='v1',
        description="API REST para gestionar issues",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="soporte@miapp.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

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
    
    path('user-profiles/', views.user_profiles, name='user_profiles'),
    path('user-profile/<int:id>/', views.user_profile, name='user_profile'),
    path('issues/', views.showAllIssues),
    path('', views.login), 
    path('issues/new/', views.createIssue),
    path('issue/<int:id>/', views.issueDetail, name='issueDetail'),

    #api urls
    path('api/issues/', views.IssueListView.as_view(), name='issue-list'),
    path('api/issues/<int:id>/', IssueDetailView.as_view(), name='issue-detail'),

    path('api/priorities/', views.PriorityListView.as_view(), name='priority-list'),
    path('api/priorities/<str:name>/', views.PriorityDetailView.as_view(), name='priority-detail'),
    path('api/priorities/<str:name>/move-up/', views.MovePriorityUpView.as_view(), name='move-priority-up'),
    path('api/priorities/<str:name>/move-down/', views.MovePriorityDownView.as_view(), name='move-priority-down'),

    path('api/types/', views.TypeListView.as_view(), name='type-list'),
    path('api/types/<str:name>/', views.TypeDetailView.as_view(), name='type-detail'),
    path('api/types/<str:name>/move-up/', views.MoveTypeUpView.as_view(), name='move-type-up'),
    path('api/types/<str:name>/move-down/', views.MoveTypeDownView.as_view(), name='move-type-down'),

    path('api/statuses/', views.StatusListView.as_view(), name='status-list'),
    path('api/statuses/<str:name>/', views.StatusDetailView.as_view(), name='status-detail'),
    path('api/statuses/<str:name>/move-up/', views.MoveStatusUpView.as_view(), name='move-status-up'),
    path('api/statuses/<str:name>/move-down/', views.MoveStatusDownView.as_view(), name='move-status-down'),
    path('api/statuses/<str:name>/change-closed/', views.ToggleStatusClosedView.as_view(), name='toggle-status-closed'),

    path('api/severities/', views.SeverityListView.as_view(), name='severity-list'),
    path('api/severities/<str:name>/', views.SeverityDetailView.as_view(), name='severity-detail'),
    path('api/severities/<str:name>/move-up/', views.MoveSeverityUpView.as_view(), name='move-severity-up'),
    path('api/severities/<str:name>/move-down/', views.MoveSeverityDownView.as_view(), name='move-severity-down'),

    path('api/users/<int:user_id>/assigned/', views.AssignedIssuesView.as_view(), name='assigned-issues'),
    path('api/users/<int:user_id>/watching/', views.WatchedIssuesView.as_view(), name='watched-issues'),
    path('api/users/<int:user_id>/comments/', views.UserCommentsView.as_view(), name='user-comments'),

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

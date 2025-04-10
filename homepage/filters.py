from django.db.models import Q
import django_filters
from django import forms
from .models import Issue

from allauth.socialaccount.models import SocialAccount

from .models import Priority, Type, Severity, Status, Assigned

class IssueFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='filter_search', 
        label="Buscar", 
        widget=forms.TextInput(attrs={
            "placeholder": "Subject or description", 
            "onchange": "this.form.submit();",
            })
    )

    created_by = django_filters.ChoiceFilter(
        choices=lambda: [
            (account.user_id, f"{account.extra_data.get('name', 'Unknown')}")
            for account in SocialAccount.objects.filter(user_id__in=Issue.objects.values_list('created_by', flat=True).distinct())
        ],
        empty_label="All",
        widget=forms.Select(attrs={"onchange": "this.form.submit();"})
    )
    
    assigned = django_filters.ChoiceFilter(
        method='filter_assigned',
        choices=[],
        empty_label="All",
        widget=forms.Select(attrs={"onchange": "this.form.submit();"})
    )

    priority = django_filters.ModelChoiceFilter(
        queryset=Priority.objects.all(),  
        empty_label="All",
        widget=forms.Select(attrs={"onchange": "this.form.submit();"})
    )
    type = django_filters.ModelChoiceFilter(
        queryset=Type.objects.all(), 
        empty_label="All",
        widget=forms.Select(attrs={"onchange": "this.form.submit();"})
    )
    severity = django_filters.ModelChoiceFilter(
        queryset=Severity.objects.all(), 
        empty_label="All",
        widget=forms.Select(attrs={"onchange": "this.form.submit();"})
    )
    status = django_filters.ModelChoiceFilter(
        queryset=Status.objects.all(), 
        empty_label="All",
        widget=forms.Select(attrs={"onchange": "this.form.submit();"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.filters['assigned'].extra['choices'] = [('0', 'Unassigned')] + [
            (account.user_id, f"{account.extra_data.get('name', 'Unknown')}")
            #for account in SocialAccount.objects.filter(user_id__in=Assigned.objects.values_list('assigned', flat=True).distinct())
            for account in SocialAccount.objects.all().order_by('extra_data__name')
        
        ]

    def filter_assigned(self, queryset, name, value):
        if value == '0':
            return queryset.exclude(
                id__in=Assigned.objects.values('issue')  
            )
        if value:
            return queryset.filter(
                assigned__assigned__user_id=value 
            )
        return queryset

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(subject__icontains=value) | Q(description__icontains=value))

    class Meta:
        model = Issue
        fields = ['created_by', 'assigned','priority', 'type', 'severity', 'status']
    
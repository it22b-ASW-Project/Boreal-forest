from django.db.models import Q
import django_filters
from django import forms
from .models import Issue

from .models import Priority, Type, Severity, Status

class IssueFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='filter_search', 
        label="Buscar", 
        widget=forms.TextInput(attrs={
            "placeholder": "Subject or description", 
            "onchange": "this.form.submit();"
            })
    )
    
    priority = django_filters.ModelChoiceFilter(
        queryset=Priority.objects.all(), 
        label="Prioridad", 
        empty_label="Todas",
        widget=forms.Select(attrs={"onchange": "this.form.submit();"})
    )
    type = django_filters.ModelChoiceFilter(
        queryset=Type.objects.all(), 
        label="Tipo", 
        empty_label="Todos",
        widget=forms.Select(attrs={"onchange": "this.form.submit();"})
    )
    severity = django_filters.ModelChoiceFilter(
        queryset=Severity.objects.all(), 
        label="Severidad", 
        empty_label="Todas",
        widget=forms.Select(attrs={"onchange": "this.form.submit();"})
    )
    status = django_filters.ModelChoiceFilter(
        queryset=Status.objects.all(), 
        label="Estado", 
        empty_label="Todos",
        widget=forms.Select(attrs={"onchange": "this.form.submit();"})
    )


    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(subject__icontains=value) | Q(description__icontains=value))

    class Meta:
        model = Issue
        fields = ['priority', 'type', 'severity', 'status']
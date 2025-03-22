from django.db.models import Q
import django_filters
from .models import Issue

class IssueFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filter_search', label="Buscar")

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(subject__icontains=value) | Q(description__icontains=value))

    class Meta:
        model = Issue
        fields = []
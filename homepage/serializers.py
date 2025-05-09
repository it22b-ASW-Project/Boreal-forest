from rest_framework import serializers
from .models import Issue, Priority, Status, Severity, Type, UserProfile
from django.db.models import Max

class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = '__all__'

class PrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = ['name', 'color']
        read_only_fields = ['position']

        def validate_name(self, value):
            if not value.strip():
                raise serializers.ValidationError("El nombre no puede estar vacío.")
            return value    
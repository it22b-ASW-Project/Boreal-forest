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

    def update(self, instance, validated_data):
        new_name = validated_data.get('name', instance.name)
        if new_name != instance.name:
            # Borrar el viejo e insertar uno nuevo
            instance.delete()
            instance.name = new_name

        instance.color = validated_data.get('color', instance.color)
        instance.save()
        return instance    

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return value
    
class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = ['name', 'color']
        read_only_fields = ['position']

    def update(self, instance, validated_data):
        new_name = validated_data.get('name', instance.name)
        if new_name != instance.name:
            # Borrar el viejo e insertar uno nuevo
            instance.delete()
            instance.name = new_name

        instance.color = validated_data.get('color', instance.color)
        instance.save()
        return instance    

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return value
    
class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ['name', 'color']
        read_only_fields = ['position']

    def update(self, instance, validated_data):
        new_name = validated_data.get('name', instance.name)
        if new_name != instance.name:
            # Borrar el viejo e insertar uno nuevo
            instance.delete()
            instance.name = new_name

        instance.color = validated_data.get('color', instance.color)
        instance.save()
        return instance    

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return value

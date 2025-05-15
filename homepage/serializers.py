from rest_framework import serializers
from .models import Issue, Priority, Status, Severity, Type, UserProfile, Comments, Attachment, Watch, Assigned
from django.db.models import Max
from allauth.socialaccount.models import SocialAccount
import re

class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = '__all__'

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'


class IssueInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = ['subject', 'description', 'status', 'type', 'severity', 'priority', 'created_by']

class BulkTitlesSerializer(serializers.Serializer):
    titles = serializers.ListField(
        child=serializers.CharField(max_length=255),
        allow_empty=False
    )        

class PrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = ['name', 'color', 'position']
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
    
    def validate_color(self, value):
        if not re.match(r'^#[0-9a-fA-F]{6}$', value):
            raise serializers.ValidationError("El color debe estar en formato hexadecimal (#RRGGBB).")
        return value
    
class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = ['name', 'color', 'position']
        read_only_fields = ['position']

    def update(self, instance, validated_data):
        new_name = validated_data.get('name', instance.name)
        if new_name != instance.name:
            instance.delete()
            instance.name = new_name

        instance.color = validated_data.get('color', instance.color)
        instance.save()
        return instance    

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return value
    
    def validate_color(self, value):
        if not re.match(r'^#[0-9a-fA-F]{6}$', value):
            raise serializers.ValidationError("El color debe estar en formato hexadecimal (#RRGGBB).")
        return value
    
class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ['name', 'color', 'isClosed', 'position']
        read_only_fields = ['position']

    def update(self, instance, validated_data):
        new_name = validated_data.get('name', instance.name)
        if new_name != instance.name:
            instance.delete()
            instance.name = new_name

        instance.color = validated_data.get('color', instance.color)
        instance.save()
        return instance    

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return value
    
    def validate_color(self, value):
        if not re.match(r'^#[0-9a-fA-F]{6}$', value):
            raise serializers.ValidationError("El color debe estar en formato hexadecimal (#RRGGBB).")
        return value
    
class SeveritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Severity
        fields = ['name', 'color', 'position']
        read_only_fields = ['position']

    def update(self, instance, validated_data):
        new_name = validated_data.get('name', instance.name)
        if new_name != instance.name:
            instance.delete()
            instance.name = new_name

        instance.color = validated_data.get('color', instance.color)
        instance.save()
        return instance    

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return value    
    
    def validate_color(self, value):
        if not re.match(r'^#[0-9a-fA-F]{6}$', value):
            raise serializers.ValidationError("El color debe estar en formato hexadecimal (#RRGGBB).")
        return value
   
class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['full_name', 'avatar']
        read_only_fields = ['full_name']

    def get_full_name(self, obj):
        try:
            user = obj.user
            return f'{user.first_name} {user.last_name}'.strip()
        except AttributeError:
            return 'Unknown User'

    def validate_bio(self, value):
        if len(value) > 500:
            raise serializers.ValidationError("La biografía no puede exceder los 500 caracteres.")
        return value


class UserProfileDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    open_assigned_issues = serializers.SerializerMethodField()
    watched_issues = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'user', 'full_name', 'username', 'bio', 'avatar',
            'open_assigned_issues', 'watched_issues', 'comments_count'
        ]

    def get_social_account(self, user):
        try:
            return SocialAccount.objects.get(user=user)
        except SocialAccount.DoesNotExist:
            return None

    def get_full_name(self, obj):
        user = obj.user
        return f"{user.first_name} {user.last_name}".strip()

    def get_username(self, obj):
        return obj.user.username

    def get_open_assigned_issues(self, obj):
        social_account = self.get_social_account(obj.user)
        if social_account:
            return Assigned.objects.filter(assigned_id=social_account, issue__status__isClosed=False).count()
        return 0

    def get_watched_issues(self, obj):
        social_account = self.get_social_account(obj.user)
        if social_account:
            return Watch.objects.filter(watcher_id=social_account).count()
        return 0

    def get_comments_count(self, obj):
        social_account = self.get_social_account(obj.user)
        if social_account:
            return Comments.objects.filter(user=social_account).count()
        return 0

    def validate_bio(self, value):
        if len(value) > 280:
            raise serializers.ValidationError("La biografía no puede exceder los 280 caracteres.")
        return value

class UserProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['avatar']

class UserBioSerializer(serializers.ModelSerializer):
    bio = serializers.CharField(max_length=280)

    class Meta:
        model = UserProfile
        fields = ['bio']

class CommentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comments
        fields = ['comment', 'created_at']

class IssueWithCommentsSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Issue
        fields = ['id', 'subject', 'comments']

    def get_comments(self, obj):
        user = self.context.get('user')
        comments = obj.comments_set.filter(user=user)
        return CommentDetailSerializer(comments, many=True).data


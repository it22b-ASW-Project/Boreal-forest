from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class Priority(models.Model):
    name = models.CharField(max_length=20, primary_key=True) 
    color = models.CharField(max_length=7, default="#808080") 
    position = models.IntegerField(default = 0)

    def __str__(self):
        return self.name

class Type(models.Model):
    name = models.CharField(max_length=20, primary_key=True)  
    color = models.CharField(max_length=7, default="#808080") 
    position = models.IntegerField(default = 0)

    def __str__(self):
        return self.name

class Severity(models.Model):
    name = models.CharField(max_length=20, primary_key=True) 
    color = models.CharField(max_length=7, default="#808080")
    position = models.IntegerField(default = 0)

    def __str__(self):
        return self.name

class Status(models.Model):
    name = models.CharField(max_length=20, primary_key=True)  
    color = models.CharField(max_length=7, default="#808080")
    position = models.IntegerField(default = 0)

    def __str__(self):
        return self.name

class Issue(models.Model):
    subject = models.CharField(max_length=30)
    description = models.CharField(max_length=280)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.ForeignKey(Type, on_delete=models.SET_NULL, null=True, blank=True)
    severity =models.ForeignKey(Severity, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.ForeignKey(Priority, on_delete=models.SET_NULL, null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey('socialaccount.socialaccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='creator')
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def get_priority_color(self):
            return self.priority.color if self.priority else "#808080"  
    
    def get_status_color(self):
            return self.status.color if self.status else "#808080"  
    
    def get_type_color(self):
            return self.type.color if self.type else "#808080" 
    
    def get_severity_color(self):
            return self.severity.color if self.severity else "#808080"  
    def save(self, *args, **kwargs):
        if not self.pk:
             self.modified_at = created_at = now()
        else:
            self.modified_at = now()
        super().save(*args, **kwargs)

class Watch(models.Model):
    watcher = models.ForeignKey('socialaccount.socialaccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='watcher')
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE)

class Assigned(models.Model):
    assigned = models.ForeignKey('socialaccount.socialaccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned')
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE)

def get_upload_path(instance, filename):
    return f'issues/{instance.issue.id}/{filename}'

class Attachment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=get_upload_path)
    filename = models.CharField(max_length=255)
    filesize = models.IntegerField(default=0)
    description = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey('socialaccount.socialaccount', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.filename
    
    def formatted_filesize(self):
        if self.filesize < 1024:
            return f"{self.filesize} bytes"
        elif self.filesize < 1024 * 1024:
            return f"{self.filesize / 1024:.1f} KB"
        else:
            return f"{self.filesize / (1024 * 1024):.1f} MB"

    def get_file_url(self):
        if not self.file:
            return None

        try:
            return self.file.url
        except Exception:
            from django.conf import settings
            from homepage.s3utils import PublicMediaStorage

            try:
                storage = PublicMediaStorage()
                file_path = f"issues/{self.issue.id}/{self.filename}"

                if storage.exists(file_path):
                    return storage.url(file_path)

                media_path = f"media/{file_path}"
                if storage.exists(media_path):
                    return storage.url(media_path)
            except Exception:
                pass

            try:
                import boto3

                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    aws_session_token=getattr(settings, 'AWS_SESSION_TOKEN', None),
                    region_name=settings.AWS_S3_REGION_NAME
                )

                file_key = f"media/issues/{self.issue.id}/{self.filename}"

                return s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                        'Key': file_key
                    },
                    ExpiresIn=3600
                )
            except Exception:
                pass

            return f"/media/issues/{self.issue.id}/{self.filename}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        from django.conf import settings
        if getattr(settings, 'USE_S3', False) and self.file:
            from homepage.s3utils import PublicMediaStorage
            import os

            s3_storage = PublicMediaStorage()
            local_path = self.file.path
            s3_key = f"issues/{self.issue.id}/{self.filename}"

            if os.path.exists(local_path):
                with open(local_path, 'rb') as f:
                    s3_storage.save(s3_key, f)
    
class Comments(models.Model):
    comment = models.CharField(max_length=280)
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE)
    user = models.ForeignKey(
        'socialaccount.socialaccount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comment_owner'
    )
    created_at = models.DateTimeField(auto_now_add=True)

def get_avatar_upload_path(instance, filename):
    return f'avatars/{instance.user.id}/{filename}'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(null=True, blank=True)
    avatar = models.ImageField(upload_to=get_avatar_upload_path, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    avatar = models.ImageField(upload_to=get_avatar_upload_path, null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
    
    def delete_avatar(self):
        if self.avatar and self.avatar.storage.exists(self.avatar.name):
            self.avatar.delete()
            self.avatar = None
            self.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        from django.conf import settings
        if getattr(settings, 'USE_S3', False) and self.avatar:
            from homepage.s3utils import PublicMediaStorage
            import os

            try:
                s3_storage = PublicMediaStorage()
                local_path = self.avatar.path
                s3_key = f"avatars/{self.user.id}/{os.path.basename(self.avatar.name)}"

                if os.path.exists(local_path):
                    with open(local_path, 'rb') as f:
                        s3_storage.save(s3_key, f)
            except Exception:
                pass

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
            return self.priority.color if self.priority else "#808080"  # Gris por defecto
    
    def get_status_color(self):
            return self.status.color if self.status else "#808080"  # Gris por defecto
    
    def get_type_color(self):
            return self.type.color if self.type else "#808080"  # Gris por defecto
    
    def get_severity_color(self):
            return self.severity.color if self.severity else "#808080"  # Gris por defecto
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
        """Devuelve el tamaño del archivo en formato legible."""
        if self.filesize < 1024:
            return f"{self.filesize} bytes"
        elif self.filesize < 1024 * 1024:
            return f"{self.filesize / 1024:.1f} KB"
        else:
            return f"{self.filesize / (1024 * 1024):.1f} MB"

    def get_file_url(self):
        """Retorna la URL del archivo adjunto"""
        print("==== get_file_url called ====")
        
        if not self.file:
            print("No file attached")
            return None
        
        try:
            # Log file information
            print(f"File name: {self.file.name}")
            print(f"File path: {self.file.path if hasattr(self.file, 'path') else 'No path'}")
            print(f"Storage class: {self.file.storage.__class__.__name__}")
            
            # Intentar obtener la URL directamente
            url = self.file.url
            print(f"Direct URL obtained: {url}")
            return url
        except Exception as e:
            print(f"❌ Error getting direct URL: {e}")
            print(f"Error type: {type(e).__name__}")
            
            # Verificar configuración S3
            from django.conf import settings
            print("\n==== S3 Configuration ====")
            print(f"USE_S3: {getattr(settings, 'USE_S3', 'Not defined')}")
            print(f"AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Not defined')}")
            print(f"AWS_S3_REGION_NAME: {getattr(settings, 'AWS_S3_REGION_NAME', 'Not defined')}")
            # Print first few chars of credentials for debugging (be careful!)
            print(f"AWS_ACCESS_KEY_ID exists: {'Yes' if hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID else 'No'}")
            print(f"AWS_SECRET_ACCESS_KEY exists: {'Yes' if hasattr(settings, 'AWS_SECRET_ACCESS_KEY') and settings.AWS_SECRET_ACCESS_KEY else 'No'}")
            print(f"AWS_SESSION_TOKEN exists: {'Yes' if hasattr(settings, 'AWS_SESSION_TOKEN') and settings.AWS_SESSION_TOKEN else 'No'}")
            
            # Use the existing PublicMediaStorage from s3utils
            print("\n==== Trying PublicMediaStorage ====")
            from homepage.s3utils import PublicMediaStorage
            
            try:
                # Create storage instance
                print("Creating PublicMediaStorage instance")
                storage = PublicMediaStorage()
                print(f"Storage class: {storage.__class__.__name__}")
                
                # Construct file path
                file_path = f"issues/{self.issue.id}/{self.filename}"
                print(f"Constructed file path: {file_path}")
                
                # Check if file exists
                print(f"Checking if file exists at path: {file_path}")
                exists = storage.exists(file_path)
                print(f"File exists in S3: {exists}")
                
                if exists:
                    # Generate URL
                    print("Generating S3 URL")
                    url = storage.url(file_path)
                    print(f"S3 URL generated: {url}")
                    return url
                else:
                    print("⚠️ File not found in S3")
                    
                    # Try with media prefix
                    print("Trying with 'media/' prefix")
                    media_path = f"media/{file_path}"
                    print(f"Alternative path: {media_path}")
                    if storage.exists(media_path):
                        print(f"File exists at alternative path: {media_path}")
                        url = storage.url(media_path)
                        print(f"Alternative URL generated: {url}")
                        return url
                    else:
                        print("⚠️ File not found with media prefix either")
            except Exception as s3_error:
                print(f"❌ S3 storage error: {s3_error}")
                print(f"Error type: {type(s3_error).__name__}")
                import traceback
                print(traceback.format_exc())
            
            # Fallback to direct boto3 approach
            print("\n==== Trying direct boto3 approach ====")
            try:
                import boto3
                from django.conf import settings
                
                print("Creating S3 client")
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    aws_session_token=getattr(settings, 'AWS_SESSION_TOKEN', None),
                    region_name=settings.AWS_S3_REGION_NAME
                )
                print("S3 client created successfully")
                
                # Try different paths
                file_key = f"media/issues/{self.issue.id}/{self.filename}"
                print(f"Attempting to generate URL for: {file_key}")
                
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                        'Key': file_key
                    },
                    ExpiresIn=3600
                )
                print(f"Presigned URL generated: {url[:30]}...")
                return url
            except Exception as boto_error:
                print(f"❌ Boto3 error: {boto_error}")
                print(f"Error type: {type(boto_error).__name__}")
                import traceback
                print(traceback.format_exc())
            
            # Final fallback
            print("\n==== Using local fallback URL ====")
            local_url = f"/media/issues/{self.issue.id}/{self.filename}"
            print(f"Fallback local URL: {local_url}")
            return local_url
    
    def save(self, *args, **kwargs):
        # Call the original save method first
        super().save(*args, **kwargs)
        
        # If using S3, ensure file is uploaded
        from django.conf import settings
        if getattr(settings, 'USE_S3', False) and self.file:
            from homepage.s3utils import PublicMediaStorage
            import os
            
            # Create S3 storage instance
            s3_storage = PublicMediaStorage()
            
            # Get local file path
            local_path = self.file.path
            
            # Construct S3 key
            s3_key = f"issues/{self.issue.id}/{self.filename}"
            
            # Upload to S3
            if os.path.exists(local_path):
                with open(local_path, 'rb') as f:
                    s3_storage.save(s3_key, f)
    
class Comments(models.Model):
        comment= models.CharField (max_length = 280)
        issue = models.ForeignKey(Issue, on_delete=models.CASCADE)
        user = models.ForeignKey('socialaccount.socialaccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='comment_owner')
        created_at = models.DateTimeField(auto_now_add=True)


def get_avatar_upload_path(instance, filename):
    """Generate upload path for avatar images"""
    return f'avatars/{instance.user.id}/{filename}'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(null=True, blank=True)
    avatar = models.ImageField(upload_to=get_avatar_upload_path, null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
    
    def delete_avatar(self):
        """Delete the avatar file and clear the field"""
        if self.avatar:
            # Delete the file from storage
            if self.avatar.storage.exists(self.avatar.name):
                self.avatar.delete()
            self.avatar = None
            self.save()

    def save(self, *args, **kwargs):
        # Call the original save method first
        super().save(*args, **kwargs)
        
        # If using S3, ensure avatar is uploaded
        from django.conf import settings
        if getattr(settings, 'USE_S3', False) and self.avatar:
            from homepage.s3utils import PublicMediaStorage
            import os
            
            try:
                # Create S3 storage instance
                s3_storage = PublicMediaStorage()
                
                # Get local file path
                local_path = self.avatar.path
                
                # Construct S3 key
                s3_key = f"avatars/{self.user.id}/{os.path.basename(self.avatar.name)}"
                
                # Upload to S3
                if os.path.exists(local_path):
                    print(f"Uploading avatar to S3: {s3_key}")
                    with open(local_path, 'rb') as f:
                        s3_storage.save(s3_key, f)
                    print("Avatar uploaded successfully to S3")
            except Exception as e:
                print(f"Error uploading avatar to S3: {e}")
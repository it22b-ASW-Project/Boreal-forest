from django.db import models
from django.utils.timezone import now

from django.utils import timezone

class Priority(models.Model):
    name = models.CharField(max_length=20, primary_key=True)  
    color = models.CharField(max_length=7, default="#808080")  

    def __str__(self):
        return self.name

class Type(models.Model):
    name = models.CharField(max_length=20, primary_key=True)  
    color = models.CharField(max_length=7, default="#808080") 

    def __str__(self):
        return self.name

class Severity(models.Model):
    name = models.CharField(max_length=20, primary_key=True) 
    color = models.CharField(max_length=7, default="#808080")  

    def __str__(self):
        return self.name

class Status(models.Model):
    name = models.CharField(max_length=20, primary_key=True)  
    color = models.CharField(max_length=7, default="#808080") 

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
class Comments(models.Model):
        comment= models.CharField (max_length = 280)
        issue = models.ForeignKey(Issue, on_delete=models.CASCADE)
        user = models.ForeignKey('socialaccount.socialaccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='comment_owner')
        created_at = models.DateTimeField(auto_now_add=True)

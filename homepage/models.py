from django.db import models

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

    def get_priority_color(self):
            return self.priority.color if self.priority else "#808080"  # Gris por defecto
    
    def get_status_color(self):
            return self.status.color if self.status else "#808080"  # Gris por defecto
    
    def get_type_color(self):
            return self.type.color if self.type else "#808080"  # Gris por defecto
    
    def get_severity_color(self):
            return self.severity.color if self.severity else "#808080"  # Gris por defecto
    
class Watch(models.Model):
        watcher = models.ForeignKey('socialaccount.socialaccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='watcher')
        issue = models.ForeignKey(Issue, on_delete=models.CASCADE)

class Assigned(models.Model):
    assigned = models.ForeignKey('socialaccount.socialaccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned')
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE)
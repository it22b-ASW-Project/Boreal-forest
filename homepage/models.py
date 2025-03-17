from django.db import models

# Create your models here.
class Issue(models.Model):
    subject = models.CharField(max_length=30)
    description = models.CharField(max_length=280)
    status = models.CharField(max_length=20,default='New')
    type = models.CharField(max_length=20,default='Question')
    severity =models.CharField(max_length=20,default='Minor')
    priority = models.CharField(max_length=20,default='Normal')
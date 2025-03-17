from django.db import models

# Create your models here.
class Issue(models.Model):
    subject = models.CharField(max_length=30)
    description = models.CharField(max_length=280)
    #status
    #type
    #serverities
    #priority
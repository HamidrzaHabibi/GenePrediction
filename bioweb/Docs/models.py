from django.db import models
import uuid
# Create your models here.
class Documents(models.Model):
    name = models.CharField(max_length=200,blank=False,null=False)
    description=models.CharField(max_length=500,blank=False,null=False)
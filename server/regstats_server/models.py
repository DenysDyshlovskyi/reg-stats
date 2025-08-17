from django.db import models
import uuid

# Create your models here.

# Model for clients table
class Clients(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,editable=False)
    username = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)
    computer_name = models.CharField(max_length=255)
import string
import random
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('examiner', 'Examiner'),
        ('candidate', 'Candidate'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='candidate')

class Session(models.Model):
    code = models.CharField(max_length=8, unique=True)
    examiner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    code_content = models.TextField(blank=True, default='')

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)

class ActionLog(models.Model):
    EVENT_CHOICES = [
        ('join', 'Join'),
        ('leave', 'Leave'),
        ('copy', 'Copy'),
        ('paste', 'Paste'),
        ('blur', 'Blur'),
    ]
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=10, choices=EVENT_CHOICES)
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

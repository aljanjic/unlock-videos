from django.db import models
from django.contrib.auth.models import User

class MediaFile(models.Model):
    # user = models.ForeignKey(User, on_delete=models.SET_NULL, null = True)
    file_name = models.CharField(max_length=1024)
    length = models.DurationField()
    size = models.IntegerField()
    upload_timestamp = models.DateTimeField(auto_now_add=True)
    transcript = models.TextField(blank=True)
    file = models.FileField(null=True)

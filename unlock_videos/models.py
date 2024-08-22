from django.db import models
from django.contrib.auth.models import User

from pydub import AudioSegment
from moviepy.editor import VideoFileClip
import os
from datetime import timedelta


class MediaFile(models.Model):
    FILE_TYPE_CHOICES = [
        ('audio', 'Audio'),
        ('video', 'Video'),
    ]

    # user = models.ForeignKey(User, on_delete=models.SET_NULL, null = True)
    file_name = models.CharField(max_length=1024)
    length = models.DurationField(blank=True, null=True)
    size = models.IntegerField(blank=True, null=True)
    upload_timestamp = models.DateTimeField(auto_now_add=True)
    transcript = models.TextField(blank=True)
    file = models.FileField(null=True)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, blank=True)

    def __str__(self):
        return self.file_name
    
    def save(self, *args, **kwargs):
        if self.file:

            extension = os.path.splitext(self.file.name)[1].lower()
            if extension in ['.mp4', '.avi', '.mov']:
                self.file_type = 'video'
            elif extension in ['.mp3', '.wav', '.aac']:
                self.file_type = 'audio'
            else:
                raise ValueError(f"Unsupported file type: {extension}")
            
            self.size = self.file.size
            
            if self.file_type == 'video':
                try:
                    video = VideoFileClip(self.file.path)
                    self.length = timedelta(seconds=video.duration)  # Convert to timedelta
                except Exception as e:
                    raise ValueError(f"Unable to calculate video length: {str(e)}")
            elif self.file_type == 'audio':
                try:
                    audio = AudioSegment.from_file(self.file.path)
                    self.length = timedelta(seconds=audio.duration_seconds)  # Convert to timedelta
                except Exception as e:
                    raise ValueError(f"Unable to calculate audio length: {str(e)}")


        super(MediaFile, self).save(*args, **kwargs)
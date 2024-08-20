from django.contrib import admin
from .models import MediaFile

class MediaFileAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'upload_timestamp')

admin.site.register(MediaFile, MediaFileAdmin)
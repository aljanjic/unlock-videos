from django.shortcuts import render
from django.http import HttpResponse, JsonResponse


from .models import MediaFile
from .serializers import MediaFileSerializer

def index(request):
    return render(request, 'unlock_videos/index.html')

def mediafiles(request):
    data = MediaFile.objects.all()
    serializer = MediaFileSerializer(data, many=True)
    return JsonResponse({'mediafiles' : serializer.data})


def home(request):
    return HttpResponse('Hello World')

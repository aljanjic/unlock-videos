from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse, JsonResponse

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import MediaFile
from .serializers import MediaFileSerializer, UserSerializer

from .whisper_utils import whisper_model

def index(request):
    return render(request, 'unlock_videos/index.html')

def home(request):
    return HttpResponse('Hello World')

@api_view(['GET', 'POST'])
# @permission_classes([IsAuthenticated])
def files(request):
    if request.method == 'GET':
        data = MediaFile.objects.all()
        serializer = MediaFileSerializer(data, many=True)
        return Response({'files' : serializer.data})
    
    elif request.method == 'POST':
        serializer = MediaFileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'DELETE', 'PATCH'])
# @permission_classes([IsAuthenticated])
def file(request, file_id):
    try:
        data = MediaFile.objects.get(pk=file_id)
    except MediaFile.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = MediaFileSerializer(data)
        return Response({'file' : serializer.data})
    
    if request.method == 'PATCH':
        serializer = MediaFileSerializer(data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        data.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 
    
@api_view(['POST'])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)

# @api_view(['POST'])
# def transcribe(request, file_id):
#     try:
#         audio_file = MediaFile.objects.get(pk = file_id)
#     except MediaFile.DoesNotExist:
#         return Response(status=status.HTTP_404_NOT_FOUND)
       
#     audio_file_location = audio_file.file.path
#     model = whisper.load_model('base')
#     result = model.transcribe(audio_file_location)

#     audio_file.transcript = result['text']
#     audio_file.save()
    
@api_view(['POST'])
def transcribe(request, file_id):
    # Fetch the MediaFile object, or return a 404 error if not found
    audio_file = get_object_or_404(MediaFile, pk=file_id)

    if not audio_file.file:
        return Response({"error": "No file associated with this MediaFile."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = whisper_model.transcribe(audio_file.file.path)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    audio_file.transcript = result['text']
    audio_file.save()
    
    return Response({"message": "Transcription successful", "transcript": audio_file.transcript}, status=status.HTTP_200_OK)
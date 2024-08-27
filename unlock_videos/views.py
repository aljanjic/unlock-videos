import os
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse, JsonResponse

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import MediaFile
from .serializers import MediaFileSerializer, UserSerializer
from django.conf import settings

from .utils import extract_audio_from_video
from .whisper_utils import whisper_model

def index(request):
    return render(request, 'unlock_videos/index.html')

def home(request):
    return HttpResponse('Hello World')

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def files(request):
    if request.method == 'GET':
        # data = MediaFile.objects.all()
        data = request.user.media_files.all()
        serializer = MediaFileSerializer(data, many=True)
        return Response({'files' : serializer.data})
    
    elif request.method == 'POST':
        serializer = MediaFileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'DELETE', 'PATCH'])
@permission_classes([IsAuthenticated])
def file(request, file_id):
    try:
        # data = MediaFile.objects.get(pk=file_id)
        # data = request.user.media_files.get(pk=file_id)
        data = get_object_or_404(MediaFile, pk= file_id, user=request.user)
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
@permission_classes([IsAuthenticated])
def transcribe(request, file_id):
    media_file = get_object_or_404(MediaFile, pk=file_id, user=request.user) 

    if not media_file.file:
        return Response({"error": "No file ID associated with this MediaFile."}, status=status.HTTP_400_BAD_REQUEST)
    
    if media_file.file_type == 'video':
        audio_file_path = os.path.join(settings.MEDIA_ROOT, f"audio_{media_file.id}.wav")
        try:
            extract_audio_from_video(media_file.file.path, audio_file_path)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        audio_file_path = media_file.file.path

    try:
        result = whisper_model.transcribe(audio_file_path)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # for i in range(0,len(result['segments'])):
    #     print('############### Result: ',result['segments'][i]['start'])
    #     print('############### Result: ',result['segments'][i]['end'])
    #     print('############### Result: ',result['segments'][i]['text'])
    #     print('------------------------------------')

    media_file.transcript = result['text']
    media_file.save()
    
    return Response({"message": "Transcription successful", "transcript": media_file.transcript}, status=status.HTTP_200_OK)

@api_view(['POST'])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)
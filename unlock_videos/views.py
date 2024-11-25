import os
import json
from time import sleep
from dotenv import load_dotenv

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, FileResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated

from .models import MediaFile
from .serializers import MediaFileSerializer, UserSerializer
from django.conf import settings

from openai import OpenAI
from .utils import extract_audio_from_video, create_summary_from_transcript, create_assistant
from .whisper_utils import whisper_model


client = OpenAI()
load_dotenv()


## Ovo ce da ispunjava def file kada se otvori, ili mozda start_chat ovo isto moze da se pobrine za transcript kad vec ionako pravi novi threadI, ali mu file mora obezbijediti pk
#  data = get_object_or_404(MediaFile, pk=file_id, user=request.user)
# threadID = ''
# pk = ''
# transcript = ''

def index(request):
    return render(request, 'unlock_videos/index.html')

def home(request):
    return HttpResponse('Hello World')

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def files(request):
    if request.method == 'GET':
        data = request.user.media_owner.all()
        #data = MediaFile.objects.all()
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
        data = get_object_or_404(MediaFile, pk=file_id, user=request.user)
        #data = MediaFile.objects.get(pk=file_id)
        #data = request.user.media_owner.get(pk=file_id)
    except MediaFile.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = MediaFileSerializer(data)
        request.session['shared_things'] = {"threadID": client.beta.threads.create(), "transcript": data.transcript}
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
    
@api_view(['GET'])   
@permission_classes([IsAuthenticated])
def download_file(request, file_id):
    try:
        data = get_object_or_404(MediaFile, pk=file_id, user=request.user)
        #data = MediaFile.objects.get(pk=file_id)
    except MediaFile.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    file_path = data.file.path
    try:
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{data.file.name}"'
        return response
    except FileNotFoundError:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transcribe(request, file_id):
    media_file = get_object_or_404(MediaFile, pk=file_id, user=request.user) 
    #media_file = MediaFile.objects.get(pk=file_id)

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
@permission_classes([IsAuthenticated])
def summary(request, file_id):

    media_file = get_object_or_404(MediaFile, pk=file_id, user=request.user)
    #media_file = MediaFile.objects.get(pk=file_id)
    if not media_file.file:
        return Response({"error": "No file ID associated with this MediaFile"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = create_summary_from_transcript(media_file.transcript, client)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    media_file.summary = result
    media_file.save()

    return Response({"message": "Summary successful", "summary": media_file.summary}, status=status.HTTP_200_OK)


@api_view(['POST'])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'User created successfully.'}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# assistant_id = create_assistant(client)
assistant_id = os.getenv('ASSISTANT_ID')

@api_view(['GET'])
def start_conversation(request):
    """Start a new conversation."""
    if request.method == "GET":
        # thread = client.beta.threads.create()
        thread_id = shared_things.get('threadID')        
        # return Response({"thread_id": thread.id})
        return Response({"thread_id": thread_id})
    return Response({"error": "Invalid HTTP method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
def chat(request):
    """Handle chat interactions."""
    if request.method == "POST":
        shared_things = request.session.get('shared_things')
        transcript = shared_things.get('transcript')
        data = json.loads(request.body)
        thread_id = data.get('thread_id')
        user_input = data.get('message', '')

        if not thread_id:
            return Response({"error": "Missing thread_id"}, status=status.HTTP_400_BAD_REQUEST)

        # Add the user's message to the thread
        client.beta.threads.messages.create(thread_id=thread_id, role="user", content=user_input)

        # Run the assistant # Mozda i ovo ubaciti kao parametar : instructions=f"Please address the user's question and provide an answer from the following transcript only: {transcript} Remember, use the transcript from the first message as your only source of information. It is important not to answer or provide any information that out side of transcript scope"
        # salje se transcript samo prvi put, nakon toga bez transcripta jer se trose tokeni
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread_id, 
            assistant_id=assistant_id,
            instructions=f"Please address the user's question and provide an answer from the following transcript only: ```{transcript}``` Remember, use the transcript from this message as your only source of information. It is important not to answer or provide any information that out side of transcript scope"     
) 


        # Check for completion
        # while True:
        #     run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        #     if run_status.status == 'completed':
        #         break
        #     sleep(1)
        while True:
            if run.status == 'completed':
                break
            sleep(1)

        # Retrieve the assistant's response
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        response = messages.data[0].content[0].text.value

        return Response({"response": response})
    return Response({"error": "Invalid HTTP method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
from moviepy import VideoFileClip
import os
from django.conf import settings

def extract_audio_from_video(video_path, output_audio_path):
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(output_audio_path)
        return output_audio_path
    except Exception as e:
        raise Exception(f"Failed to extract audio: {str(e)}")
    
TRANSCRIPT_INSTRUCTIONS = """You are an Audio and Video file transcript interpreter. \
You will be provided with a transcript and you will be answering user questions and drawing the conclusions only from the provided transcript, \
DO NOT use any other external knowledge beside provided transcript. \
Do not ask to be provided with more information. In situations when the \
question is not related to transcript answer: 'Unfortunately, that information is not included in transcript'"""

def create_summary_from_transcript(transcript, client):
    try:
        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            instructions=f"{TRANSCRIPT_INSTRUCTIONS}\n\nTranscript:\n{transcript}",
            input="What is this video about?",
        )
        return response.output_text
    except Exception as e:
        raise Exception(f"Failed to create summary: {str(e)}")

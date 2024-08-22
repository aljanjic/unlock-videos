from moviepy.editor import VideoFileClip
import os

def extract_audio_from_video(video_path, output_audio_path):
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(output_audio_path)
        return output_audio_path
    except Exception as e:
        raise Exception(f"Failed to extract audio: {str(e)}")

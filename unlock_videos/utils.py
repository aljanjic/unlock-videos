from moviepy.editor import VideoFileClip
import os
from openai import OpenAI

def extract_audio_from_video(video_path, output_audio_path):
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(output_audio_path)
        return output_audio_path
    except Exception as e:
        raise Exception(f"Failed to extract audio: {str(e)}")
    
def create_summary_from_transcript(transcript):
    try:
        client = OpenAI()
        thread = client.beta.threads.create()

        assistant = client.beta.assistants.create(
            name="Audio an Video file transcript interpreter",
            instructions="You are an Audio an Video file transcript interpreter. You will be provided with a transcript and you will be answering user questions only from the provided transcript, DO NOT use any other external knowledge beside provided transcript. Do not ask to be provided with more information. In situations when the question is not related to transcript answer: 'Unfortunately, that information is not included in transcript'",
            tools=[],
            model="gpt-4o-mini",
        )

        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="What is this video about?"
        )

        run = client.beta.threads.runs.create_and_poll(
          thread_id=thread.id,
          assistant_id=assistant.id,
          instructions=f"Please address the user's question and provide an answer from the following transcript only: {transcript} Remember, use the transcript from the first message as your only source of information. It is important not to answer or provide any information that out side of transcript scope"
        )

        if run.status == 'completed': 
          messages = client.beta.threads.messages.list(
            thread_id=thread.id
          )
          print(messages.data[0].content[0].text.value)
          print('')
          print('thread_id: ', thread.id)
          print('assistant_id: ', assistant.id)
          print(': ',)
          return messages.data[0].content[0].text.value
        else:
          print(run.status)
        
    except Exception as e:
        raise Exception(f"Failed to create summary: {str(e)}")

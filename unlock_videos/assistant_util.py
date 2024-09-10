from openai import OpenAI


transcript = """Hey Matush, how are you? Hi, Oksha. I'm very good. I feel very productive because we found and time at Friday
    at 7 p.m. to work. So I'm very happy and very motivated. I'm glad that you're happy because this is a good 
    project and we can learn a lot from it. Yes. And we have accomplished what today because we had straight go
    to run your Python script with Docker. I think we did it, but one thing is not finished that we somehow 
    cannot write to file. We cannot create a file because of I guess, I guess, permission problems, but otherwise
    the thing is working. It's at least it's printing the text. Well, it's a video. So I think we are successful
    today. Yeah, that's cool. High degree. So let's try and test the script and our Docker application one
    more time with this new recording. You agree? Yes. Absolutely. Cool. """

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


# Without the Stream

# if run.status == 'completed': 
#   messages = client.beta.threads.messages.list(
#     thread_id=thread.id
#   )
#   print(messages)
#   print('')
#   print('thread_id: ', thread.id)
#   print('assistant_id: ', assistant.id)
#   print(': ',)
# else:
#   print(run.status)



from typing_extensions import override
from openai import AssistantEventHandler
 
# First, we create a EventHandler class to define
# how we want to handle the events in the response stream.
 
class EventHandler(AssistantEventHandler):    
  @override
  def on_text_created(self, text) -> None:
    print(f"\nassistant > ", end="", flush=True)
      
  @override
  def on_text_delta(self, delta, snapshot):
    print(delta.value, end="", flush=True)
      
  def on_tool_call_created(self, tool_call):
    print(f"\nassistant > {tool_call.type}\n", flush=True)
  
  def on_tool_call_delta(self, delta, snapshot):
    if delta.type == 'code_interpreter':
      if delta.code_interpreter.input:
        print(delta.code_interpreter.input, end="", flush=True)
      if delta.code_interpreter.outputs:
        print(f"\n\noutput >", flush=True)
        for output in delta.code_interpreter.outputs:
          if output.type == "logs":
            print(f"\n{output.logs}", flush=True)
 
# Then, we use the `stream` SDK helper 
# with the `EventHandler` class to create the Run 
# and stream the response.
 
with client.beta.threads.runs.stream(
  thread_id=thread.id,
  assistant_id=assistant.id,
  instructions="Please address the user as Jane Doe. The user has a premium account.",
  event_handler=EventHandler(),
) as stream:
  stream.until_done()
from openai import OpenAI


transcript = """September 11, 1973, a military coup overthrows the government in Chile, ending the longest democratic tradition in Latin America. It was a bloody, bloody coup. Chileans who lived through the coup and years of repression reflect on its meaning for us today. Isabel Ayende and others describe the effects of terror and dictatorship on a people and a nation. Chile, promise of freedom. """

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


# Without the Stream

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
else:
  print(run.status)


# With streaming

# from typing_extensions import override
# from openai import AssistantEventHandler
 
# # First, we create a EventHandler class to define
# # how we want to handle the events in the response stream.
 
# class EventHandler(AssistantEventHandler):    
#   @override
#   def on_text_created(self, text) -> None:
#     print(f"\nassistant > ", end="", flush=True)
      
#   @override
#   def on_text_delta(self, delta, snapshot):
#     print(delta.value, end="", flush=True)
      
#   def on_tool_call_created(self, tool_call):
#     print(f"\nassistant > {tool_call.type}\n", flush=True)
  
#   def on_tool_call_delta(self, delta, snapshot):
#     if delta.type == 'code_interpreter':
#       if delta.code_interpreter.input:
#         print(delta.code_interpreter.input, end="", flush=True)
#       if delta.code_interpreter.outputs:
#         print(f"\n\noutput >", flush=True)
#         for output in delta.code_interpreter.outputs:
#           if output.type == "logs":
#             print(f"\n{output.logs}", flush=True)
 
# # Then, we use the `stream` SDK helper 
# # with the `EventHandler` class to create the Run 
# # and stream the response.
# print('Thread id: ', thread.id)
# print('Assistant id: ', assistant.id)


# with client.beta.threads.runs.stream(
#   thread_id=thread.id,
#   assistant_id=assistant.id,
#   instructions="Please address the user's question and provide an answer from the following transcript only: {transcript} Remember, use the transcript from the first message as your only source of information. It is important not to answer or provide any information that out side of transcript scope",
#   event_handler=EventHandler(),
# ) as stream:
#   stream.until_done()
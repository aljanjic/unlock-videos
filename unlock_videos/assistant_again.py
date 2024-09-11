from openai import OpenAI

client = OpenAI()

thread_id_='thread_W5bB8IBwrIkW8Sa4QLZpfPXZ'

message = client.beta.threads.messages.create(
  thread_id= thread_id_,
  role="user",
  content="What is the video about?"
)

assistant_id_ = 'asst_24B20LUvAxUpdqtSQFlSTekb'

run = client.beta.threads.runs.create_and_poll(
  thread_id= thread_id_,
  assistant_id= assistant_id_,
)


# Without streem
if run.status == 'completed': 
  messages = client.beta.threads.messages.list(
    thread_id= thread_id_
  )

  print(messages.data[0].content[0].text.value) 
  # print(messages)

  print('thread_id: ', thread_id_)
  print('assistant_id: ', assistant_id_)
  print(': ',)
else:
  print(run.status)
from openai import OpenAI

client = OpenAI()

thread_id_='thread_kHnmwsBDGqrANlVqnnMB9ZvZ'

message = client.beta.threads.messages.create(
  thread_id= thread_id_,
  role="user",
  content="When did the coup ocurred?"
)

assistant_id_ = 'asst_PPfYTrtwNevWRF56v2e559M4'

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
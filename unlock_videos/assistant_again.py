from openai import OpenAI

client = OpenAI()

thread_id_='thread_oBXQ2zlWSoRWMGQXAWHwiDoG'

message = client.beta.threads.messages.create(
  thread_id= thread_id_,
  role="user",
  content="What is Docker?"
)

assistant_id_ = 'asst_UfFRm5BqgdCwOwEML91uqE9Z'

run = client.beta.threads.runs.create_and_poll(
  thread_id= thread_id_,
  assistant_id= assistant_id_,
)



if run.status == 'completed': 
  messages = client.beta.threads.messages.list(
    thread_id= thread_id_
  )
  print(messages)
  print('')
  print('thread_id: ', thread_id_)
  print('assistant_id: ', assistant_id_)
  print(': ',)
else:
  print(run.status)
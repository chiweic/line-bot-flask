from openai import OpenAI

class OpenAIThread():
    
    def __init__(self, api_key: str, assistant_id: str):
        
        # client and assistant are singleton, should init once
        self.client = OpenAI(api_key=api_key)
        self.assistant = self.client.beta.assistants.retrieve(
            assistant_id=assistant_id
        )
        self.thread = self.client.beta.threads.create()


    def qa_polling (self, user_message):
        
        # inject user message to this thread
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=user_message
        )

        
        # associate thread and assistant
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
        )


        if run.status == 'completed':
            messages = self.client.beta.threads.messages.list(
                self.thread.id,
                limit=1
            )
            return messages


import logging
if __name__ == '__main__':
    
    logging.basicConfig(level=logging.INFO)
    
    # retrieve assistant built-previously
    OPENAI_KEY = 'sk-proj-Yb7jEqkkHRXqNmykqp3rT3BlbkFJxNGm170j6k9Vx61GnFFV'
    ASSISTANT_ID='asst_jJvDQj9f43UFWRMY0Bsd6xZV'
    # instance that resemble conversation with a user    
    thread = OpenAIThread(api_key=OPENAI_KEY, assistant_id=ASSISTANT_ID)
    # turns...
    message = thread.qa_polling(user_message='法鼓山的下次禪修活動是什麼時候')
    logging.info(message.data[0].content[0].text.value)
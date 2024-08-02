from flask import Flask
from flask import render_template

# section added from https://github.com/line/line-bot-sdk-python/blob/master/examples/flask-echo/app_with_handler.py
# that add the support on callback with line bot message API
# noted we are using version 3
import os
import sys
import logging


from flask import Flask, request, abort
from linebot.v3 import (
     WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    UserSource
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)

from model import OpenAIThread


# set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

handler = WebhookHandler(channel_secret)

configuration = Configuration(
    access_token=channel_access_token
)

# global instance of the model store, with user_id as key
# this keep track of thread/user
thread_store = {}




@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

from linebot.v3.messaging import ShowLoadingAnimationRequest
import time
@handler.add(MessageEvent, message=TextMessageContent)
def message_text(event):    
    text = event.message.text
    user_id=event.source.user_id
    app.logger.info('received message: {}'.format(text))
    with ApiClient(configuration) as api_client:
        # instance of line bot api
        line_bot_api = MessagingApi(api_client)
        # incoming text == profile
        if text == 'profile':
            if isinstance(event.source, UserSource):
                profile = line_bot_api.get_profile(user_id=event.source.user_id)
                # show animation
                line_bot_api.show_loading_animation(
                        show_loading_animation_request=ShowLoadingAnimationRequest(
                            chatId=event.source.user_id
                        )
                ) 
                # lengthy computation
                time.sleep(5)
                # return message
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(text='UserId: '+ event.source.user_id),
                            TextMessage(text='Display name: ' + profile.display_name),
                            TextMessage(text='Status message: ' + str(profile.status_message))
                        ]
                    )
                )
                
                
            else:
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="Bot can't use profile API without user ID")]
                    )
                )


        else:
            
            # look up instance that spin up from store
            #if user_id in thread_store:
            #    thread = thread_store[user_id]
            #else:   
            #    pass            
            # based on user_id: 
            thread = OpenAIThread(
                api_key = os.getenv('OPENAI_KEY'), 
                assistant_id = os.getenv('ASSISTANT_ID')
            )

            # show progress/animation
            line_bot_api.show_loading_animation(
                        show_loading_animation_request=ShowLoadingAnimationRequest(
                            chatId=event.source.user_id
                        )
                ) 
            
            # this will take awhile
            chatgpt_reply = thread.qa_polling(user_message=text)
            

            # reply via messaing API
            line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=chatgpt_reply.data[0].content[0].text.value)]
                    )
                )

        #else:
            # all other no leading command text hint
        #    line_bot_api.reply_message(
        #        ReplyMessageRequest(
        #            replyToken= event.reply_token,
        #            messages=[TextMessage(text=event.message.text)]
        #        )
        #    )

        #line_bot_api.show_loading_animation
        #(
        #    ShowLoadingAnimationRequest(chatId=event.source.user_id, loadingSeconds=5)
        #)

        


@app.route("/")
def hello_world():
    return render_template("index.html")

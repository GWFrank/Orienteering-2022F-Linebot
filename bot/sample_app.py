# Src:
# https://ithelp.ithome.com.tw/articles/10217767 
# https://ithelp.ithome.com.tw/articles/10229943

from __future__ import unicode_literals
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from werkzeug.middleware.proxy_fix import ProxyFix

import configparser

import random

app = Flask(__name__)

# LINE 聊天機器人的基本資料
config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))

LeaderBoard = dict()

# 接收 LINE 的資訊
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        print(body, signature)
        handler.handle(body, signature)

    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 學你說話
@handler.add(MessageEvent, message=TextMessage)
def pretty_echo(event):

    if event.source.user_id != "Udeadbeefdeadbeefdeadbeefdeadbeef":

        if event.source.user_id in LeaderBoard:
            LeaderBoard[event.source.user_id] += 1
        else:
            LeaderBoard[event.source.user_id] = 1
        
        # # Phoebe 愛唱歌
        # pretty_note = '♫♪♬'
        # pretty_text = ''
        # for i in event.message.text:
        #     pretty_text += i
        #     pretty_text += random.choice(pretty_note)
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text=pretty_text)
        # )
        
        msg = f"Howdy, user id {event.source.user_id}!\nYou've sent {LeaderBoard[event.source.user_id]} messages to me!"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )

if __name__ == "__main__":
    # app.run()
    pass

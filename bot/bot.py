# Src:
# https://ithelp.ithome.com.tw/articles/10217767 
# https://ithelp.ithome.com.tw/articles/10229943

from __future__ import unicode_literals
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from werkzeug.middleware.proxy_fix import ProxyFix

import configparser
import json

app = Flask(__name__)

# LINE 聊天機器人的基本資料
config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))

class Station:
    def __init__(self, sid: int, name: str, hints: tuple[str, str], points: int):
        self._sid = sid
        self._name = name
        self._hints = hints
        self._points = points
        self._captured = False
    
    def get_hints(self):
        pass
    
    def get_points(self) -> int:
        if self._captured:
            return self._points
        else:
            self._captured = True
            return round(1.5*self._points)

class Team:
    def __init__(self, user_id: str, name: str):
        self._user_id = user_id
        self._name = name
        self.score = 0
        self._answered_stations = set()
        self._captured_stations = set()
    
    def change_name(self, new_name: str) -> None:
        self._name = new_name
    
    def get_info(self) -> str:
        return f"{self._name} | {self.score}"

TeamList = dict[str, Team]
StationList = list[Station]
Teams = TeamList()
Stations = StationList()

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

@handler.add(MessageEvent, message=TextMessage)
def getCommand(event: MessageEvent):

    # Ignore Line's verify message
    if event.source.user_id == "Udeadbeefdeadbeefdeadbeefdeadbeef":
        return
    
    msgs = list()

    args = event.message.text.split()
    cmd = args[0]
    if cmd == "register":
        # Register team name
        # Usage: register <teamname>
        if len(args) != 2:
            msgs.append(TextSendMessage(
                text = """格式錯誤。
                指令格式： register <team name>
                範例： register 第一組
                備註： 隊伍名稱不能含有空白、換行
                """
            ))
        else:
            uid = event.source.user_id
            if not (uid in Teams):
                Teams[uid] = Team(uid, args[1])
            else:
                Teams[uid].change_name(args[1])
            msgs.append(TextSendMessage(
                text = f"已成功註冊為「{args[1]}」"
            ))
    elif cmd == "leaderboard":
        # Show leaderboard & status of each question
        leaderboard_msg = "隊伍名稱 | 分數\n"
        for t in sorted(Teams.values(), key=lambda x:x.score, reverse=True):
            leaderboard_msg += t.get_info()
        msgs.append(TextSendMessage(text=leaderboard_msg))
    elif cmd == "answer":
        # Answer questions about stations
        pass
    elif cmd == "capture":
        # Capture a station
        pass
    else:
        msgs.append(TextSendMessage(
            text = "找不到指令，請檢查是否拼錯字"
        ))

    line_bot_api.reply_message(
        event.reply_token,
        msgs
        # TextSendMessage(text=msg)
    )

if __name__ == "__main__":
    pass

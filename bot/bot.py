# Src:
# https://ithelp.ithome.com.tw/articles/10217767 
# https://ithelp.ithome.com.tw/articles/10229943

from __future__ import unicode_literals
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
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
    def __init__(self, sid: int, name: str, hints: tuple[str, str], points: int, flag: str):
        self._sid = sid
        self._name = name
        self._hints = hints
        self._points = points
        self._captured = False
        self._flag = flag
    
    def check_answer(self, sid: int, name: str) -> bool:
        return (sid == self._sid and name == self._name)
    
    def check_capture(self, sid: int, flag: str) -> bool:
        return (sid == self._sid and flag == self._flag)

    def get_hints(self) -> tuple[str, str]:
        return self.hints
    
    def get_points(self) -> tuple[bool, int]:
        if self._captured:
            return (False, self._points)
        else:
            self._captured = True
            return (True, round(1.5*self._points))

class Team:
    def __init__(self, user_id: str, name: str):
        self._user_id = user_id
        self._name = name
        self.score = 0
        self._answered_stations = list()
        self._captured_stations = list()
    
    def change_name(self, new_name: str) -> None:
        self._name = new_name
    
    def get_info(self) -> str:
        return f"{self._name} | {self.score}"

    def check_answered(self, sid: int) -> bool:
        return sid in self._answered_stations
    
    def check_captured(self, sid: int) -> bool:
        return sid in self._captured_stations
    
    def answered(self, sid: int) -> None:
        self._answered_stations.append(sid)
    
    def captured(self, sid: int) -> None:
        self._captured_stations.append(sid)


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
            
            tmp_team = list()
            for t in Teams:
                tmp_team.append(vars(Teams[t]))
            with open("team.json", "w", newline='', encoding="utf-8") as json_file:
                json.dump(tmp_team, json_file, ensure_ascii=False)

    elif cmd == "leaderboard":
        # Show leaderboard & status of each question
        leaderboard_msg = "隊伍名稱 | 分數\n"
        for t in sorted(Teams.values(), key=lambda x:x.score, reverse=True):
            leaderboard_msg += t.get_info()
        msgs.append(TextSendMessage(text=leaderboard_msg))
    elif cmd == "answer":
        # Answer questions about stations
        if len(args) != 3 or not args[1].isdigit():
            msgs.append(TextSendMessage(
                text = """格式錯誤。
                指令格式： answer <station_id> <your_answer>
                範例： answer 1 定向越野好讚
                備註： <station_id> 須為數字，答案不能含有空白、換行
                """
            ))
        else:
            uid = event.source.user_id
            sid, name = int(args[1]), args[2]
            if Teams[uid].check_answered(sid): # When the station has been answered
                msgs.append(TextSendMessage(
                    text = "你好像已經回答過這站了喔！！"
                ))
            else:
                for t in Stations:
                    if t.check_answer(sid, name):
                        hint = t.get_hints()
                        msgs.append(
                            TextSendMessage(text="恭喜你答對了，以下是你的站內地圖以及要找的地方。"),
                            ImageSendMessage(original_content_url=hint[0]),
                            ImageSendMessage(original_content_url=hint[1])
                        )
                        Teams[uid].answered(sid)
                else: # When no station matched
                    msgs.append(TextSendMessage(
                        text = "也許你好像哪裡答錯了QQ"
                    ))

    elif cmd == "capture":
        # Capture a station
        if len(args) != 3 or not args[1].isdigit():
            msgs.append(TextSendMessage(
                text = """格式錯誤。
                指令格式： capture <station_id> <your_flag>
                範例： capture 1 flag\{定向越野好讚\}
                備註： <station_id> 須為數字，<your_flag>為一個形式為flag\{<content>\}的字串
                """
            ))
        else:
            uid = event.source.user_id
            sid, flag = int(args[1]), args[2]
            if Teams[uid].check_captured(sid):
                msgs.append(TextSendMessage(
                    text = "再傳一次是不會獲得兩倍分數的"
                ))
            else:
                for t in Stations:
                    if t.check_capture(sid, flag):
                        first, pts = t.get_points()
                        Teams[uid].captured(sid)
                        Teams[uid].score += pts
                        if first:
                            msgs.append(TextSendMessage(
                                text = f"""恭喜你獲得本站的首殺
                                獲得分數{pts}
                                目前總得分{Teams[uid].score}
                                """
                            ))
                        else:
                            msgs.append(TextSendMessage(
                                text = f"""恭喜你獲得本站的flag
                                獲得分數{pts}
                                目前總得分{Teams[uid].score}
                                """
                            ))
                else:
                    msgs.append(TextSendMessage(
                        text = "flag好像不是這個QQ，請檢查看看有沒有寫錯字"
                    ))
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
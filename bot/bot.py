from __future__ import unicode_literals
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from werkzeug.middleware.proxy_fix import ProxyFix

import configparser
import json

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))


class Station:
    def __init__(
        self,
        sid: int,
        name: str,
        hints: list[str, str],
        questions: list[str],
        points: list[int],
        flags: list[str],
        captured: bool = False
    ):
        self._sid = sid
        self._name = name
        self._hints = hints
        self._questions = questions
        self._points = points
        self._flags = flags
        self._captured = captured

    def check_answer(self, sid: int, name: str) -> bool:
        return (sid == self._sid and name == self._name)

    def check_capture(self, sid: int, pid: int, flag: str) -> bool:
        if pid <= 0:
            return False
        try:
            return (sid == self._sid and flag == self._flags[pid-1])
        except IndexError:
            return False

    def get_sid(self) -> int:
        return self._sid

    def get_hints(self) -> list[str, str]:
        return self._hints

    def get_points(self, pid: int) -> int:
        return self._points[pid-1]
        # if self._captured:
        #     return (False, self._points)
        # else:
        #     self._captured = True
        #     return (True, round(1.5*self._points))
    
    def get_questions(self) -> list[str]:
        return self._questions


class Team:
    def __init__(
        self,
        user_id: str,
        name: str,
        score: int = 0,
        answered_stations: list = list(),
        captured_stations: list = list()
    ):
        self._user_id = user_id
        self._name = name
        self.score = score
        self._answered_stations = answered_stations
        self._captured_stations = captured_stations

    def change_name(self, new_name: str) -> None:
        self._name = new_name

    def get_info(self) -> str:
        return f"\n{self._name} | {self.score}"

    def check_answered(self, sid: int) -> bool:
        return sid in self._answered_stations

    def check_captured(self, sid: int, pid: int) -> bool:
        return f"{sid}-{pid}" in self._captured_stations

    def answered(self, sid: int) -> None:
        self._answered_stations.append(sid)

    def captures(self, sid: int, pid: int) -> None:
        self._captured_stations.append(f"{sid}-{pid}")


TeamList = dict[str, Team]
StationList = list[Station]


def dict2station(obj):
    return Station(
        obj["_sid"],
        obj["_name"],
        obj["_hints"],
        obj["_questions"],
        obj["_points"],
        obj["_flags"],
        obj["_captured"]
    )


def dict2team(obj):
    return Team(
        obj["_user_id"],
        obj["_name"],
        obj["score"],
        obj["_answered_stations"],
        obj["_captured_stations"]
    )


Teams = TeamList()
Stations = StationList()


def read_db() -> None:
    global Teams, Stations
    try:
        with open("team.json", "r") as f:
            Teams = json.load(f)
            for k, v in Teams.items():
                Teams[k] = dict2team(v)
    except FileNotFoundError:
        Teams = TeamList()
    # Stations = StationList()
    with open("stations.json", "r") as f:
        Stations = json.load(f, object_hook=dict2station)


def write_db() -> None:
    global Teams, Stations
    tmp_team = dict()
    for k, v in Teams.items():
        tmp_team[k] = vars(v)
    with open("team.json", "w", newline="\n", encoding="utf-8") as json_file:
        json.dump(tmp_team, json_file, ensure_ascii=False, indent=4)
    # tmp_stations = list()
    # for s in Stations:
    #     tmp_stations.append(vars(s))
    # with open("stations.json", "w", newline="\n", encoding="utf-8") as json_file:
    #     json.dump(tmp_stations, json_file, ensure_ascii=False, indent=4)


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

    read_db()
    msgs = list()
    args = event.message.text.split()
    print(args)
    cmd = args[0]
    if cmd == "register" or cmd == "Register" or cmd == "r" or cmd == "R":
        # Register team name
        # Usage: register <teamname>
        if len(args) != 2:
            msgs.append(TextSendMessage(text=(
                "格式錯誤。\n"
                "指令格式： register <team name>\n"
                "範例： register 第一組\n"
                "備註： 隊伍名稱不能含有空白、換行"
            )))
        else:
            uid = event.source.user_id
            if not (uid in Teams):
                Teams[uid] = Team(uid, args[1])
            else:
                Teams[uid].change_name(args[1])
            msgs.append(TextSendMessage(
                text=f"已成功註冊為「{args[1]}」"
            ))

    elif cmd == "leaderboard" or cmd == "Leaderboard" or cmd == "l" or cmd == "L":
        # Show leaderboard & status of each question
        leaderboard_msg = "隊伍名稱 | 分數"
        for st in sorted(Teams.values(), key=lambda x: x.score, reverse=True):
            leaderboard_msg += st.get_info()
        msgs.append(TextSendMessage(text=leaderboard_msg))
    elif cmd == "answer" or cmd == "Answer" or cmd == "a" or cmd == "A":
        # Answer questions about stations
        if len(args) != 3 or not args[1].isdigit():
            msgs.append(TextSendMessage(text=(
                "格式錯誤。\n"
                "指令格式： answer <station_id> <your_answer>\n"
                "範例： answer 1 定向越野好讚\n"
                "備註： <station_id> 須為數字，答案不能含有空白、換行"
            )))
        else:
            uid = event.source.user_id
            sid, name = int(args[1]), args[2]
            # print(sid, name)
            # When the station has been answered
            if Teams[uid].check_answered(sid):
                for st in Stations:
                    if st.get_sid() == sid:
                        hints = st.get_hints()
                        question_text = ""
                        for i, q in enumerate(st.get_questions()):
                            question_text += f"\n檢查點 {i+1}：{q}"
                        msgs.append(TextSendMessage(text=(f"你好像已經回答過這站了喔！！\n以下是你的站內地圖以及提示圖片。{question_text}")))
                        for h in hints:
                            msgs.append(ImageSendMessage(h, h))
                        break
            else:
                correct = False
                for st in Stations:
                    if st.check_answer(sid, name):
                        correct = True
                        hints = st.get_hints()
                        question_text = ""
                        for i, q in enumerate(st.get_questions()):
                            question_text += f"\n檢查點 {i+1}：{q}"
                        msgs.append(TextSendMessage(text=(f"恭喜你答對了，以下是你的站內地圖以及提示圖片。{question_text}")))
                        for h in hints:
                            msgs.append(ImageSendMessage(h, h))
                        Teams[uid].answered(sid)
                if not correct:  # When no station matched
                    msgs.append(TextSendMessage(
                        text="也許你好像哪裡答錯了QQ"
                    ))

    elif cmd == "capture" or cmd == "Capture" or cmd == "c" or cmd == "C":
        # Capture a station
        if len(args) != 4 or not args[1].isdigit() or not args[2].isdigit():
            msgs.append(TextSendMessage(text=(
                "格式錯誤。\n"
                "指令格式： capture <station_id> <point_id> <your_flag>\n"
                "範例： capture 1 1 定向越野好讚\n"
                "備註： <station_id> & <point_id> 須為數字"
            )))
        else:
            uid = event.source.user_id
            sid, pid, flag = int(args[1]), int(args[2]), args[3]
            if not Teams[uid].check_answered(sid):
                msgs.append(TextSendMessage(text="你好像還沒解出這是哪一站喔"))
            elif Teams[uid].check_captured(sid, pid):
                msgs.append(TextSendMessage(text="再傳一次是不會獲得兩倍分數的"))
            else:
                correct = False
                for st in Stations:
                    if st.check_capture(sid, pid, flag):
                        correct = True
                        pts = st.get_points(pid)
                        Teams[uid].captures(sid, pid)
                        Teams[uid].score += pts
                        msgs.append(TextSendMessage(text=(
                            "恭喜你獲得本站的flag\n"
                            f"獲得分數{pts}\n"
                            f"目前總得分{Teams[uid].score}"
                        )))
                        
                if not correct:
                    msgs.append(TextSendMessage(
                        text="flag好像不是這個QQ，請檢查看看有沒有寫錯字"))
    else:
        msgs.append(TextSendMessage(
            text="找不到指令，請檢查是否拼錯字"
        ))

    line_bot_api.reply_message(
        event.reply_token,
        msgs
    )
    write_db()


if __name__ == "__main__":
    pass

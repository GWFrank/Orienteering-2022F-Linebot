FROM python:3.9-alpine
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
# RUN pip install line-bot-sdk flask waitress
RUN mkdir /linebot
CMD /bin/sh

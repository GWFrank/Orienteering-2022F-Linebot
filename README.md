# Orienteering-2022F-Linebot
 
## Setup

1. Go to [ngrok's website](https://ngrok.com)
2. Get your authtoken and put it in `rev_proxy/authtoken`
3. Download ngrok's executable and put it in `rev_proxy/ngrok.tgz`
4. Create `bot/config.ini` in this format:
   ```
   [line-bot]
   channel_access_token = <your channel access token>
   channel_secret = <your channel secret>
   ```
5. Prepare your `bot/stations.json` in this format:
   ```json
   [
   {
        "_sid": "station_id (int)",
        "_name": "station_name",
        "_hints": ["urls_to_hint_photo"],
        "_questions": ["questions_at_each_station"],
        "_points": ["points_for_each_question (int)"],
        "_flags": ["flags_for_each_question"],
        "_captured": false
   }
   ]
   ```
## Run

1. `docker compose build`
2. `docker compose up`
3. Go to http://localhost:4545/status to view ngrok's status
4. Go to Line developer's website to change your Webhook url accordingly

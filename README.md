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
   ```
   {
        "_sid": <station id>,
        "_name": <station name>,
        "_hints": [<url to hint photos>],
        "_questions": [<questions at each station>],
        "_points": [<points for each question>],
        "_flags": [<flags for each question>],
        "_captured": false
    },

## Run

1. `docker compose build`
2. `docker compose up`
3. Go to http://localhost:4545/status to view ngrok's status
4. Go to Line developer's website to change your Webhook url accordingly
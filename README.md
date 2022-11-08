# Orienteering-2022F-Linebot
 
## Setup

1. Go to [ngrok's website](https://ngrok.com)
2. Get your authtoken and put it in `rev_proxy/authtoken`
3. Download ngrok's executable and put it in `rev_proxy/ngrok.tgz`

## Run

1. `docker compose build`
2. `docker compose up`
3. Go to http://localhost:4545/status to view ngrok's status
4. Go to Line developer's website to change your Webhook url accordingly
FROM alpine:latest
COPY authtoken authtoken
COPY ngrok.tgz /tmp/ngrok.tgz
RUN tar -xvf /tmp/ngrok.tgz -C /bin
RUN ngrok config add-authtoken $(cat authtoken)
RUN echo 'web_addr: 0.0.0.0:4040' >> ~/.config/ngrok/ngrok.yml
CMD ngrok help

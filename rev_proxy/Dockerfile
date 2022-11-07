FROM alpine:latest
COPY authtoken authtoken
# Fix rootless alpine bug
COPY resolv.conf /etc/resolv.conf
RUN wget -O ngrok.tgz https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
RUN tar -xvf ngrok.tgz -C /bin
RUN ngrok config add-authtoken $(cat authtoken)
RUN echo 'web_addr: 0.0.0.0:4040' >> ~/.config/ngrok/ngrok.yml
CMD ngrok help

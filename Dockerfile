FROM debian:stable-slim

ENV PIP_BREAK_SYSTEM_PACKAGES 1

RUN apt-get update
RUN apt-get install -y curl python3 python3-pip htop mc nano git
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

WORKDIR /app
COPY src .

WORKDIR /app/OpenIntranet
ENTRYPOINT ["python3", "web.py", "--config=/data/intranet.conf"]

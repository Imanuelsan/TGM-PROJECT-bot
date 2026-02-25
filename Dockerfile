FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
FROM openjdk:17-slim

ARG LAVALINK_JAR="https://github.com/lavalink-devs/Lavalink/releases/download/v4.0.0/lavalink-4.0.0.jar"

RUN apt-get update && \
    apt-get install -y curl && \
    mkdir /lavalink && \
    cd /lavalink && \
    curl -L -o lavalink.jar $LAVALINK_JAR

ENV LAVALINK_PASSWORD=youshallnotpass
ENV LAVALINK_PORT=2333

WORKDIR /lavalink

CMD ["java", "-jar", "lavalink.jar"]

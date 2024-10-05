FROM python:3.11

ENV PYTHONDONOTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

WORKDIR /app

COPY requirements.txt /app

RUN apt-get update && apt-get --no-install-recommends install -y ffmpeg && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8002

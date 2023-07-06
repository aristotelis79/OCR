# syntax=docker/dockerfile:1
FROM python:3

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

EXPOSE 8000
EXPOSE 5678

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

COPY . /app
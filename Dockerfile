FROM python:3.8.10
LABEL maintainer="fredrik@scaleoutsystems.com"

RUN apt update

RUN mkdir /app
COPY . /app/
WORKDIR /app

RUN python -m venv /venv
RUN /venv/bin/python -m pip install --no-cache-dir -e .

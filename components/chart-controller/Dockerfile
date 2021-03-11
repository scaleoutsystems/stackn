FROM python:3.7-alpine
LABEL maintainer="morgan@scaleoutsystems.com"
ENV VERSION="3.0.2"
ENV BASE_URL="https://get.helm.sh"
ENV TAR_FILE="helm-v${VERSION}-linux-amd64.tar.gz"

ENV BRANCH="master"

RUN apk add --update --no-cache curl ca-certificates wget && \
    curl -L ${BASE_URL}/${TAR_FILE} |tar xvz && \
    mv linux-amd64/helm /usr/bin/helm && \
    chmod +x /usr/bin/helm && \
    rm -rf linux-amd64 && \
    apk del curl && \
    rm -f /var/cache/apk/*

RUN mkdir /app
COPY requirements.txt /app/
COPY . /app/

WORKDIR /app

RUN mkdir -p /root/.kube/
RUN touch /root/.kube/config

RUN pip install -r requirements.txt

ENV FLASK_APP=controller/serve.py

# comment out if running docker-compose
ENTRYPOINT gunicorn --bind 0.0.0.0:80 --workers=2 --log-level=debug wsgi:app --limit-request-line 0 --reload

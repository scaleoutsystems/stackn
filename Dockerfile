FROM python:3.8.10-alpine as base
LABEL maintainer="fredrik@scaleoutsystems.com"
WORKDIR /app
COPY requirements.txt .
RUN apk add --update --no-cache \
    build-base \
    python3-dev \
    py3-setuptools \
    postgresql-dev \
    libpq \
    tiff-dev \
    jpeg-dev \ 
    openjpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    libwebp-dev \
    tcl-dev \
    tk-dev \
    harfbuzz-dev \
    fribidi-dev \
    libimagequant-dev \
    libxcb-dev libpng-dev \
    && pip install --no-cache-dir -r requirements.txt

FROM bitnami/kubectl:1.20.9 as kubectl
FROM alpine/helm:3.1.1 as helm

# Non-root user with sudo access
FROM python:3.8.10-alpine as build
COPY --from=base /usr/local/lib/python3.8/site-packages/ /usr/local/lib/python3.8/site-packages/
COPY --from=base /usr/local/bin/ /usr/local/bin/
COPY --from=kubectl /opt/bitnami/kubectl/bin/kubectl /usr/local/bin/
COPY --from=helm /usr/bin/helm /usr/local/bin/

RUN apk add --update --no-cache \
    sudo \
    bash \
    postgresql-client \
    libpq \
    jpeg-dev \ 
    openjpeg-dev \
    libpng-dev


# Set working directory
WORKDIR /app
COPY . /app/
ARG USER=stackn
RUN adduser -D $USER \
        && echo "$USER ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/$USER \
        && chmod 0440 /etc/sudoers.d/$USER \
        && if [ ! -d "/app/media" ]; then mkdir -p /app/media; fi \ 
        && if [ ! -d "/app/charts/values" ]; then mkdir -p /app/charts/values; fi \
        && if [ ! -d "/app/sent_emails" ]; then mkdir -p /app/sent_emails; fi \
        && chown -R $USER /app/fixtures /app/media /app/charts /app/sent_emails /app/static \
        && chgrp -R $USER /app/fixtures /app/media /app/charts /app/sent_emails /app/static
        
USER $USER
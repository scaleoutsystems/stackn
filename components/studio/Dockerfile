FROM python:3.6 as pybuild1
#-alpine
LABEL maintainer="morgan@scaleoutsystems.com"
#RUN apk update
#RUN apk add musl-dev postgresql-dev gcc python3-dev linux-headers
RUN mkdir /app
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt



RUN apt update
RUN apt install -y curl
RUN curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3
RUN chmod 700 get_helm.sh
RUN ./get_helm.sh
# ENV VERSION="3.0.2"
# ENV BASE_URL="https://get.helm.sh"
# ENV TAR_FILE="helm-v${VERSION}-linux-amd64.tar.gz"
# RUN apt update
# RUN apt install curl ca-certificates wget -y && \
#     curl -L ${BASE_URL}/${TAR_FILE} |tar xvz && \
#     mv linux-amd64/helm /usr/bin/helm && \
#     chmod +x /usr/bin/helm && \
#     rm -rf linux-amd64 && \
#     apt remove curl -y && \
#     rm -f /var/cache/apk/*



FROM pybuild1

COPY . /app/

WORKDIR /app

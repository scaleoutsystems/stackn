FROM python:3.8.10 as pybuild1
LABEL maintainer="matteo@scaleoutsystems.com"

RUN mkdir /app
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

RUN apt update
RUN apt install -y curl vim
RUN curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3
RUN chmod 700 get_helm.sh
RUN ./get_helm.sh

RUN apt update && apt install -y apt-transport-https gnupg2 curl
RUN curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
RUN echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | tee -a /etc/apt/sources.list.d/kubernetes.list
RUN apt update
RUN apt install -y kubectl

FROM pybuild1

COPY . /app/
WORKDIR /app

# To be used in production - Commented out for local dev
# Add a new user "mark" with user id 1818
#RUN useradd -s /bin/bash -u 1818 stackn
# Provide sudo privileges to this user
#RUN usermod -aG sudo stackn
# Swith to a specific user
#USER stackn
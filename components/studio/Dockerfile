FROM python:3.8.10 as pybuild1
LABEL maintainer="fredrik@scaleoutsystems.com"

# Non-root user with sudo access
ARG USERNAME=stackn
RUN useradd -s /bin/bash $USERNAME
# Provide root privileges to this user
RUN usermod -aG sudo $USERNAME
RUN usermod -aG root $USERNAME

# Install stackn pip deps
RUN mkdir /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Install apt deps
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

# Set working directory
COPY . /app/
RUN chown -R stackn /app/
WORKDIR /app

USER $USERNAME

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog

FROM continuumio/miniconda:4.7.12

# Non-root user with sudo access
ARG USERNAME=default
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Conda
ARG CONDA_ENV_NAME="default"

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Install apt deps
RUN apt-get --allow-releaseinfo-change update \
  && apt-get -y install --no-install-recommends \
  apt-utils \
  dialog 2>&1 \
  #
  # More apt deps
  && apt-get install -y --no-install-recommends \
  sudo \
  snapd \
  ca-certificates \
  wget \
  curl \
  git \
  vim \
  #
  # Install microk8s via snap
  && snap install microk8s --classic --channel=1.21 \
  # Install docker binaries
  && curl -L https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz | tar xvz docker/docker \
  && cp docker/docker /usr/local/bin \
  && rm -R docker \
  && curl -L https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose \
  && chmod +x /usr/local/bin/docker-compose \
  #
  # Create a non-root user to use if preferred
  && groupadd --gid $USER_GID $USERNAME \
  && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME \
  && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
  && chmod 0440 /etc/sudoers.d/$USERNAME \
  #
  # Add current non-root user to the group and gain access to the .kube caching directory
  && sudo usermod -a -G microk8s $USER \
  && sudo chown -f -R $USER ~/.kube \
  && newgrp microk8s \
  #
  # Cleanup
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/*
 

# Setup default environment
COPY environment.yaml /tmp/environment.yaml
RUN conda env create -f /tmp/environment.yaml \
  && rm /tmp/environment.yaml \
  && chown default /opt/conda/envs/$CONDA_ENV_NAME

# Setup microk8s
RUN microk8s status --wait-ready \
  && microk8s.enable dns rbac ingress storage \
  && microk8s config >> ~/.kube/config 

# Init conda for non-root user
USER $USERNAME
RUN conda init bash \
  && conda config --set auto_activate_base false \
  && echo "conda activate $CONDA_ENV_NAME" >> ~/.bashrc

# Set working directory
WORKDIR /home/$USERNAME

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog
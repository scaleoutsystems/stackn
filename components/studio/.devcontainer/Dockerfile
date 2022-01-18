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
  ca-certificates \
  wget \
  curl \
  git \
  vim \
  #
  # Install docker binary
  && curl -L https://download.docker.com/linux/static/stable/x86_64/docker-19.03.9.tgz | tar xvz docker/docker \
  && cp docker/docker /usr/local/bin \
  && rm -R docker \
  #
  # Create a non-root user to use if preferred
  && groupadd --gid $USER_GID $USERNAME \
  && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME \
  && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
  && chmod 0440 /etc/sudoers.d/$USERNAME \
  #
  # Cleanup
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/*

# Setup default environment
COPY environment.yaml /tmp/environment.yaml
RUN conda env create -f /tmp/environment.yaml \
  && rm /tmp/environment.yaml \
  && conda run -n $CONDA_ENV_NAME python -m ipykernel install --name $CONDA_ENV_NAME \
  && chown default /opt/conda/envs/$CONDA_ENV_NAME

# Init conda for non-root user
USER $USERNAME
RUN conda init bash \
  && conda config --set auto_activate_base false \
  && echo "conda activate $CONDA_ENV_NAME" >> ~/.bashrc

# Set working directory
WORKDIR /home/$USERNAME

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog
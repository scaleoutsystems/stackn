FROM jupyter/minimal-notebook:python-3.8.8
USER root
RUN /bin/bash -c "apt update"
RUN /bin/bash -c "apt install curl -y"
COPY . /home/jovyan/cli
RUN chown jovyan /home/jovyan/cli
USER $NB_UID
RUN pip install mlflow boto3
RUN pip uninstall minio -y
RUN pip install minio==7.0.2

RUN pip install /home/jovyan/cli/
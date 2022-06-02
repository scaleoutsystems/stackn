FROM jupyter/minimal-notebook:python-3.8.8
USER root
RUN /bin/bash -c "apt update"
RUN /bin/bash -c "apt install curl -y"
USER $NB_UID
COPY . /home/jovyan/stackn
RUN pip install mlflow boto3
RUN pip uninstall minio -y
RUN pip install minio==7.0.2

RUN pip install /home/jovyan/stackn/
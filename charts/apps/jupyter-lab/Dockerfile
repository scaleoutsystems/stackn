FROM jupyter/minimal-notebook:python-3.8.8
USER root
RUN /bin/bash -c "apt update"
RUN /bin/bash -c "apt install curl -y"
COPY examples /home/jovyan/work/examples
RUN chown -R jovyan /home/jovyan/work/examples
USER $NB_UID

RUN python -m pip install --upgrade pip
RUN pip install mlflow boto3
RUN pip uninstall minio -y
RUN pip install minio==7.0.2

RUN pip install git+https://github.com/scaleoutsystems/studio-cli.git@195f860d5f8bf9c1e06897f9d4eadba4fc72d651
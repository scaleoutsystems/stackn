FROM python:3.8-slim-buster
COPY requirements.txt requirements.txt
RUN /bin/bash -c "pip install -r requirements.txt"
RUN /bin/bash -c "apt update"
RUN /bin/bash -c "apt install curl -y"
RUN /bin/bash -c "curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3"
RUN /bin/bash -c "chmod 700 get_helm.sh"
RUN /bin/bash -c "./get_helm.sh"
RUN /bin/bash -c "curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"
RUN /bin/bash -c "chmod +x ./kubectl"
RUN /bin/bash -c "mv kubectl /usr/local/bin/kubectl"
COPY monitor/main.py main.py
CMD python main.py
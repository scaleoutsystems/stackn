{
    "name": "Scaleout STACKn",
    "dockerFile": "Dockerfile",
    "context": "..",
    "remoteUser": "default",
    // when connecting to a remote host
    //"workspaceFolder": "/stack/components/studio",
    //"workspaceMount": "source=/home/carmat/scaleout/stackn/,target=/stackn,type=bind,consistency=default",
    "extensions": [
        "ms-python.python",
        "batisteo.vscode-django",
        "ms-azuretools.vscode-docker",
        "exiasr.hadolint",
        "redhat.vscode-yaml"
    ],

    "mounts": [
        "source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind,consistency=default",
    ],

    "settings": {
        "terminal.integrated.shell.linux": "/bin/bash"
    },
    
    // when connecting to a remote host
    //"runArgs": ["--net=host"],

    "forwardPorts": [8080]
  }
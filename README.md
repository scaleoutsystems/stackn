
# Studio

## Important

This is a private repository and some django app dependencies (studio-user, studio-control etc) are also private. To build studio locally you need to have ssh authentication enabled for Github.
I recommend you add it to your ssh-agent. App dependencies will be installed via pip git+ssh.

## (Quick start) Deploy Studio via Helm


Change `global.postgresql.storageClass` for your particular cluster.

```bash
$ git clone https://github.com/scaleoutsystems/studio-deploy-charts
$ cd studio-deploy-charts
```
Deploy the chart
```bash
$ helm install --set global.postgresql.storageClass=microk8s-hostpath \
  stackn .
```
Once all services are up and running, navigate to http://studio.127.0.0.1.nip.io in your browser.




## Deploy Studio for local development with Docker Compose
Observe that you still need a kubernetes cluster to deploy resources within Studio. However, for local development of the Django project, we recommend deploying with docker compose.

1. Clone this repository locally:
```
$ git clone https://github.com/scaleoutsystems/studio.git
```

2. Add your cluster config and modify settings.py

At root add file:
- `cluster.conf`
  - add your kubernetes cluster config to this file by e.g running: `$ cat ~/.kube/config > ./cluster.conf`
- `studio/settings.py`
  - The settings file for the Django project. The only setting that is required to change is AUTH_DOMAIN, set this to be your local IP (not localhost). By default the studio URL will be http://studio.127.0.0.1.nip.io:8080
  
  Obs that certain features will not work if using localhost since studio apps depends on an external ingress controller. Therefore, it can be useful to use a wildcard dns such as [nip.io](http://nip.io). For example, if your local IP is 192.168.1.10 then the `<your-domain>` field becomes `192.168.1.10.nip.io`.

3. Build image

Since we are dealing with private repos, we need to mount one or several ssh keys to the docker build. Luckily Docker BuildKit has this feature but unfortunately docker compose does not. Therefore we need to build studio first with docker build:

```
$ DOCKER_BUILDKIT=1 docker build -t studio:develop . --ssh=default
```
This assumes you have the correct ssh key in your ssh-agent. If you like to give a specific key replace default with the path to your key. 

3. Finally, fire up Studio with compose:
```
$ docker-compose up -d
```

## Devcontainer

Studio comes with a devcontainer for VS Code. Useful for automated linting, formatting and sorting imports. 

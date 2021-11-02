# Dev

## Deployment

For deployment of STACKn, see the [installation guide](/install).

## Github

Clone the STACKn and Charts repositories:
```
git clone https://github.com/scaleoutsystems/stackn.git
git clone https://github.com/scaleoutsystems/charts.git
```
In both repositories, check out the ``develop`` branch.

We use Gitflow: https://datasift.github.io/gitflow/IntroducingGitFlow.html 

## STACKn CLI

Install setup tools (if not already installed):
```
sudo apt install python-setuptools
```

Setup and install the CLI:
```
cd stackn/cli
sudo python3 setup.py install
```
Run `stackn setup --insecure` and point it to your deployment as follows:

```
Name: local
Keycloak host: https://keycloak.<your-local-ip>.nip.io
Studio host: https://studio.<your-local-ip>.nip.io
Username: user@email.com
Password: ***********
```
**This assumes that you already have a deployment of STACKn, and that you have a user setup in that deployment**. This will not create a new user. If you have a valid SSL certificate, you won't have to use the ``--insecure`` option.

## Telepresence

First check how to [install telepresence](https://www.telepresence.io/reference/install)

For local development of STACKn, you can replace the studio pod with a proxy that points to a local container. First build the Studio container:
```
cd stackn/components/studio
docker build -t scaleoutsystems/studio_local:latest .
```

then run telepresence command as follows:

```
telepresence --swap-deployment stackn-studio --expose 8080 --docker-run --rm -t -v $(pwd):/app studio_local:latest scripts/run_web.sh
```

The same can be done with the Chart Controller:

```
cd stackn/components/chart-controller
docker build -t scaleoutsystems/chart-controller-local:latest .
```

then run telepresence command as follows:

```
telepresence --swap-deployment stackn-chart-controller --expose 80 --docker-run --rm -t -e DEBUG=true -v $(pwd):/app -v /path/to/charts-repo/ scaleout:/app/charts/scaleout chart-controller-local:latest
```

In the previous command above, make sure to replace `/path/to/charts-repo` with your path to the charts. For instance, if the charts have been cloned into `/home/john/charts`, then the path should be `/home/john/charts/scaleout`.

Using telepresence in this way allows local changes to be reflected immediately in the deployment, even if it is a remote deployment.

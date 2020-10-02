# Dev

## Deployment

For deployment of STACKn, see [[...]]...

## Github

Clone the STACKn and Charts repositories:
```
git clone https://github.com/scaleoutsystems/stackn.git
git clone https://github.com/scaleoutsystems/charts
```
In both repositories, check out the ``develop`` branch.

We use Gitflow:  

## STACKn CLI

Setup and install the CLI:
```
cd stackn/cli
python3 setup.py install
```
Run ``stackn setup`` and point to your deployment:
```
Name: local
Keycloak host: https://keycloak.192.168.64.2.nip.io
Studio host: https://studio.192.168.64.2.nip.io
Username: stefan@scaleoutsystems.com
Password:
```
This assumes that you already have a deployment of STACKn, and that you have a user setup in that deployment. This will not create a new user.

## Telepresence

Install: https://www.telepresence.io/reference/install

For local development of STACKn, you can replace the studio pod with a proxy that points to a local container.

First build the Studio container:
```
cd stackn/components/studio
docker build -t scaleoutsystems/studio_local:latest .
```
```
telepresence --swap-deployment stackn-studio --expose 8080 --docker-run --rm -t -v $(pwd):/app studio_local:latest scripts/run_web.sh 
```

The same can be done with the Chart Controller:
```
cd stackn/components/chart-controller
docker build -t scaleoutsystems/chart-controller-local:latest .
```
```
telepresence --swap-deployment stackn-chart-controller --expose 80 --docker-run --rm -t -e DEBUG=true -v $(pwd):/app -v /path/to/charts-repo/ scaleout:/app/charts/scaleout chart-controller-local:latest
```
Above, replace /path/to/charts-repo with the path to the charts. For instance, if the charts have been cloned into /Users/stefan/charts, then the path should be /Users/stefan/charts/scaleout.

Using telepresence in this way allows local changes to be reflected immediately in the deployment, even if it is a remote deployment.







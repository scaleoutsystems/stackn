![alt text](https://thumb.tildacdn.com/tild3162-6435-4365-a230-656137616436/-/resize/560x/-/format/webp/stacknlogo3.png)

* [What is STACKn?](#what-is-stackn)
* [Setup a local deployment](#setup-a-local-deployment)
* [Where is STACKn used?](#where-is-stackn-used)
* [Maintainers](#maintainers)

# What is STACKn?

STACKn is a machine learning platform that lets data scientist collaborate on projects where they can share datasets, work in various development environments, and deploy and serve trained models and analytics apps without worrying about DevOps.

<p align="center">
  <img src="images/stackn_diagram.png" width="100%" title="hover text">
</p>
<p align="center">
  <img src="images/stackn_serve_overview.png" width="100%" title="hover text">
</p>


With an intuitive web UI, users can create private or shared projects in which various data science applications can be deployed, such as
- Dataset: project storage volumes, object stores, and databases for storing and sharing datasets.
- Environments and apps: Jupyter notebooks, VSCode, MLFlow etc. for experimentation and training models with pre-configured data science environments.
- STACKn Models: enables trained models to be deployed and served using tools such as Tensorflow Serving, PyTorch Serve and MLFlow Serve, which in turn enables deployment of analytics apps and custom UIs using served model endpoints (Dash, Flask etc).     

STACKn has been designed to be highly customizable (but comes packaged with the most widely used applications) and cloud agnostic.  STACKn deployments can be configured on any infrastructure that implements the Kubernetes API, and is packaged using Helm charts.

<br />
<br />

# Setup a local deployment
This deployment is for quick testing on Debian/Ubuntu and will not require any TLS certificates. For a production deployment, please see the [documentation](https://scaleoutsystems.github.io/stackn/#/?id=setup).
<br />

## Setup single-node microk8s

1. Install microk8s

```bash
sudo snap install microk8s --classic
```
2. Add user to microk8s group and give permissions to the k8s config folder

```
sudo usermod -a -G microk8s $USER
sudo chown -f -R $USER ~/.kube
newgrp microk8s
```
3. Enable extensions
```
microk8s.enable dns rbac ingress storage
```
4. If kubectl is installed on host add cluster config to kubectl config
```
microk8s config >> ~/.kube/config
```
5. Finally, install the latest version of Helm since microk8s is usually not packaged with the latest Helm version.
**Follow the instructions** [here](https://helm.sh/docs/intro/install/#from-apt-debianubuntu)

## Install STACKn for Local Development with Docker-Compose

1. Clone this repository locally:
```
$ git clone https://github.com/scaleoutsystems/stackn.git
```

2. Navigate to the directory “components/studio“:
```
$ cd stackn/components/studio
```
At this directory there are two files that need to be quickly modified before running the command `docker-compose up`:
- `cluster.conf`
  - update this file with your kubernetes cluster config by running: `$ microk8s config > ./cluster.conf`
- `studio/settings.py`
  - The settings file for the Django project. Update this file by searching and replacing **all** occurrences of `<your-domain>` with your local IP or localhost domain. Obs that certain features will not work if using localhost since stackn apps depends on an external ingress controller. Therefore, it can be useful to use a wildcard dns such as [nip.io](http://nip.io). For example, if your local IP is 192.168.1.10 then the `<your-domain>` field becomes `192.168.1.10.nip.io`.


**Note:** We have created a quite basic shell utility script that takes care of the above manual changes. You can find it under the same directory (i.e. `stackn/components/studio`) and it is called [`init.sh`](https://github.com/scaleoutsystems/charts/blob/release/v0.6.0/scaleout/stackn/values-utility-script.sh). 

3. Finally, fire up STACKn with the following simple command:
```
$ docker-compose up
```
**Note:** in the `docker-compose.yaml` file, it is important to know and be aware that there exists flag for the studio container which default value is:
- `INIT=true`

This flag is used by the studio container when starting the web server with the script [`run_web.sh`](https://github.com/scaleoutsystems/stackn/blob/release/v0.6.0-1/components/studio/scripts/run_web.sh).

The `INIT` flag tells the studio container whether the initial database migrations, fixtures and admin user should be created. This means that such flag should be set to `true` whenever a fresh instance/deployment of STACKn is needed.


## Start using STACKn
Open studio in your browser (for example `studio.192.168.1.10.nip.io:8080`), register a new user with the "Sign up" button and create a new project. Here are [tutorials](https://github.com/scaleoutsystems/examples/tree/main/tutorials/studio) to get you started! Happy STACKning!  
<br />
<br />
# Production ready deployment
Please contact info@scaleoutsystems.com or reach out to the maintainers! 
# Where is STACKn used?
STACKn is used in various places, an example include [SciLifeLab Data Center](https://www.scilifelab.se/data). For a live view of their deployment visit [Scilifelab Serve](https://serve.scilifelab.se/).
<br />
<br />
# Maintainers
**Scaleout Systems AB** is the main contributing organization behind this project.
- Morgan Ekmefjord
- Fredrik Wrede

## Software provided "as is"
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## License
> See [LICENSE](LICENSE) for details.

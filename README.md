![alt text](https://thumb.tildacdn.com/tild3162-6435-4365-a230-656137616436/-/resize/560x/-/format/webp/stacknlogo3.png)

* [What is STACKn?](#what-is-stackn)
* [Setup local deployment](#setup-local-deployment)
* [Where is STACKn used?](#where-is-stackn-used)
* [Maintainers](#maintainers)

# What is STACKn?

STACKn is a machine learning platform that lets data scientist collaborate on projects where they can share datasets, work in various development environments, and deploy and serve trained models and analytics apps without worrying about DevOps.

<p align="center">
  <img src="docs/images/STACKn_overview.svg" width="100%" title="hover text">
</p>
<p align="center">
  <img src="docs/images/stackn_serve_overview.png" width="100%" title="hover text">
</p>



With an intuitive web UI, users can create private or shared projects in which various data science applications can be deployed, such as 
- Data store: project storage volumes, object stores, and databases for storing and sharing datasets.
- Development: Jupyter notebooks, VSCode, MLFlow etc. for experimentation and training models with pre-configured data science environments.
- STACKn Models: enables trained models to be deployed and served in production using tools such as Tensorflow Serving, TorchServe and MLFlow. 
- STACKn Apps: enables deployment of analytics apps and custom UIs usign served model endpoints (Dash, Flask etc)     

STACKn has been designed to be highly customizible (but comes packaged with the most widely used applications) and cloud agnostic.  STACKn deployments can be configured on any infrastructure that implements the Kubernetes API, and is packaged using Helm charts.

STACKn also integrates [FEDn](https://github.com/scaleoutsystems/fedn), a framework for federated machine learning which enables collaborative projects between stakeholders where data cannot be shared due to private, regulatory or practical reasons.   
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
2. Add user to microk8s group

```
sudo usermod -a -G microk8s $USER
```
3. Enable extensions
```
microk8s.enable dns rbac ingress storage
```
4. If kubectl is installed on host add cluster config to kubectl config
```
sudo chown -f -R $USER ~/.kube
microk8s config >> ~/.kube/config
```
5. Finally, install Helm since microk8s is usually not packaged with the latest Helm version.
**Follow the instructions** [here](https://helm.sh/docs/intro/install/#from-apt-debianubuntu)

## Install STACKn

1. Clone  Helm chart repo for STACKn
```
git clone https://github.com/scaleoutsystems/charts.git
```
2. A template file for values.yaml can be found in “charts/scaleout/stackn”
Follow the instructions in this file to set required values:

- StorageClass for microk8s is “microk8s-hostpath”
- For the domain one can use a wildcard dns such as [nip.io](http://nip.io)
- Set oidc.verify = false, this will enable insecure options (without certificates)
- Set global passwords as desired, if these are left blank passwords will be generated

3. After the values.yaml is set install STACKn via helm, this will take several minutes:
```
helm install stackn charts/scaleout/stackn -f values.yaml
```

4. Go to studio in your browser:
```
https://studio.\<your-domain\>
```
5. Register a new user. Press "sign in"  

6. Go to django admin page:
```
https://studio.\<your-domain\>/admin
```
- Sign in with the superuser which was set in helm values (\<global\>.studio.superUser and \<global\>.studio.superUserPassword). If these values were omitted, the password can be found in the Secret "stackn" and superUser is by default "admin".

- Go to "Users" tab and click on the user you created earlier.

- Give the user all permission (admin, staff), then “save”.

 ## Install default apps and project templates

1.  Clone this repository
```
git clone git@github.com:scaleoutsystems/stackn.git
```
2. Install STACKn CLI
```
cd stackn/cli
sudo python3 setup.py install
```
3. Login with the user (which you created in studio)
```
stackn login -u <user-email> -p <password> --insecure --url studio.<your-domain>
```

4. Install the project templates.

```
cd ../../projecttemplates/default
stackn create projecttemplate --insecure
cd ../fedn-mnist/
stackn create projecttemplate --insecure
```
5 . Install apps
```
cd ../../apps
stackn create apps --insecure
```
## Start using STACKn
Open studio in your browser and create a new project. Here are [tutorials](https://github.com/scaleoutsystems/examples/tree/main/tutorials/studio) to get you started! Happy STACKning!  
<br />
<br />
# Where is STACKn used?
STACKn is used in various places, examples include [SciLifeLab Data Center](https://www.scilifelab.se/data) and within the EU-funded project [EOSC-Nordics](https://www.eosc-nordic.eu/).
<br />
<br />
# Maintainers
**Scaleout Systems AB** is the main contributing organization behind this project.
- Morgan Ekmefjord
- Fredrik Wrede
- Matteo Carone

## Software provided "as is"
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## License
> See [LICENSE](LICENSE) for details.

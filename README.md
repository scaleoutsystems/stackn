<a href="#what-is-stackn">What is STACKn</a><br>
<a href="#why-use-stackn">Why use STACKn</a><br>
<a href="#core-features">Core features</a><br>
<a href="#setup">Setup</a>

# What is STACKn?

STACKn is an open source collaborative ML platform. 

We aim to provide organizations and institutions with a complete end-to-end toolbox solution evolved by community feedback and adoption.

# Why use STACKn?
The aim of the STACKn solution is to provide an end-to-end solution for working on collaborative machine learning projects. With a vendor agnostic approach, no framework is preselected and it is entirely up to the users to select their preferred frameworks. 

STACKn is cloud-native and can be deployed on any solution that implements the Kubernetes api. 

# Core features

## Custom Resource management
- Ability to lifecycle control resources. STACKn provides model, dataset, files and project lifecycle management, including user management.

## Model Management
- Ability to track models from cradle to grave with version control, inference auto scaling and control as well as audit trails and scheduled rollouts and/or decommissions. 

## Platform support
- Deploy anywhere where there is a Kubernetes compliant API.

## Integration and customization
- The STACKn front end is composed of modules on a plugin architecture. The versatility enables composeability and  extendability of multiple services together for consumption by the end user. 
- On the backend side Helm charts can easily be extended to include additional services with the inclusion of additional resources to the Helm chart. 
 - A third way to extend resources includes complementing existing bundling with additional Helm charts with bundled resources to allow for custom resources to be deployed and managed either by the chart controller or by manual deployment. 

## Components
STACKn is a composition of multiple required components. The overview can give you a high level introduction to the project and its components.
For additional details please see the technical documentation.

# Setup
## Getting started
This guide lets you quickly get started with STACKn.

1. Check prerequisites
2. Create an SSL certificate
3. Download charts
4. Install STACKn
5. Setup a user
<!-- 5. Create a project -->

### 1. Check prerequisites

- Ensure you have a Kubernetes compliant cluster.
- Your user must have a KUBECONFIG in env configured such that you can access kubectl.
- Helm 3 client installed.
- You need a domain name with a wildcard SSL certificate. If your domain is your-domain.com, you will need a certificate for *.your-domain.com and *.studio.your-domain.com.

#### Kubernetes prerequisites
Your kubernetes setup is expected to have (unless you configure other options):
- Working Ingress controller (ingress-nginx)
- Working Dynamic Storage Provider.
To configure STACKn you must know your storage class name and storage provisioner.

#### Kubernetes configuration
- Setup a desired namespace (or default)
- Setup a service account (or rolebind to admin)
Ensure your service account user has a rolebinding to administrator permissions for deployment.
```bash
cat <<EOF | kubectl apply -f - 
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: admin
  namespace: default
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: admin
subjects:
- kind: ServiceAccount
  name: default
  namespace: default
EOF
```

As we are using fusemounting for some of the s3 overlay mounts to allow for easy s3 access through filesystem you are required to configure so pods allow privileged mode.
If you don't want this feature you can remove this by configuration.

Also if you intend to deploy lab sessions that will utilize hardware capabilities such as GPU, make sure the service account used or configured for the services have the right permissions. 

For example, if you are deploying to microk8s you are required to allow for privilege escalation for docker with `--allow-privileged=true` in `kube-apiserver`.

### 2. Create an SSL certificate

You need a domain name with a wildcard SSL certificate. If your domain is your-domain.com, you will need a certificate for *.your-domain.com and *.studio.your-domain.com. Assuming that your certificate is fullchain.pem and your private key privkey.pem, you can create a secret `prod-ingress` containing the certificate with the command:
```
 kubectl create secret tls prod-ingress --cert fullchain.pem --key privkey.pem
```
An alternative is to deploy STACKn without a certificate, but you will then receive warnings from your browser, and the command-line tool will not work properly.

### 3. Download charts
Navigate to the official chart repository and either download or clone the repository. 

> https://github.com/scaleoutsystems/charts

The ability to add helm chart as a source will be configured soon.

The chart for STACKn is in `charts/scaleout/stackn`.

### 4. Install STACKn
<!-- Copy the example file best matching your intended deployment. There exist examples for some of the most common scenarios like local deployments on various light weight workstation solutions as well as remote hosted deployment templates.  -->

Copy `charts/scaleout/stackn/values.yaml` and make appropriate edits. For more information on how to configure the deployment, see  https://github.com/scaleoutsystems/charts/tree/master/scaleout/stackn. Some of the values are mandatory to update for a working deployment, specifically:

`your-domain.com` should be replaced with your actual domain name everywhere.

`cluster_config` should be updated with the config file for your cluster. You need to have admin access to the namespace in which STACKn is to be deployed.

You might have to update `storageClassName`, `storageClass`, and `namespace`, depending on your cluster setup.

Assuming that your configuration file is `testdeploy/values.yaml`, you can now deploy STACKn with
```bash
$ helm install stackn charts/scaleout/stackn -f testdeploy/values.yaml
```
You can lint or check the deployment with the flags —dry-run —debug.

Make sure to assign the chart to the right namespace with —namespace yournamespace (when deploying to the default namespace this can be omitted.)

### 5. Setup a user

You will need to create a user to login into Studio. Click the login button in the lower left corner, and click register. By default, Keycloak is configured not to require email verification, but this can be changed by logging into the Keycloak admin console and updating the STACKn realm login settings.

To access the admin page of Studio, you will need to create a Django user with admin rights. First find the pod name to the Studio deployment:
```bash
$ kubectl get pods -n yournamespace
```
and get the pod id that correspond to the studio pod running. Replace `pod-Id` in the command below.
```bash
$ kubectl exec -it pod-Id python manage.py createsuperuser
```

### Additional - Upgrading STACKn

Similar to how you install a chart you may also upgrade a chart.

An example of how to upgrade STACKn with a values file as per above:
```bash
$ helm upgrade stackn scaleout/stackn --values=testdeploy/values.yaml --debug --dry-run
```
To perform the upgrade
```bash
$ helm upgrade stackn scaleout/stackn --values=testdeploy/values.yaml
```

# Tutorial projects

## Digits MNIST Project
https://github.com/scaleoutsystems/digits-example-project

## AML Example project
https://github.com/scaleoutsystems/aml-example-project


Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md).

# Where is STACKn used?
STACKn is used in various places, examples include [SciLifeLab Data Center](https://www.scilifelab.se/data) and within the EU-funded project [EOSC-Nordics](https://www.eosc-nordic.eu/).

# Maintainers
**Scaleout Systems AB** is the main contributing organization behind this project.
- morganekmefjord
- dstoyanova
- stefanhellander

## Software provided "as is"
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## License
> See [LICENSE](LICENCE.md) for details.

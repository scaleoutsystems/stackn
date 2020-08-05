

# What is STACKn?

STACKn is an open source collaborative AI platform. 

We aim to provide organizations and institutions with a complete end-to-end toolbox solution evolved by community feedback and adoption.

# Why use STACKn?
The STACKn solution provides an end-to-end solution for working on collaborative machine learning projects. With a vendor agnostic approach, no framework is preselected and it is entirely up to the users to select their preferred frameworks. 

Deploying is a breeze with a cloud-native, vendor-agnostic approach, able to deploy on any solution that provides and implements the kubernetes api. 

# Core features

## Custom Resource management
- Ability to lifecycle control resources. STACKn provides model, dataset, files and project lifecycle management, including user management.

## Model Management
- Ability to track models from cradle to grave with version control, inference auto scaling and control as well as audit trails and scheduled rollouts and/or decommissions. 

## Platform support
- Deploy anywhere where there is a Kubernetes compliant API.

## Integration and customization
- STACKn front end is composed of modules on a plugin architecture. The versatility enables composeability and  extendability of multiple services together for consumption by the end user. 
- On the backend side Helm charts can easily be extended to include additional services with the inclusion of additional resources to the Helm chart. 
 - A third way to extend resources includes complementing existing bundling with additional Helm charts with bundled resources to allow for custom resources to be deployed and managed either by the chart controller or by manual deployment. 

## Components
STACKn is a composition of multiple required components. The overview can give you a high level introduction to the project and its components.
For additional details please see the technical documentation.

# Setup
## Getting started
This guide lets you quickly get started with STACKn. If you are already familiar with installing Helm charts you may skip ahead to Setup a user.

1. Check prerequisites
2. Download charts
3. Install STACKn
4. Setup a user
5. Create a project

### 1. Check prerequisites

- Ensure you have a Kubernetes compliant cluster.
- Your user must have a KUBECONFIG in env configured such that you can access kubectl.
- Helm 3 client installed.

#### Kubernetes prereqs
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
- Utilize hardware capabilities?
As we are using fusemounting for some of the s3 overlay mounts to allow for easy s3 access through filesystem you are required to configure so pods allow privileged mode.
If you don't want this feature you can remove this by configuration.

Also if you intend to deploy labs sessions that will utilize hardware capabilities such as GPU make sure the service account used or configured for the services have the right permissions. 

Example if you are deploying to microk8s you are required to allow for privilege escalation for docker with `--allow-privileged=true` (https://gist.github.com/antonfisher/d4cb83ff204b196058d79f513fd135a6)[reference]

### 2. Download charts
Navigate to the official chart repository and either download the repo or clone the repository to your local device. 

> https://github.com/scaleoutsystems/charts

```bash
$wget https://github.com/scaleoutsystems/charts/archive/master.zip
```
Or 

```bash
$ git clone git@github.com:scaleoutsystems/charts.git
```

Soon the ability to add helm chart as a source will be configured.

### 3. Install STACKn
Copy the example file best matching your intended deployment. There exist examples for Some of the most common scenarios like local deployments on various light weight workstation solutions as well as remote hosted deployment templates. 

```bash
$ cp example/microk8s/values.yaml testdeploy/values.yaml
```
Now edit the configuration file appropriately.

Hint : lint or check deployment with —dry-run —debug flags to ensure correct value replacement. 
```bash
$ helm install stackn /path/to/charts/stackn -f testdeploy/values.yaml
```
Make sure to assign the chart to the right namespace with —namespace yournamespace (when deploying to the default namespace this can be omitted.)

### 4. Setup a user

You will need to create a user to login into Studio. Click the login button in the lower left corner, and click register. By default, Keycloak is configured not to require email verification, but this can be changed by logging into the Keycloak admin console and updating the STACKn realm login settings.

To access the admin page of Studio, you will need to create a Django user with admin rights. First find out the pod name to the studio deployment:
```bash
$ kubectl get pods -n yournamespace
```
and get the pod id that correspond to the studio pod running. Replace the "pod-Id" in the command below.
```bash
$ kubectl exec -it pod-Id python manage.py createsuperuser
```

### Additional - Upgrading STACKn

Similar to how you install a chart you may also upgrade a chart if some parameters have changed.

An example for upgrading STACKn with a values file as per above:
```bash
$ helm upgrade stackn scaleout/stackn --values=testdeploy/values.yaml --debug --dry-run
```
To perform the upgrade
```bash
$ helm upgrade stackn scaleout/stackn --values=testdeploy/values.yaml
```

## Tutorial projects

### Digits MNIST Project
https://github.com/scaleoutsystems/digits-example-project

### AML Example project
https://github.com/scaleoutsystems/aml-example-project


Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md).

## Our main maintainers are
**Scaleout Systems AB** is the main contributing organization behind this project.
- morganekmefjord
- dstoyanova
- stefanhellander


## License
> See [LICENSE](LICENCE.md)

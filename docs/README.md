

# What is STACKn?

STACKn is an open source collaborative AI platform. 

Some solutions exist out there but none with both an open source and an end to end approach. 
We aim to provide organizations and institutions with a complete end to end toolbox solution evolved by community feedback and adoption.

# Why use STACKn?
Stackn solution provides an end to end solution for working on collaborative machine learning projects and assignments. With the vendor agnostic approach no framework is preselected and it is entirely up to the machine learning engineers to select their preferred frameworks. 

Deploying is a breeze with a cloud native vendor agnostic approach able to deploy on any solution that provides and implements the kubernetes api. 

# Core features

## Custom Resource management
- Ability to lifecycle control resources. Out of the box stackn provides model, dataset, files and project lifecycle management including user management 

## Model Management
- Ability to track models from cradle to grave with version control, inference auto scaling and control as well as audit trails and scheduled rollouts and/or decommissions. 

## Platform support
- Deploy anywhere where there is a kubernetes compliant api.

## Integration and customization
- Stackn front end is composed of modules on a plugin architecture. The versatility enables composeability and  extendability of multiple services together for consumption by the end user. 
- On the backend side helm charts can easily be extended to include additional services with the inclusion of additional resources to the helm chart. 
 - A third way to extend resources includes complementing existing bundling with additional helm charts with bundled resources to allow for custom resources to be deployed and managed either by the chart controller or by manual deployment. 

## Components
STACKn is a composition of multiple components required to run the STACKn. The overview can give you a high level introduction to the project and its components.
For additional details please see the technical documentation.

# Setup
## Getting started
This guide lets you quickly get started with STACKn. If you are already familiar with installing helm charts you may skip ahead to Setup a user.

1. Check prerequisites
2. Download charts
3. Install STACKn
4. Setup a user
5. Create a project

### 1. Check prerequisites

- Ensure you have a kubernetes compliant cluster.
- Your user must have a KUBECONFIG in env configured such that you can access kubectl.
- Helm 3 client installed.

#### Kubernetes prereqs
Your kubernetes setup is expected to have (unless you configure other options):
- Working Ingress controller (ingress-nginx)
- Working Dynamic Storage Provider
to configure you must know your storage class name and storage provisioner.

#### Kubernetes configuration
- Setup a desired namespace (or default)
- Setup a service account (or rolebind to admin)
Ensure your service account user have a rolebinding to administrator permissions for deployment.
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
If you dont want this feature you can remove this by configuration.

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
Copy one of the example files most redeeming your intended deployment. There exist examples for Some of the most common scenarios like local deployments on various light weight workstation solutions as well as remote hosted deployment templates. 

Copy the most resembling values.yaml file and name it according to your choice. Make sure to read thoroughly as any malconfiguration will prevent or make for an erroneous deployment. 
```bash
$ cp example/microk8s/values.yaml testdeploy/values.yaml
```
Edit the configuration file appropriately
```bash 
$ vi testdeploy/values.yaml
```
Hint : lint or check deployment with —dry-run —debut flags to ensure correct value replacement. 
```bash
$ helm install stackn 
```
Make sure to assign the chart to the right namespace with —namespace yournamespace

### 4. Setup a user
Either find out the pod name to the studio deployment
```bash
$ kubectl get pods -n yournamespace
```
get the pod id that correspond to the studio pod running. Replace the "pod-Id" in the command below.
```bash
$ kubectl exec -it pod-Id python manage.py createsuperuser
```
Helm chart deployment also allow to pre loaded with seed data on deployment such as initial users. Mole on that can be found in the advanced section. 

### 5. Create a project
1. Navigate to your configured ingress for studio.
2. Login with your newly added credentials.
3. Create a project either blank or by selecting a public repository to import and start with.

### Additional - Upgrading STACKn
Describe how to upgrade stack with the helm chart. Changing different parameters or similar.

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

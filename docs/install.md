# Installing STACKn

## Local Deployment
<br />

### Mac

- Install Helm:

```
brew install helm
```

- Install kubectl:

```
brew install kubectl
```

- Install multipass:

```
brew cask install multipass
```

- Install microk8s:

```
brew install ubuntu/microk8s/microk8s
```

- Start microk8s:

```
microk8s install --cpu 4 --mem 8 --disk 30
```

This starts microk8s with 4 CPUs, 8Gb of RAM, and 30GB of disk space.

- Enable add-ons:

```
microk8s enable dns storage rbac ingress
```

- Clone the Scaleout charts repo:

```
git clone https://github.com/scaleoutsystems/charts.git
cd charts/scaleout/stackn
```

- Create a folder where you can keep configuration files for your deployment:

```
mkdir stackn-local
cd stackn-local
```

Then copy `values.yaml`, which should be lcoated under `charts/scaleout/stackn/`, in your new folder:

```
cp ../values.yaml ./my-values.yaml
```

- You will need to make some edits to this file, but first get your kubeconfig for access to the cluster:

```
microk8s kubectl config view --raw > config
```

- Get the IP address of the VM running microk8s:

```
multipass list
```

- Edit the `config` field by changing the line:

```
server: https://127.0.0.1:16443
```
to
```
server: https://your-ip:16443
```

- Check that everything is working as expected by running for instance:

```
kubectl --kubeconfig config get pod
helm --kubeconfig config list
```

- If you want to make this cluster the default cluster:

```
cp config ~/.kube/config
```

This way you don't have to specify kubeconfig with `kubectl` and `helm`. If you're managing multiple clusters, you can use the `kubectx` tool to be able to conveniently switch between different contexts.


- Now it's time to start editing your `values.yaml` file. Please make sure to follow the instructions that you will find **at the beginning of this file** in order to set some required values, such as:

  - `StorageClass` (for microk8s is “microk8s-hostpath”)

  - Search and replace **all** occurrences of `<your-domain.com>` with your local IP domain. It can be useful to use a wildcard dns such as [nip.io](http://nip.io). For example, if your local IP is 192.168.1.10 then the `<your-domain.com>` field becomes `192.168.1.10.nip.io`

  - If you plan to use a self-signed certificate, then set  `oidc.verify_ssl = false`; this will enable insecure options to be used.

  - Setting passwords are optional, but we recommend setting  `global.studio.superUser` and `global.studio.superUserPassword` since these are required in step 6.,   if these are left blank passwords will be auto generated.

  - Copy your kubernetes cluster config and paste it in the values.yaml under the `cluster_config` field. Your kubernetes config file should be locate under the path `$HOME/.kube`; otherwise if you have followed this tutorial and used microk8s, then run the command:

```
microk8s config
```


- The last step before we can deploy STACKn is to create a self-signed wildcard certificate:

```
cp ../examples/issuer.yaml .
cp ..examples/certificate.yaml .
```

In `certificate.yaml`, replace 127.0.0.1 with your IP. For example, if your local IP is 192.168.1.10 and you are using nip.io as a wildcard DNS, then replace 127.0.0.1 with `192.168.1.10.nip.io`. Once done, install `cert-manager`as follows:

```
kubectl --kubeconfig config create namespace cert-manager
kubectl --kubeconfig config apply --validate=false -f https://github.com/jetstack/cert-manager/releases/download/v0.13.1/cert-manager.yaml
```

Before installing the certificate, make sure that all the pods are up and running:

```
kubectl --kubeconfig config get po -n cert-manager
```

Now:

```
kubectl --kubeconfig config apply -f issuer.yaml
kubectl --kubeconfig config apply -f certificate.yaml
```

And finally, deploy STACKn:

```
helm --kubeconfig config install stackn ../stackn -f my-values.yaml
```

Note that you will need to take extra steps for your browser to accept the self-signed certificate. On Mac:

```
kubectl --kubeconfig config get secret prod-ingress -o jsonpath='{.data.ca\.crt}' | base64 -d > ca.crt
```

Then `open ca.crt`, and add it to `System` in your key-chain. Right-click the entry, select `Get Info`, expand `Trust` and set `When using this certificate` to `Always Trust`.

Once all the pods have started (check with `kubectl --kubeconfig config get po`), you can browse to `Studio` at `studio.your-ip.nip.io`. It could take several minutes to start all the pods.
<br />
<br />

### Linux

- Install Helm:

```
sudo snap install helm --classic
```

- Install kubectl:

```
sudo snap install kubectl --classic
```

- Install microk8s:

```
sudo snap install microk8s --classic
```

- Add user to microk8s group and give permissions to the k8s config folder

```
sudo usermod -a -G microk8s $USER
sudo chown -f -R $USER ~/.kube
newgrp microk8s
```

- Start microk8s:

```
microk8s start
```

- Enable add-ons:

```
sudo microk8s enable dns storage rbac ingress
```

- Clone the Scaleout charts repo:

```
git clone https://github.com/scaleoutsystems/charts.git
cd charts/scaleout/stackn
```

- Create a folder where you can keep configuration files for your deployment:

```
mkdir stackn-local
cd stackn-local
```

- Then copy `value.yaml`, which should be located at `charts/scaleout/stackn`, in your new folder:

```
cp ../value.yaml ./my-values.yaml
```

- Get your config for access to the cluster:

```
microk8s kubectl config view --raw > config
```

- If you want to make this cluster the default cluster:

```
cp config ~/.kube/config
```

This way you don't have to specify kubeconfig with `kubectl` and `helm`. If you're managing multiple clusters, you can use the `kubectx` tool to be able to conveniently switch between different contexts. Now edit `local.yaml`:

- Now it's time to start editing your `values.yaml` file. Please make sure to follow the instructions that you will find **at the beginning of this file** in order to set some required values, such as:

  - `StorageClass` (for microk8s is “microk8s-hostpath”)

  - Search and replace **all** occurrences of `<your-domain.com>` with your local IP domain. It can be useful to use a wildcard dns such as [nip.io](http://nip.io). For example, if your local IP is 192.168.1.10 then the `<your-domain.com>` field becomes `192.168.1.10.nip.io`

  - If you plan to use a self-signed certificate, then set  `oidc.verify_ssl = false`; this will enable insecure options to be used.

  - Setting passwords are optional, but we recommend setting  `global.studio.superUser` and `global.studio.superUserPassword` since these are required in step 6.,   if these are left blank passwords will be auto generated.

  - Copy your kubernetes cluster config and paste it in the values.yaml under the `cluster_config` field. Your kubernetes config file should be locate under the path `$HOME/.kube`; otherwise if you have followed this tutorial and used microk8s, then run the command:

```
microk8s config
```

- And finally, deploy STACKn:

```
helm install stackn ../stackn -f my-values.yaml
```

- Get to see if everything is working fine.

```
kubectl get pods
```

- Once all the pods have started, you can browse to `Studio` at `studio.your-ip.nip.io`. It could take several minutes to start all the pods.
<br />
<br />

### Windows 10

- Install helm for Windows:

```bash
choco install kubernetes-helm
```

You can find instructions how to install Chocolatey [here](https://chocolatey.org/install).

- Install kubectl for Windows:

```bash
choco install kubernetes-cli
```

After that, navigate to the main directory and run:

```bash
mkdir .kube
cd .kube
New-Item config -type file
```

- Install [Microk8s](https://ubuntu.com/tutorials/install-microk8s-on-windows#2-installation).

**Note**: Make sure you to select multipass to be installed together with Microk8s.

- Enable Virtualization in your BIOS:

  - Restart your system
  - Press **DEL** before the OS has loaded
  - Go to **Advanced CPU Settings**
  - Set **SVM** to **Enabled**


- Once restarted, launch a VM as follows:

```bash
microk8s install --cpu 4 --mem 8 --disk 30
```

and install the add-ons:

```bash
microk8s enable dns storage rbac ingress
```

- Create a kubernetes config:

```bash
microk8s kubectl config view --raw > config
multipass list
```

Then, copy the IP address of your VM and edit the config file by changing

```bash
server: https://127.0.0.1:16443
```

to

```bash
server: https://your-ip:16443
```

- Clone the charts repository:

```bash
git clone https://github.com/scaleoutsystems/charts.git
cd charts/scaleout/stackn
```

- Create a folder where you can keep configuration files for your deployment:

```bash
mkdir stackn-local
cd stackn-local
```

- Then copy `value.yaml`, which should be located at `charts/scaleout/stackn`, in your new folder:

```bash
cp ../values.yaml ./my-values.yaml
```

- Now it's time to start editing your `values.yaml` file. Please make sure to follow the instructions that you will find **at the beginning of this file** in order to set some required values, such as:

  - `StorageClass` (for microk8s is “microk8s-hostpath”)

  - Search and replace **all** occurrences of `<your-domain.com>` with your local IP domain. It can be useful to use a wildcard dns such as [nip.io](http://nip.io). For example, if your local IP is 192.168.1.10 then the `<your-domain.com>` field becomes `192.168.1.10.nip.io`

  - If you plan to use a self-signed certificate, then set  `oidc.verify_ssl = false`; this will enable insecure options to be used.

  - Setting passwords are optional, but we recommend setting  `global.studio.superUser` and `global.studio.superUserPassword` since these are required in step 6.,   if these are left blank passwords will be auto generated.

  - Copy your kubernetes cluster config and paste it in the values.yaml under the `cluster_config` field. Your kubernetes config file should be locate under the path `$HOME/.kube`; otherwise if you have followed this tutorial and used microk8s, then run the command:

```
microk8s config
```

- And finally, deploy STACKn:

```bash
helm --kubeconfig config install stackn ../stackn -f my-values.yaml
```

- Verify the deployment

```bash
helm --kubeconfig config list

kubectl --kubeconfig config get pods
```

- Once all the pods have started, you can browse to `Studio` at `studio.your-ip.nip.io`. It could take several minutes to start all the pods.

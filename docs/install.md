# Installing STACKn

## Local Deployment

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
 - Clone the Scaleout charts repo and check out the develop branch:
  ```
  git clone https://github.com/scaleoutsystems/charts.git
  cd charts
  git checkout develop
  cd ..
  ```
 - Create a folder where you can keep configuration files for your deployment:
  ```
  mkdir stackn-local
  cd stackn-local
  ```
  Then copy ``local.yaml`` from ``charts/scaleout/stackn/examples/``:
  ```
  cp ../charts/scaleout/stackn/examples/local.yaml .
  ```
 - You will need to make some edits to this file, but first get your kubeconfig for access to the cluster:
  ```
  microk8s kubectl config view --raw > config
  ```
 - Get the IP address of the VM running microk8s:
  ```
  multipass list
  ```
 - Edit ``config``: Change the line 
  ```
  server: https://127.0.0.1:16443
  to
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
  Now you don't have to specify kubeconfig with ``kubectl`` and ``helm``. If you're managing multiple clusters, you can use the ``kubectx`` tool to be able to conveniently switch between different contexts.
 - Now edit ``local.yaml``:
   - Replace ``cluster_config`` with your config file.
   - Search for 127.0.0.1 and replace with your cluster's IP.
 - The last step before we can deploy STACKn is to create a self-signed wildcard certificate:
  ```
  cp ../charts/scaleout/stackn/examples/issuer.yaml .
  cp ../charts/scaleout/stackn/examples/certificate.yaml .
  ```
  In ``certificate.yaml``, replace 127.0.0.1 with your IP. Install ``cert-manager``:
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
  helm --kubeconfig config install stackn ../charts/scaleout/stackn -f local.yaml
  ```
  Note that you will need to take extra steps for your browser to accept the self-signed certificate. On Mac:
  ```
  kubectl --kubeconfig config get secret prod-ingress -o jsonpath='{.data.ca\.crt}' | base64 -d > ca.crt
  ```
  Then ``open ca.crt``, and add it to ``System`` in your key-chain. Right-click the entry, select ``Get Info``, expand ``Trust`` and set ``When using this certificate`` to ``Always Trust``.

  Once all the pods have started (check with ``kubectl --kubeconfig config get po``), you can browse to ``Studio`` at ``studio.your-ip.nip.io``. It could take up to 10 minutes to start all the pods.
  
  
  
### Linux 

- Installing Helm:
```
sudo snap install helm –classic
```
- Installing kubectl:
```
sudo snap install kubectl –classic
```
- Installing microk8s:
```
sudo snap install microk8s –classic
```
- Start microk8s:
```
microk8s start
```
- Enable add-ons: 
```
sudo microk8s enable dns storage rbac ingress
 ```
- Clone the Scaleout charts repo and check out the develop branch:
```
git clone https://github.com/scaleoutsystems/charts.git -b develop
 ```
- Create a folder where you can keep configuration files for your deployment:
```
mkdir stackn-local
cd stackn-local
 ```
- Then copy local.yaml from charts/scaleout/stackn/examples/:
```
cp ../charts/scaleout/stackn/examples/local.yaml .
```
- Get your config for access to the cluster: 
```
microk8s kubectl config view --raw > config
 ```
- If you want to make this cluster the default cluster: 
```
cp config ~/.kube/config
 ```
Now you don't have to specify kubeconfig with ``kubectl`` and ``helm``. If you're managing multiple clusters, you can use the ``kubectx`` tool to be able to conveniently switch between different contexts. Now edit ``local.yaml``:

- Replace ``cluster_config`` with your config file.
 
- And finally, deploy STACKn:
```
helm install stackn ../charts/scaleout/stackn -f local.yaml
```
- Get to see if everything is working fine.
```
kubectl get pods
```

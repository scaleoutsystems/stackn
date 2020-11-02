# Minimal Model Deployment

If you haven't already installed the STACKn CLI, you can install it with pip:
```
pip install git+https://@github.com/scaleoutsystems/stackn@develop#subdirectory=cli
```


Create a project:
```
stackn create project -n demo
```
Create a directory for your model:
```
mkdir demo-model
cd demo-model
```
Initialize the model with
```
stackn init
```
Create the model and deploy it:
```
stackn create model -n test-model -r minor
stackn create deployment -m test-model -d default-python
```
It will take a minute for the model to deploy. Once it is ready, you can run a prediction:
```
stackn predict -m test-model -v v0.1.0 -i '{"pred":"test"}'
```
Alternatively you can create a lab session:
```
stackn create lab -f large -e default
```
and then you can call the model endpoint from inside a notebook:
```
from scaleout.auth import get_token
import requests
url = 'https://studio.scilifelab.stackn.dev/demo-cbn/serve/demo-model/v010/predict/'
token, config = get_token()
res = requests.post(url, headers={"Authorization": "Token "+token}, json={"pred":"test"})
res.json()
```
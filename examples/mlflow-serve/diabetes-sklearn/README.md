# MLFlow-diabetes-sklearn
This example of using MLFlow to track ML experiments is based on the [sklearn diabetes tutorial](https://github.com/mlflow/mlflow/tree/master/examples/sklearn_elasticnet_diabetes/linux). The example trains an ElesticNet model provided by Sklearn. MLFlow will track hyperparams and the model and add the model to the registry. STACKn model registry will sync with the MLFlow registry, thus creating a model object is not needed by the user. 

From inside a Jupyter lab instance:
## Instructions
- `$ mlflow run .`
- This will run the MLFlow project defined in MLproject.
- Navigate to STACKn UI models tab and make sure the a new model ElasticNet version 1 has been created, alt. in jupyter lab terminal run: `$ stackn get model-obj -t mlflow`
- From the UI click on the link for the MLFlow server. Observe the newly created ecperiment under the "Experiment" tab. Also observe the newly created model (version 1) under the "Models" tab.
- From the STACKn UI navigate to the "Serve" tab. Create a new MLFlow-Serve instance using the newly created model. Once the status has been updated to Running, click on the "Open" link and copy the URL (endpoint) from the browser URL field. If you get a "Bad gateway" error message the MLFlow-Serve service might not yet be ready. If so, try again later.

## Inference requests
- In ./tests/tests is an example of how to send inference request to the service. To run this tests you first need to create conda environment provided in the folder:
- `conda create env -f env_test.yaml`
- Once that is done: `./tests predict --endpoint https://\<release\>.domain/invocations`
- Where the endpoint is the URL you copied from the browser. 


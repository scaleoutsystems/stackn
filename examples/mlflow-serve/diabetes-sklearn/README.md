# MLFlow-diabetes-sklearn
This example of using mlflow to track ML experiments is based on the [sklearn diabetes tutorial](https://github.com/mlflow/mlflow/tree/master/examples/sklearn_elasticnet_diabetes/linux). The example trains an ElesticNet model provided by Sklearn. MLFlow will track hyperparams and the model and add the model to the registry. STACKn model registry will sync with the MLFlow registry. 


## Instructions
- `$ mlflow run .`
- Navigate to STACKn UI models tab and make sure the a new model ElasticNet ver.1 has been created, alt. in jupyter lab terminal run: `$ stackn get model-obj -t mlflow`


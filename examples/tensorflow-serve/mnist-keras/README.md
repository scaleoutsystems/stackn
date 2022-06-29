## MNIST-KERAS Tensorflow Serve Example

based on: https://github.com/scaleoutsystems/fedn/tree/master/examples/mnist-keras

From inside jupyter lab:

## Instructions
- `$ ./build.sh`
- The above script will create a neural network using Tensorflow, save the model and create a STACKn model object using the API. Navigate to the project dashboard and confirm the the model object has been created.
- Create a Tensorflow-serve instance from STACKn UI, copy the endpoint URL: From the project dashboard navigate to the Serve tab and create a Tensorflow-Serve instance using the newly created model object. When status has been updated to "Running", click on the "open" link and copy the URL(endpoint excluding :predict) from the browser URL field.
- From the jupyter lab instance: `$ ./entrypoint predict --endpoint https://\<release\>.domain/v1/models/models`
- Running the above script will send an inference request to the serve endpoint using some test data. 

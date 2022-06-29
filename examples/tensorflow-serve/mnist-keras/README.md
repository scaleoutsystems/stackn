## MNIST-KERAS Tensorflow Serve Example

based on: https://github.com/scaleoutsystems/fedn/tree/master/examples/mnist-keras

From inside jupyter lab:

## Instructions
- `$ ./build.sh`
- Create a Tensorflow-serve instance from STACKn UI, copy the endpoint URL
- `$ ./entrypoint predict --endpoint https://\<release\>.domain/v1/models/models`

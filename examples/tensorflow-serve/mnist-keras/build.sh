#!/bin/bash
#build venv
./init_venv.sh

#download input data and build model
./entrypoint get_data
./entrypoint build_model
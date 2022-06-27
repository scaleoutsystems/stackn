#!/bin/bash
#build venv
./init_venv.sh

#download input data and build model
./entrypoint.py get_data
./entrypoint.py build_model
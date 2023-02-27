#!/bin/bash
set -e

# Init venv
python -m venv .mnist-keras

# Pip deps
.mnist-keras/bin/pip install --upgrade pip
.mnist-keras/bin/pip install git+https://github.com/scaleoutsystems/studio-cli.git@195f860d5f8bf9c1e06897f9d4eadba4fc72d651
.mnist-keras/bin/pip install -r requirements.txt
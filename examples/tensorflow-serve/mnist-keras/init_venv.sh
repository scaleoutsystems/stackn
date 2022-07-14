#!/bin/bash
set -e

# Init venv
python -m venv .mnist-keras

# Pip deps
.mnist-keras/bin/pip install --upgrade pip
cp -r ~/cli/ .
.mnist-keras/bin/pip install ./cli
rm -r cli
.mnist-keras/bin/pip install -r requirements.txt
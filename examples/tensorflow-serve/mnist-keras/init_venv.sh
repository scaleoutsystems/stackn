#!/bin/bash
set -e

# Init venv
python -m venv .mnist-keras

# Pip deps
.mnist-keras/bin/pip install --upgrade pip
cp -r ~/stackn/ .
.mnist-keras/bin/pip install ./stackn
rm -r stackn
.mnist-keras/bin/pip install -r requirements.txt
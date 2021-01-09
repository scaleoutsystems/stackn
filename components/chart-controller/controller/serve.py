import os
from flask import Flask
from flask import request
import json
from controller.controller import Controller
import subprocess

app = Flask(__name__)


@app.route('/')
def index():

    path = os.getcwd()
    c = Controller(path + '/charts')

    args = 'helm list'.split(' ')

    status = subprocess.run(args, cwd=path, capture_output=True)
    return json.dumps({'helm': {'command': args, 'cwd': str(path), 'status': str(status)}})


@app.route('/deploy', methods=['POST'])
def deploy():
    path = os.getcwd()
    c = Controller(path)

    return c.deploy(request.json)

@app.route('/upgrade')
def update():
    path = os.getcwd()
    c = Controller(path)

    return c.deploy(request.args, 'upgrade')


@app.route('/delete', methods=['POST'])
def delete():
    path = os.getcwd()
    c = Controller(path)
    return c.delete(request.json)

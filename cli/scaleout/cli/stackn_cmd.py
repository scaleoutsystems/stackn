import click
from .main import main
import requests
from scaleout.auth import login, get_stackn_config, get_remote_config, get_token
from .helpers import create_table
import os
import random
import string
import json

# @click.option('--daemon',
#               is_flag=True,
#               help=(
#                       "Specify to run in daemon mode."
#               )
#               )

@main.command('setup')
@click.option('--secure/--insecure', default=True)
@click.pass_context
def setup_cmd(ctx, secure):
    login(secure=secure)

@main.command('login')
@click.option('--secure/--insecure', default=True)
@click.pass_context
def login_cmd(ctx, secure):
    stackn_config, load_status = get_stackn_config(secure=secure)
    if not load_status:
        print('Failed to load STACKn config.')
        return

    remote_config, load_status = get_remote_config()
    if remote_config:
        login(deployment=stackn_config['active'],
              keycloak_host=remote_config['keycloak_url'],
              studio_host=remote_config['studio_url'])

@main.command('status')
@click.pass_context
def status_cmd(ctx):
    stackn_config, load_status = get_stackn_config()
    if not load_status:
        print('Failed to load STACKn config.')
    else:
        print('Context: '+stackn_config['active'])
        if 'active_project' in stackn_config:
            print('Project: '+stackn_config['active_project'])
        else:
            print('No active project; create a new project or set an existing project.')

@main.command('predict')
@click.option('-m', '--model', required=True)
@click.option('-v', '--version')
@click.option('-i', '--inp', required=True)
@click.pass_context
def predict_cmd(ctx, model, version, inp):
    client = ctx.obj['CLIENT']
    client.predict(model, inp, version)
    # token, config = get_token()
    # res = requests.post(url,
    #                     headers={"Authorization": "Token "+token},
    #                     json = inp)

@main.command('train')
@click.option('-m', '--model', required=True)
@click.option('-f', '--training-file', required=False, default="src/models/train.py")
@click.pass_context
def train_cmd(ctx, model, training_file):
    current_dir = os.getcwd()
    if os.path.isdir('src/models'):
        if os.path.isfile(training_file):
            #run_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k = 32)) # Randomized id for current run; string of size 32, same as MLflow
            #os.mkdir('mlruns/' + run_id) # Make sub-directory in 'mlruns' for current training run
            #dir_path = os.path.dirname(os.path.realpath(__file__))
            #file_path = os.path.join(dir_path, 'run-structure.tar.gz')
            #import tarfile
            #tf = tarfile.open(file_path)
            #tf.extractall('mlruns/' + run_id)
            client = ctx.obj['CLIENT']
            client.log_training(model, training_file)
            #client.train(training_file, model, version, run_id)
        else:
            print('The file "train.py" does not exist in "src/models". Create it in the directory and include code for model training before running "stackn train" again.')
    else:
        print('No project structure initialized in ' + current_dir + '; navigate to the correct folder or use "stackn init" to initialize a generic project structure in the current directory.')

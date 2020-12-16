import click
from .main import main
import requests
from scaleout.auth import login, get_stackn_config, get_remote_config, get_token
from .helpers import create_table, search_for_model, new_id, Determinant
import os
import random
import string
import json
import uuid
from scaleout.details import get_run_details 

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


# ------------------- Question ---------------------
# Is it a good idea to make it possible to pass --log-off as an argument if the user does not want to log the run to Studio?
# In that case, the model name and code version is not possible to pass to the stackn train command and train.py will run without logging. 
# Not sure if this is a good idea
# --------------------------------------------------
@main.command('train')
@click.option('--log-off', flag_value='log-off', default=False)
@click.option('-m', '--model', prompt=True, cls=Determinant, determinant='log_off')
@click.option('-i', '--run-id', required=False, default=str(uuid.uuid1().hex))
@click.option('-f', '--training-file', required=False, default="src/models/train.py")
@click.option('-v', '--version', prompt=True, cls=Determinant, determinant='log_off')
@click.pass_context
def train_cmd(ctx, log_off, model, run_id, training_file, version):
    """ Train a model and log metadata """
    
    if os.path.isfile('src/models/tracking/metadata/{}.pkl'.format(run_id)): # Only checks locally. Should we check if there exists a log on Studio with the same ID as well?
        run_id = new_id(run_id)
    print("Preparing to start training session with '{}' as unique ID.".format(run_id))
    if os.path.isfile(training_file):
        if log_off:
            import subprocess
            subprocess.run(['python', training_file, run_id])
        else:
            model_exists = search_for_model(ctx, "models", model) 
            if model_exists:
                client = ctx.obj['CLIENT']
                client.train(model, run_id, training_file, version)
            else: 
                print("The model '{}' does not exist in the active project and cannot be trained.".format(model))
    else:
        current_dir = os.getcwd()
        print("Could not start a training session. Check that you have initialized a model "\
            + "in '{}' and that the file '{}' exists.".format(current_dir, training_file))    



@main.command('test')
@click.pass_context
def test_cmd(ctx):
    get_run_details('12')
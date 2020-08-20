import click
from .main import main
import requests
from scaleout.auth import login, get_stackn_config, get_remote_config
from .helpers import create_table

# @click.option('--daemon',
#               is_flag=True,
#               help=(
#                       "Specify to run in daemon mode."
#               )
#               )

@main.command('setup')
@click.pass_context
def setup_cmd(ctx):
    login()

@main.command('login')
@click.pass_context
def login_cmd(ctx):
    stackn_config, load_status = get_stackn_config()
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

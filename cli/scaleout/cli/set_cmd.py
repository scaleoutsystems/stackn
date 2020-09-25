import click
from .main import main
import requests
from scaleout.studioclient import StudioClient
import scaleout.auth as sauth
from .helpers import create_table
import os

@click.option('--daemon',
              is_flag=True,
              help=(
                      "Specify to run in daemon mode."
              )
              )

@main.group('set')
@click.pass_context
def set_cmd(ctx, daemon):
    pass

@set_cmd.command('remote')
@click.option('-r', '--remote', required=False)
@click.pass_context
def remote_cmd(ctx, remote):
    if not remote:
        remote = input('Remote: ')
    stackn_config, load_status = sauth.get_stackn_config()
    if not load_status:
        print('Failed to load STACKn config.')
    else:
        dirpath = os.path.expanduser('~/.scaleout/'+remote)
        if not os.path.exists(dirpath):
            print("Remote doesn't exist.")
            print("Configure remote with 'stackn setup'")
        else:
            stackn_config['active'] = remote
            sauth.write_stackn_config(stackn_config)
            print('New context: '+remote)

@set_cmd.command('mode')
@click.option('--secure/--insecure', default=True)
@click.pass_context
def secure_cmd(ctx, secure):
    stackn_config, load_status = sauth.get_stackn_config()
    stackn_config['secure'] = secure
    sauth.write_stackn_config(stackn_config)

@set_cmd.command('project')
@click.option('-p', '--project', required=False)
@click.pass_context
def project_cmd(ctx, project):
    if not project:
        project = input('Project: ')
    from scaleout.studioclient import StudioClient
    client = StudioClient()
    client.set_project(project)
import click
from .main import main
import requests
from scaleout.studioclient import StudioClient 
from .helpers import create_table

@click.option('--daemon',
              is_flag=True,
              help=(
                      "Specify to run in daemon mode."
              )
              )

@main.group('delete')
@click.pass_context
def delete_cmd(ctx, daemon):
    if daemon:
        print('{} NYI should run as daemon...'.format(__file__))

@delete_cmd.command('models')
@click.option('-n', '--name', required=True)
@click.pass_context
def delete_model_cmd(ctx, name):
    """ Delete a model """
    names = ["Name","Tag","Created"]
    keys = ['name', 'tag', 'uploaded_at']
    create_table(ctx, 'models', names, keys)

@delete_cmd.command('deployments')
@click.pass_context
def delete_deployment_cmd(ctx):
  """ Delete a deployment """
    names = ["Name","Model","Version"]
    keys = ["name", "model", "version"]
    create_table(ctx, 'deploymentInstances', names, keys)

@delete_cmd.command('deploymentdefinitions')
@click.pass_context
def delete_deploymentdefinition_cmd(ctx):
    names = ["Name"]
    keys = ["name"]
    create_table(ctx, "deploymentDefinitions", names, keys)

@delete_cmd.command('projects')
@click.pass_context
def delete_project_cmd(ctx):
    names = ["Name","Created", "Last updated"]
    keys = ["name", "created_at", "updated_at"]
    create_table(ctx, "projects", names, keys)


# alliance

# dataset
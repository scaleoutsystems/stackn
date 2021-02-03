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

@delete_cmd.command('model')
@click.option('-n', '--name', required=True)
@click.option('-v', '--version')
@click.pass_context
def delete_model_cmd(ctx, name, version=None):
    """ Delete a model """
    client = ctx.obj['CLIENT']
    client.delete_model(name, version)

@delete_cmd.command('deployment')
@click.option('-n', '--name', required=True)
@click.option('-v', '--version')
@click.pass_context
def delete_deployment_cmd(ctx, name, version=None):
    """ Delete a model """
    client = ctx.obj['CLIENT']
    client.delete_deployment(name, version)

@delete_cmd.command('dataset')
@click.option('-n', '--name', required=True)
@click.option('-v', '--version', required=True)
@click.pass_context
def delete_dataset_cmd(ctx, name, version=None):
    """ Delete a model """
    client = ctx.obj['CLIENT']
    client.delete_dataset(name, version)

@delete_cmd.command('volume')
@click.option('-n', '--name', required=True)
@click.pass_context
def delete_volume_cmd(ctx, name):
    """ Delete a volume """
    client = ctx.obj['CLIENT']
    client.delete_volume(name)

@delete_cmd.command('projects')
@click.option('-f', '--userfile', required=True)
@click.pass_context
def delete_projects(ctx, userfile):
    """ Delete a volume """
    client = ctx.obj['CLIENT']
    client.delete_projects(userfile)

@delete_cmd.command('resources')
@click.option('-f', '--userfile', required=True)
@click.pass_context
def delete_resources(ctx, userfile):
    """ Delete a volume """
    client = ctx.obj['CLIENT']
    client.delete_resources(userfile)

@delete_cmd.command('labs')
@click.option('-f', '--userfile', required=True)
@click.option('-p', '--project-name', required=True)
@click.option('-e', '--environment', required=True)
@click.option('-t', '--flavor', required=True)
@click.pass_context
def delete_labs_cmd(ctx, project_name, userfile, environment, flavor):
    client = ctx.obj['CLIENT']
    client.bulk_manage_labs(userfile, project_name, environment, flavor, "delete")

@delete_cmd.command('lab')
@click.option('-a', '--appname', required=True)
@click.pass_context
def delete_lab_cmd(ctx, appname):
    client = ctx.obj['CLIENT']
    client.delete_labs_appname(appname)


# @delete_cmd.command('deployments')
# @click.pass_context
# def delete_deployment_cmd(ctx):
#   """ Delete a deployment """
#     names = ["Name","Model","Version"]
#     keys = ["name", "model", "version"]
#     create_table(ctx, 'deploymentInstances', names, keys)

# @delete_cmd.command('deploymentdefinitions')
# @click.pass_context
# def delete_deploymentdefinition_cmd(ctx):
#     names = ["Name"]
#     keys = ["name"]
#     create_table(ctx, "deploymentDefinitions", names, keys)

# @delete_cmd.command('projects')
# @click.pass_context
# def delete_project_cmd(ctx):
#     names = ["Name","Created", "Last updated"]
#     keys = ["name", "created_at", "updated_at"]
#     create_table(ctx, "projects", names, keys)


# alliance

# dataset
import click
from .main import main
import requests
from prettytable import PrettyTable
from scaleout.studioclient import StudioClient 


@click.option('--daemon',
              is_flag=True,
              help=(
                      "Specify to run in daemon mode."
              )
              )

@main.group('create')
@click.pass_context
def create_cmd(ctx, daemon):
  if daemon:
      print('{} NYI should run as daemon...'.format(__file__))

@create_cmd.command('model')
@click.option('-f', '--model-file', required=False, default="")
@click.option('-n', '--model-name', required=True)
@click.option('-r', '--release-type', required=False)
@click.option('-d', '--description', required=False,default="")
@click.pass_context
def create_model_cmd(ctx, model_file, model_name, release_type, description):
  """ Publish a model. """
  client = ctx.obj['CLIENT']
  client.create_model(model_file, model_name, release_type, description)

@create_cmd.command('deploymentdefinition')
@click.option('-n', '--name', required=True)
@click.option('-f', '--filepath', required=True)
@click.option('-p', '--path_predict')
@click.pass_context
def create_deployment_definition(ctx, name, filepath, path_predict=''):
    """ Create a deployment definition. """
    client = ctx.obj['CLIENT']
    client.create_deployment_definition(name, filepath, path_predict)

@create_cmd.command('deployment')
@click.option('-m', '--model', required=True)
@click.option('-v', '--model-version', default='latest')
@click.option('-d', '--deploymentdefinition', required=True)
@click.option('-s', '--settings', required=False)
@click.pass_context
def create_deployment_cmd(ctx, model, deploymentdefinition, model_version=[], settings=[]):
    client = ctx.obj['CLIENT']
    client.deploy_model(model, model_version, deploymentdefinition, settings)


# Create project
@create_cmd.command('project')
@click.option('-n', '--name', required=True)
@click.option('-d', '--description', required=False)
@click.option('-r', '--repository', required=False)
@click.pass_context
def create_project_cmd(ctx, name, description='', repository=''):
    client = ctx.obj['CLIENT']
    client.create_project(name, description, repository)

@create_cmd.command('lab')
@click.option('-f', '--flavor', required=True)
@click.option('-e', '--environment', required=True)
@click.option('-v', '--volumes', required=False, default=[])
@click.pass_context
def create_session(ctx, flavor, environment, volumes):
    client = ctx.obj['CLIENT']
    client.create_session(flavor_slug=flavor, environment_slug=environment, volumes=volumes)

@create_cmd.command('volume')
@click.option('-s', '--size', required=True)
@click.option('-n', '--name', required=True)
@click.pass_context
def create_volume(ctx, size, name):
    client = ctx.obj['CLIENT']
    client.create_volume(name=name, size=size)

@create_cmd.command('job')
@click.option('-c', '--config', required=True)
@click.pass_context
def create_job(ctx, config):
    client = ctx.obj['CLIENT']
    client.create_job(config)

# Create dataset


@create_cmd.command('dataset')
@click.option('-n', '--name', required=True)
@click.option('-f', '--filenames', required=False)
@click.option('-d', '--directory', required=False)
@click.option('-r', '--release_type', required=False, default='minor')
@click.pass_context
def create_dataset(ctx, name, directory=[], filenames=[], release_type='minor', description='', bucket='dataset'):
    client = ctx.obj['CLIENT']
    client.create_dataset(name,
                          release_type,
                          filenames,
                          directory,
                          description=description,
                          bucket=bucket)

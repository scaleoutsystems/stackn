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
@click.option('-c', '--cluster', required=False, default=[])
@click.pass_context
def create_session(ctx, flavor, environment, volumes, cluster):
    client = ctx.obj['CLIENT']
    client.create_session(flavor_slug=flavor, environment_slug=environment, volumes=volumes, cluster=cluster)

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

@create_cmd.command('users')
@click.option('-f', '--userfile', required=True)
@click.pass_context
def create_users_cmd(ctx, userfile):
    client = ctx.obj['CLIENT']
    client.create_users(userfile)

@create_cmd.command('projects')
@click.option('-f', '--userfile', required=True)
@click.option('-b', '--project-name', required=True)
@click.option('-c', '--cluster', required=False, default="default")
@click.pass_context
def create_projects_cmd(ctx, userfile, project_name, cluster):
    client = ctx.obj['CLIENT']
    client.create_projects(userfile, project_name, cluster)

@create_cmd.command('labs')
@click.option('-f', '--userfile', required=True)
@click.option('-p', '--project-name', required=True)
@click.option('-e', '--environment', required=True)
@click.option('-t', '--flavor', required=True)
@click.pass_context
def create_labs_cmd(ctx, project_name, userfile, environment, flavor):
    client = ctx.obj['CLIENT']
    client.bulk_manage_labs(userfile, project_name, environment, flavor, "create")


@create_cmd.command('passwords')
@click.option('-f', '--user-file', required=True)
@click.pass_context
def passwords_cmd(ctx, user_file):
    client = ctx.obj['CLIENT']
    client.reset_passwords(user_file)
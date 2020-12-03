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

@main.group('get')
@click.pass_context
def get_cmd(ctx, daemon):
    if daemon:
        print('{} NYI should run as daemon...'.format(__file__))

@get_cmd.command('settings')
@click.pass_context
def get_settings_cmd(ctx):
    """ List STACKn settings needed to set up the CLI client. """

    names = ['Setting', 'Value']
    keys = ['name', 'value']
    create_table(ctx, 'settings', names, keys)

@get_cmd.command('models')
@click.pass_context
def get_models_cmd(ctx):
    """ List all models and show their status and endpoints """
    names = ["Name","Version","Created"]
    keys = ['name', 'version', 'uploaded_at']
    create_table(ctx, 'models', names, keys)

@get_cmd.command('deployments')
@click.pass_context
def get_deployments_cmd(ctx):
    # client = ctx.obj['CLIENT']
    # client.list_deployments()
    names = ["Name","Version", "Endpoint"]
    keys = ["name", "version", "endpoint"]
    create_table(ctx, 'deploymentInstances', names, keys)

@get_cmd.command('deploymentdefinitions')
@click.pass_context
def get_deploymentdefinitions_cmd(ctx):
    names = ["Name"]
    keys = ["name"]
    create_table(ctx, "deploymentDefinitions", names, keys)

@get_cmd.command('projects')
@click.pass_context
def get_projects_cmd(ctx):
    names = ["Name","Created", "Last updated"]
    keys = ["name", "created_at", "updated_at"]
    create_table(ctx, "projects", names, keys)

@get_cmd.command('labs')
@click.pass_context
def lab_list_all_cmd(ctx):
    """ List all Lab Sessions. """
    names = ["Name", "Flavor", "Environment", "Status", "Created"]
    keys = ["name", "flavor_slug", "environment_slug", "status", "created_at"]
    create_table(ctx, "labs", names, keys)

@get_cmd.command('members')
@click.pass_context
def members_list_cmd(ctx):
    """ List all project members. """
    names = ["Username"]
    keys = ["username"]
    create_table(ctx, "members", names, keys)

@get_cmd.command('dataset')
@click.pass_context
def dataset_list_cmd(ctx):
    """ List all project members. """
    names = ["Name", "Version", "Release", "Project", "Created", "Created by"]
    keys = ["name", "version", "release_type", "project_slug", "created_on", "created_by"]
    create_table(ctx, "dataset", names, keys)

# alliance

# dataset
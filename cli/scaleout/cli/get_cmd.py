import json
import click
from .main import main
import requests
from .helpers import create_table, PrettyTable

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
    """
    List STACKn settings needed to set up the CLI client.
    """
    studio_host = input("Studio host: ")
    url = "{}/api/settings".format(studio_host)
    try:
        r = requests.get(url)
        studio_settings = json.loads(r.content)["data"]

        names = ['Setting', 'Value']
        keys = ['name', 'value']
        x = PrettyTable()
        x.field_names = names
        for item in studio_settings:
            row = [item[k] for k in keys]
            x.add_row(row)
        print(x)
    except Exception as e:
        print("Couldn't get studio settings.")
        print("Returned status code: {}".format(r.status_code))
        print("Reason: {}".format(r.reason))
        print("Error: {}".format(e))

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
    """ List all projects. """
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

@get_cmd.command('volumes')
@click.pass_context
def get_volumes_cmd(ctx):
    """ List all volumes """
    names = ["Name","Size", "Created by","Created"]
    keys = ['name', 'size', 'created_by', 'created_on']
    create_table(ctx, 'volumes', names, keys)

@get_cmd.command('jobs')
@click.pass_context
def get_jobs_cmd(ctx):
    """ List all jobs """
    names = ["User","command", "Environment","Schedule"]
    keys = ['username', 'command', 'environment', 'schedule']
    create_table(ctx, 'jobs', names, keys)

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
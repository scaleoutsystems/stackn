import click
from .main import main

from scaleout.project import init_project as init_p
from scaleout.studioclient import StudioClient

def init_project(project_dir):
    init_p(project_dir)

@main.group('project')
@click.pass_context
def project_cmd(ctx, daemon):
  if daemon:
      print('{} NYI should run as daemon...'.format(__file__))

@project_cmd.command('init')
@click.pass_context
def init_cmd(ctx):
	""" Create project template files in the current working directory. """
	project_dir = ctx.obj['PROJECT_DIR']
	init_project(project_dir)

@project_cmd.command('fetch')
@click.pass_context
def fetch_cmd(ctx):
	""" Stage project components locally.  """


@project_cmd.command('list')
@click.pass_context
def list_cmd(ctx):
	""" List projects. """
	client = ctx['CONTROLLER']

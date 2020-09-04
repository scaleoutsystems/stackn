import click
from .main import main


@main.group('lab')
@click.pass_context
def lab_cmd(ctx):
    pass


@lab_cmd.command('create')
@click.option('-f', '--flavor', required=True)
@click.option('-e', '--environment', required=True)
@click.pass_context
def create_session(ctx, flavor, environment):
    client = ctx.obj['CLIENT']
    client.create_session(flavor_slug=flavor, environment_slug=environment)


# List group
@lab_cmd.group('list')
@click.pass_context
def lab_list_cmd(ctx):
    pass


@lab_list_cmd.command('all')
@click.pass_context
def lab_list_all_cmd(ctx):
    pass

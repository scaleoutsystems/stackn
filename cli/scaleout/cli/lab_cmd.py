import click
from .main import main
from prettytable import PrettyTable


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
    """ List all Lab Sessions. """

    client = ctx.obj['CLIENT']
    labs = client.get_lab_sessions()

    x = PrettyTable()
    x.field_names = ["Name", "Flavor", "Environment", "Status", "Created"]
    for l in labs:
        x.add_row([l["name"], l["flavor_slug"], l["environment_slug"], l['status'], l['created_at']])
    print(x)

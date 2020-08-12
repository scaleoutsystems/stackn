import click
from .main import main
import requests
from scaleout.auth import login 
from .helpers import create_table

@click.option('--daemon',
              is_flag=True,
              help=(
                      "Specify to run in daemon mode."
              )
              )

@main.group('login')
@click.pass_context
def login_cmd(ctx, daemon):
    pass

@login_cmd.command('login')
@click.pass_context
def login_cmd(ctx):
    login()


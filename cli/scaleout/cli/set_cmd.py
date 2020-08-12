import click
from .main import main
import requests
from scaleout.auth import login 
from .helpers import create_table
import os

@click.option('--daemon',
              is_flag=True,
              help=(
                      "Specify to run in daemon mode."
              )
              )

@main.group('set')
@click.pass_context
def set_cmd(ctx, daemon):
    pass

@set_cmd.command('remote')
@click.pass_context
def remote_cmd(ctx):
    remote = input('Remote: ')
    # os.


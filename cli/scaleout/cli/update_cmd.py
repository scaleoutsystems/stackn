import click
from .main import main
import requests
from scaleout.studioclient import StudioClient
import scaleout.auth as sauth
from .helpers import create_table
import os

@click.option('--daemon',
              is_flag=True,
              help=(
                      "Specify to run in daemon mode."
              )
              )

@main.group('update')
@click.pass_context
def update_cmd(ctx, daemon):
    pass


@update_cmd.command('deployment')
@click.option('-n', '--name', required=True)
@click.option('-t', '--tag')
@click.option('-r', '--replicas', required=False)
@click.pass_context
def update_deployment_cmd(ctx, name, tag='latest', replicas=[]):
    if replicas:
        client = ctx.obj['CLIENT']
        client.update_deployment(name, tag, params={'replicas': replicas})
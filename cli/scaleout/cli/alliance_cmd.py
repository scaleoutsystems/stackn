import click
from .main import main

import requests

@click.option('--daemon',
              is_flag=True,
              help=(
                      "Specify to run in daemon mode."
              )
              )

@main.group('alliance')
@click.pass_context
def alliance_cmd(ctx, daemon):
  if daemon:
      print('{} NYI should run as daemon...'.format(__file__))

@alliance_cmd.command('show')
@click.pass_context
def show_cmd(ctx):
  """ Show basic information about this alliance model. """ 

@alliance_cmd.group('member')
@click.pass_context
def member_cmd(ctx):
  """ List models and their status and endpoints """ 

@member_cmd.command('list')
@click.pass_context
def member_list_cmd(ctx):
  """ List alliance members. """ 
  print("List all alliance members, showing an overview and status.")

@member_cmd.command('show')
@click.pass_context
def member_show_cmd(ctx):
  """ Show info about member <member_id> """ 
  print("Show detailed information for a member")


@alliance_cmd.group('run')
@click.pass_context
def run_cmd(ctx):
  """ Run local clients."""
 
@run_cmd.command('client')
@click.pass_context
def client_cmd(ctx):
    controller = ctx.obj['CONTROLLER']
    controller.client()

@run_cmd.command('train')
@click.pass_context
def train_cmd(ctx):
    controller = ctx.obj['CONTROLLER']
    controller.train()


@run_cmd.command('validate')
@click.pass_context
def validate_cmd(ctx):
    controller = ctx.obj['CONTROLLER']
    controller.validate()


@run_cmd.command('predict')
@click.pass_context
def predict_cmd(ctx):
    controller = ctx.obj['CONTROLLER']
    controller.predict()


@alliance_cmd.group('history')
@click.pass_context
def history_cmd(ctx):
  """ List models and their status and endpoints """ 

@history_cmd.command('list')
@click.pass_context
def history_list_cmd(ctx):
  """ List history for this alliance model. """ 
  # TODO: Should have some kind of pretty print here?
  controller = ctx.obj['CONTROLLER']
  repository = controller.get_repository()
  repository.list_artifacts()


  


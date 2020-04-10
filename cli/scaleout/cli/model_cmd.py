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

@main.group('model')
@click.pass_context
def model_cmd(ctx, daemon):
  if daemon:
      print('{} NYI should run as daemon...'.format(__file__))

@model_cmd.command('list')
@click.pass_context
def list_cmd(ctx):
  """ List all models and show their status and endpoints """
  client = ctx.obj['CLIENT']
  models = client.list_models()

  x = PrettyTable()
  x.field_names = ["Name","Tag","ID"]
  for m in models:
    x.add_row([m["name"],m["tag"],m["uid"]])
  print(x)

@model_cmd.command('show')
@click.option('-m', '--model', required=True)
@click.pass_context
def show_cmd(ctx,model):
  """ Show model details. """
  client = ctx.obj['CLIENT']
  model = client.show_model(model)
  x = PrettyTable()
  #x.field_names = list(model.keys())
  x.add_column("Property",list(model.keys()))
  x.add_column("Value",list(model.values()))
  print(x)


@model_cmd.command('publish')
@click.option('-m', '--model', required=True)
@click.option('-n', '--name', required=True)
@click.option('-t', '--tag', required=False,default="latest")
@click.option('-u', '--url', required=False,default=None)
@click.option('-d', '--description', required=False,default="")
@click.pass_context
def publish_cmd(ctx, model, name, tag, url, description):
  """ Publish a model to Studio. """
  client = ctx.obj['CLIENT']
  client.publish_model(model, name, tag, url, description)

@click.option('-m','--model_id',required=True)
@click.option('-t','--tag')
@click.option('-o','--output',default="model.out")
@model_cmd.command('download')
@click.pass_context
def download_cmd(ctx, model_id, tag, output):
    """ Download a model. """
    # TODO: Use model tag, default to latest 
    client = ctx.obj['CLIENT']
    repository = client.get_repository()
    repository.bucket = 'models'
    obj = repository.get_artifact(model_id)

    with open(output, 'wb') as fh:
      fh.write(obj)

@click.option('-n', '--name', required=True)
@click.option('-t', '--tag', required=False)
@model_cmd.command('delete')
@click.pass_context
def delete_cmd(ctx, name,tag):
    """ Delete a model. """
    # TODO: It should probably not be possible to delete ANY model (e.g. seed models)
    client = ctx.obj['CLIENT']
    client.delete_model(name,tag)
    #repository = client.get_repository()
    #repository.bucket = 'models'
    #repository.delete_artifact(instance_name)

import click

from .main import main
from .stackn import create_object, create_project, create_resource, create_releasename, create_app

class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        try:
            cmd_name = ALIASES[cmd_name].name
        except KeyError:
            pass
        return super().get_command(ctx, cmd_name)


@main.group('create', cls=AliasedGroup)
def create():
  pass

@create.command('project')
@click.argument('name')
@click.option('-d', '--description', required=False, default="")
@click.option('-t', '--template', required=False, default="stackn-default")
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def project(name, description, template, studio_url, secure):
    create_project(name, description=description, template=template, secure_mode=secure)

@create.command('resource')
@click.argument('filename')
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('-p', '--project', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def resource(filename, studio_url, project, secure):
    create_resource(filename, studio_url=studio_url, project=project, secure=secure)

@create.command('releasename')
@click.argument('name')
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('-p', '--project', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def releasename(name, studio_url, project, secure):
    create_releasename(name, studio_url=studio_url, project=project, secure=secure)

@create.command('object')
@click.argument('name')
@click.option('-t', '--object-type', required=False, default="model")
@click.option('-f', '--file-name', required=False, default="")
@click.option('-r', '--release-type', required=False, default="minor")
@click.option('-d', '--description', required=False, default="")
@click.option('-m', '--model-card', required=False, default="")
@click.option('-p', '--project', required=False, default=[])
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('-s', '--s3-storage', required=False, default=None)
@click.option('--secure/--insecure', default=True)
def obj(name, object_type, file_name, release_type, description, model_card, project, studio_url, s3_storage, secure):
    create_object(name,
                  model_file=file_name,
                  project_name=project,
                  release_type=release_type,
                  object_type=object_type,
                  model_description=description,
                  model_card=model_card,
                  studio_url=studio_url,
                  s3storage=s3_storage,
                  secure_mode=secure)


# Admin commands

@create.command('app')
@click.option('-t', '--settings', required=False, default="config.json")
@click.option('-a', '--chart', required=False, default="chart")
@click.option('-l', '--logo', required=False, default="logo.png")
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def app(settings, chart, logo, studio_url, secure):
    print("CREATING APP")
    create_app(settings,
               chart,
               logo=logo,
               studio_url=studio_url,
               secure_mode=secure)
    #, studio_url=studio_url, project=project, secure=secure)




ALIASES = {
    "projects": project,
    "resources": resource,
    "app": app,
    "apps": app,
    "objects": obj,
    "environments": resource,
    "environment": resource,
    "flavors": resource
}
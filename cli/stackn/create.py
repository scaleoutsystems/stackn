import click

from .main import main
from .stackn import (create_app, create_apps, create_meta_resource,
                     create_object, create_project, create_template,
                     create_templates)


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


# Admin-privileges commands

@create.command('app')
@click.option('-t', '--settings', required=False, default="config.json")
@click.option('-a', '--chart', required=False, default="chart")
@click.option('-l', '--logo', required=False, default="logo.png")
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def app(settings, chart, logo, studio_url, secure):
    create_app(settings,
               chart,
               logo=logo,
               studio_url=studio_url,
               secure_mode=secure)


@create.command('apps')
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def apps(studio_url, secure):
    create_apps(studio_url=studio_url,
                secure_mode=secure)


@create.command('projecttemplate')
@click.option('-t', '--settings', required=False, default="template.json")
@click.option('-i', '--image', required=False, default="image.png")
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def template(settings, image, studio_url, secure):
    create_template(template=settings,
                    image=image,
                    studio_url=studio_url,
                    secure_mode=secure)


@create.command('projecttemplates')
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def templates(studio_url, secure):
    create_templates(studio_url=studio_url,
                     secure_mode=secure)


# Also for non-admin users

@create.command('meta-resource', help="Such as: project environments, flavors, mlflow and s3 enpoints")
@click.argument('filename')
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('-p', '--project', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def metaresource(filename, studio_url, project, secure):
    create_meta_resource(filename, studio_url=studio_url,
                         project=project, secure=secure)


@create.command('model-obj')
@click.argument('name')
@click.option('-t', '--object-type', required=False, default="model")
@click.option('-f', '--file-name', required=False, default="")
@click.option('-r', '--release-type', required=False, default="minor")
@click.option('-v', '--version', required=False, default="1.0")
@click.option('-d', '--description', required=False, default="")
@click.option('-m', '--model-card', required=False, default="")
@click.option('-p', '--project', required=False, default=[])
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('-s', '--s3-storage', required=False, default=None)
@click.option('--secure/--insecure', default=True)
def obj(name, object_type, file_name, release_type, version, description, model_card, project, studio_url, s3_storage, secure):
    create_object(name,
                  model_file=file_name,
                  project_name=project,
                  release_type=release_type,
                  version=version,
                  object_type=object_type,
                  model_description=description,
                  model_card=model_card,
                  studio_url=studio_url,
                  s3storage=s3_storage,
                  secure_mode=secure)


@create.command('project')
@click.argument('name')
@click.option('-d', '--description', required=False, default="")
@click.option('-t', '--template', required=False, default="default")
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def project(name, description, template, studio_url, secure):
    create_project(name, description=description,
                   template=template, secure_mode=secure)


ALIASES = {
    "projects": project,
    "resources": metaresource,
    "app": app,
    "objects": obj,
    "environments": metaresource,
    "environment": metaresource,
    "flavors": metaresource
}

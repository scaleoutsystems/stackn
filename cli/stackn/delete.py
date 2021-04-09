import click
from .main import main
from .stackn import delete_app, delete_object, delete_project, delete_meta_resource

class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        try:
            cmd_name = ALIASES[cmd_name].name
        except KeyError:
            pass
        return super().get_command(ctx, cmd_name)

@main.group('delete')
def delete():
  pass

@delete.command('project')
@click.argument('name')
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def delete_proj(name, studio_url, secure):
    delete_project(name, studio_url=studio_url, secure=secure)

@delete.command('app')
@click.argument('name')
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('-p', '--project', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def app(name, studio_url, project, secure):
    delete_app(name, studio_url, project, secure)

@delete.command('object')
@click.argument('name')
@click.option('-v', '--version', required=False, default=[])
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('-p', '--project', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def delete_obj(name, version, studio_url, project, secure):
    delete_object(name,
                  version=version,
                  studio_url=studio_url,
                  project=project,
                  secure=secure)

@delete.command('environment')
@click.argument('name')
@click.option('-p', '--project', required=False, default=[])
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def delete_env(name, project, studio_url, secure):
    delete_meta_resource('environments', name, project=project, studio_url=studio_url, secure=secure)

@delete.command('flavor')
@click.argument('name')
@click.option('-p', '--project', required=False, default=[])
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def delete_flavor(name, project, studio_url, secure):
    delete_meta_resource('flavors', name, project=project, studio_url=studio_url, secure=secure)

@delete.command('MLflow')
@click.argument('name')
@click.option('-p', '--project', required=False, default=[])
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def delete_mlflow(name, project, studio_url, secure):
    delete_meta_resource('mlflow', name, project=project, studio_url=studio_url, secure=secure)

@delete.command('S3')
@click.argument('name')
@click.option('-p', '--project', required=False, default=[])
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def delete_s3(name, project, studio_url, secure):
    delete_meta_resource('s3', name, project=project, studio_url=studio_url, secure=secure)

@delete.command('releasename')
@click.argument('name')
@click.option('-p', '--project', required=False, default=[])
@click.option('-u', '--studio-url', required=False, default=[])
@click.option('--secure/--insecure', default=True)
def delete_s3(name, project, studio_url, secure):
    delete_meta_resource('releasenames', name, project=project, studio_url=studio_url, secure=secure)

ALIASES = {
    "projects": delete_proj,
    "app": app,
    "apps": app,
    "objects": delete_obj,
    "environments": delete_env,
    "environment": delete_env,
    "env": delete_env,
    "flavors": delete_flavor
}
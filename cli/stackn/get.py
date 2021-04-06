import click
import prettytable

from .main import main
from .stackn import get_projects, call_project_endpoint, get_current, get_remote

class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        try:
            cmd_name = ALIASES[cmd_name].name
        except KeyError:
            pass
        return super().get_command(ctx, cmd_name)

def _print_table(resource, names, keys):
    x = prettytable.PrettyTable()
    x.field_names = names
    for item in resource:
        row = [item[k] for k in keys]
        x.add_row(row)
    print(x)

def _find_dict_by_value(dicts, key, value):
    try:
        res = next(item for item in dicts if item[key] == value)
    except Exception as e:
        print("Object type {} doesn't exist.".format(value))
        return []
    return res

@main.group('get', cls=AliasedGroup)
def get():
  pass

@get.command('remote')
def get_rem():
    current = get_remote()
    for curr in current:
        print(curr)



@get.command('current')
def get_curr():
    current = get_current()
    if current['STACKN_URL']:
        print("Studio: {}".format(current['STACKN_URL']))
        if current['STACKN_PROJECT']:
            print("Project: {}".format(current['STACKN_PROJECT']))
        else:
            print("No project set.")
    else:
        print("No STACKn instance set as current.")

@get.command('project')
@click.option('-u', '--studio-url', required=False, default=[])
def project(studio_url):
    conf = {
        'STACKN_URL': studio_url
    }
    projects = get_projects(conf=conf)
    if projects:
        _print_table(projects, ['Name', 'Created'], ['name', 'created_at'])



@get.command('app')
@click.option('-c', '--category', required=False, default=[])
def app(category):
    params = []
    if category:
        params = {"app__category": category.lower()}
    apps = call_project_endpoint('appinstances', params=params)
    applist = list()
    for app in apps:
        tmp = dict()
        tmp['name'] = app['name']
        tmp['app_name'] = app['app']['name']
        tmp['app_cat'] = app['app']['category']['name']
        tmp['url'] = ''
        tmp['state'] = app['state']
        status = max(app['status'], key=lambda x:x['id'])
        tmp['status'] = status['status_type']
        if 'url'in app['table_field']:
            tmp['url'] = app['table_field']['url']
        applist.append(tmp)
    applist = sorted(applist, key=lambda k: k['app_cat']) 

    _print_table(applist, ['Category', 'App', 'Name', 'URL', 'Status'], ['app_cat', 'app_name', 'name', 'url', 'status'])
    # print(apps)


@get.command('object')
@click.option('-t', '--object-type', required=False, default="model")
@click.option('-p', '--project', required=False, default=[])
@click.option('-u', '--studio-url', required=False, default=[])
def obj(object_type, project, studio_url):
    conf = {
        'STACKN_OBJECT_TYPE': object_type,
        'STACKN_PROJECT': project,
        'STACKN_URL': studio_url
    }
    params = []
    object_types = call_project_endpoint('objecttypes', conf=conf)
    if not object_types:
        return
    if object_type:
        obj_type = _find_dict_by_value(object_types, 'slug', object_type)
        if not obj_type:
            return
        params = {'object_type': obj_type['id']}

    objects = call_project_endpoint('models', conf=conf, params=params)

    obj_dict = dict()
    for obj_type in object_types:
        obj_dict[str(obj_type['id'])] = obj_type['name']
    for obj in objects:
        obj['object_type'] = obj_dict[str(obj['object_type'][0])]
    _print_table(objects, ['Name', 'Version', 'Type', 'Created'], ['name', 'version','object_type', 'uploaded_at'])

@get.command('environment')
def environment():
    environments = call_project_endpoint('environments')
    envlist = list()
    for env in environments:
        tmp = dict()
        tmp['name'] = env['name']
        tmp['app_name'] = env['app']['name']
        tmp['cat'] = env['app']['category']['name']
        tmp['image'] = env['repository']+'/'+env['image']
        envlist.append(tmp)
    header = ['Category', 'App', 'Name', 'Image']
    fields = ['cat', 'app_name', 'name', 'image']
    envlist = sorted(envlist, key=lambda k: k['cat']) 
    _print_table(envlist, header, fields)

@get.command('flavor')
def flavor():
    flavors = call_project_endpoint('flavors')
    header = ['Name', 'CPU req', 'CPU lim', 'Mem req', 'Mem lim', 'GPUs', 'Eph mem req', 'Eph mem lim']
    fields = ['name', 'cpu_req', 'cpu_lim', 'mem_req', 'mem_lim', 'gpu_req', 'ephmem_req', 'ephmem_lim']
    _print_table(flavors, header, fields)

@get.command('objecttypes')
def objecttypes():
    objecttypes = call_project_endpoint('objecttypes')
    _print_table(objecttypes, ['Name', 'Slug'], ['name', 'slug'])

@get.command('S3')
@click.option('-n', '--name', required=False, default=[])
def s3(name):
    params = []
    if name:
        params = {"name": name}
    s3s = call_project_endpoint('s3', params=params)
    _print_table(s3s, ['Name', 'Host', 'Region'], ['name', 'host', 'region'])

@get.command('mlflow')
def mlflow():
    mlflows = call_project_endpoint('mlflow')
    mlflowlist = list()
    for mlflow in mlflows:
        tmp = dict()
        tmp['name'] = mlflow['name']
        tmp['URL'] = mlflow['mlflow_url']
        tmp['S3'] = mlflow['s3']['name']
        mlflowlist.append(tmp)
    _print_table(mlflowlist, ['Name', 'URL', 'S3'], ['name', 'URL', 'S3'])

@get.command('templates')
def templates():
    print('templates')

ALIASES = {
    "projects": project,
    "proj": project,
    "apps": app,
    "objects": obj,
    "model": obj,
    "models": obj,
    "obj": obj,
    "environments": environment,
    "env": environment,
    "flavors": flavor,
    "fl": flavor,
    "s3": s3,
    "MLflow": mlflow,
    "mlflows": mlflow,
    "MLflows": mlflow
}
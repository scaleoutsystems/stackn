import json
import os
import subprocess
import uuid

import requests

import stackn.auth
import stackn.error_msg
import stackn.s3


def _check_status(r, error_msg="Failed"):
    if (r.status_code < 200 or r.status_code > 299):
        print(error_msg)
        print('Returned status code: {}'.format(r.status_code))
        print('Reason: {}'.format(r.reason))
        print(r.text)
        return False
    else:
        return True

# Sort of utils functions


def call_admin_endpoint(name, conf={}, params=[]):

    conf, status = stackn.auth.get_config(conf)

    if not status:
        print("Failed to get current STACKn configuration file.")
        return False

    auth_header, conf = get_auth_header(conf)

    if not auth_header:
        return False

    endpoints = get_endpoints(conf['STACKN_URL'])
    url = endpoints[name]

    if params:
        r = requests.get(url, headers=auth_header,
                         params=params, verify=conf['STACKN_SECURE'])
    else:
        r = requests.get(url, headers=auth_header,
                         verify=conf['STACKN_SECURE'])
    if r:
        objs = json.loads(r.content)
        return objs
    else:
        print("Fetching {} failed.".format(name))
        print('Returned status code: {}'.format(r.status_code))
        print('Reason: {}'.format(r.reason))
        return None


def call_project_endpoint(name, conf={}, params=[]):

    conf, status = stackn.auth.get_config(conf)

    if not status:
        print("The configuration file for STACKn could not be correctly retrieved.")
        return False

    auth_header, conf = get_auth_header(conf)

    if not auth_header:
        return False

    endpoints = get_endpoints(conf['STACKN_URL'])

    if conf['STACKN_PROJECT']:
        project = get_projects(conf, params={'name': conf['STACKN_PROJECT']})
    else:
        print("No project name specified.")
        print("Try to run 'stackn get current' to check if a project is set.")
        return False
    if len(project) > 1:
        print('Found several matching projects.')
        return
    if not project:
        print("Project \'{}\' not found.".format(conf['STACKN_PROJECT']))
        return False

    project = project[0]
    url = endpoints[name].format(project['id'])

    if params:
        r = requests.get(url, headers=auth_header,
                         params=params, verify=conf['STACKN_SECURE'])
    else:
        r = requests.get(url, headers=auth_header,
                         verify=conf['STACKN_SECURE'])
    if r:
        projects = json.loads(r.content)
        return projects
    else:
        print("Fetching {} failed.".format(name))
        print('Returned status code: {}'.format(r.status_code))
        print('Reason: {}'.format(r.reason))
        return None


def setup_project_endpoint_call(conf, endpoint_type):

    conf, status = stackn.auth.get_config(conf, required=['STACKN_URL'])

    if not status:
        print("Failed to get current STACKn configuration file.")
        return False, False, False

    auth_header, conf = get_auth_header(conf)
    if not auth_header:
        return False, False, False

    project = get_projects(
        conf, params={'name': conf['STACKN_PROJECT']}, auth_header=auth_header)

    if project == False:
        return False, False, False
    elif len(project) > 1:
        print('Found several matching projects. Please select a specific project.')
        return False, False, False
    elif len(project) == 0:
        print("Project \'{}\' not found.".format(conf['STACKN_PROJECT']))
        return False, False, False

    project = project[0]
    endpoints = get_endpoints(conf['STACKN_URL'])
    url = endpoints[endpoint_type].format(project['id'])
    return conf, auth_header, url

# Get functions


def get_endpoints(studio_url):
    # These endpoints are related to the API available in Studio under: stackn/components/studio/api/
    endpoints = dict()
    if (not 'http://' in studio_url) and (not 'https://' in studio_url):
        studio_url = 'https://'+studio_url
    base = studio_url.strip('/')+'/api'
    endpoints['admin'] = dict()
    endpoints['admin']['apps'] = base+'/apps/'
    endpoints['appinstances'] = base+'/projects/{}/appinstances/'
    endpoints['environments'] = base+'/projects/{}/environments/'
    endpoints['flavors'] = base+'/projects/{}/flavors/'
    endpoints['members'] = base+'/projects/{}/members/'
    endpoints['models'] = base+'/projects/{}/models/'
    endpoints['mlflow'] = base+'/projects/{}/mlflow/'
    endpoints['objecttypes'] = base+'/projects/{}/objecttype'
    endpoints['project_del'] = base+'/projects/{}'
    endpoints['projects'] = base+'/projects/'
    endpoints['project_templates'] = base+'/projecttemplates/'
    endpoints['resources'] = base+'/projects/{}/resources/'
    endpoints['s3'] = base+'/projects/{}/s3/'

    return endpoints


def get_auth_header(conf):
    conf, status = stackn.auth.get_config(conf)
    if not status:
        return False, False
    auth_header = {"Authorization": "Token {}".format(
        conf['STACKN_ACCESS_TOKEN'])}
    return auth_header, conf


def get_current(secure):

    res = {'STACKN_URL': False, 'STACKN_PROJECT': False}
    conf, status = stackn.auth.get_config({'STACKN_SECURE': secure})

    if not status:
        print("Failed to get current STACKn configuration file.")
    else:
        if 'STACKN_URL' in conf:
            res['STACKN_URL'] = conf['STACKN_URL']
        if 'STACKN_PROJECT' in conf:
            res['STACKN_PROJECT'] = conf['STACKN_PROJECT']

    return res


def get_projects(conf={}, params=[], auth_header=[]):

    conf, status = stackn.auth.get_config(conf)

    if not status:
        print('Cannot list projects.')
        return False

    auth_header, conf = get_auth_header(conf)

    if not auth_header:
        return False

    endpoints = get_endpoints(conf['STACKN_URL'])
    url = endpoints['projects']
    if params:
        r = requests.get(url, headers=auth_header,
                         params=params, verify=conf['STACKN_SECURE'])
    else:
        r = requests.get(url, headers=auth_header,
                         verify=conf['STACKN_SECURE'])
    if r:
        projects = json.loads(r.content)
        return projects
    else:
        print("Fetching projects failed.")
        print('Returned status code: {}'.format(r.status_code))
        print('Reason: {}'.format(r.reason))
        return None


def get_remote(inp_conf):

    conf, status = stackn.auth.get_config(inp_conf)

    if not status:
        return False

    keys = stackn.auth._get_remote(conf)

    if not keys:
        return False

    return keys


# Create functions

def create_template(template='template.json', image="image.png", studio_url=[], secure_mode=True):

    conf = {
        'STACKN_URL': studio_url,
        'STACKN_SECURE': secure_mode
    }

    conf, status = stackn.auth.get_config(conf, required=['STACKN_URL'])

    if not status:
        print("Failed to get current STACKn configuration file.")
        return False

    auth_header, conf = get_auth_header(conf)
    if not auth_header:
        return False

    with open(template, 'r') as templ_file:
        try:
            settings = json.load(templ_file)
        except Exception as err:
            print("Failed to load JSON from settings file.")
            print(err)

    payload = {
        'settings': json.dumps(settings)
    }

    file_ob = {'image': open(image, 'rb')}

    endpoints = get_endpoints(conf['STACKN_URL'])
    url = endpoints['project_templates']
    r = requests.post(url, headers=auth_header, files=file_ob,
                      data=payload, verify=conf['STACKN_SECURE'])

    if r:
        print("Created template.")
    else:
        print("Failed to create template.")
        print(r.status_code)
        print(r.text)
        print(r.reason)


def create_templates(folder='.', studio_url=[], secure_mode=True):
    subfolders = [f.path for f in os.scandir(folder) if f.is_dir()]
    curr_dir = os.getcwd()
    for folder in subfolders:
        os.chdir(folder)
        create_template(studio_url=studio_url, secure_mode=secure_mode)
        os.chdir(curr_dir)


def create_apps(folder='.', studio_url=[], secure_mode=True):
    subfolders = [f.path for f in os.scandir(folder) if f.is_dir()]
    curr_dir = os.getcwd()
    for folder in subfolders:
        os.chdir(folder)
        create_app(studio_url=studio_url, secure_mode=secure_mode)
        os.chdir(curr_dir)


def create_app(settings="config.json",
               chart_archive="chart",
               logo="logo.png",
               studio_url=[],
               secure_mode=True):

    conf = {
        'STACKN_URL': studio_url,
        'STACKN_SECURE': secure_mode
    }
    conf, status = stackn.auth.get_config(conf, required=['STACKN_URL'])
    if not status:
        print("Failed to get current STACKn configuration file.")
        return False

    auth_header, conf = get_auth_header(conf)
    if not auth_header:
        return False

    chart_uid = str(uuid.uuid1().hex)
    res = subprocess.run(
        ['tar', '-C', chart_archive, '-czvf', chart_uid, '.'], stdout=subprocess.PIPE)
    file_ob = {'chart': open(chart_uid, 'rb'), 'logo': open(logo, 'rb')}

    ftable = open(settings, 'r')
    config = json.load(ftable)
    settings = config['settings']
    table_field = config['table_field']
    description = config['description']
    name = config['name']
    slug = config['slug']
    category = config['category']
    access = 'public'
    if 'access' in config:
        access = config['access']
    priority = 100
    if 'priority' in config:
        priority = config['priority']
    ftable.close()

    payload = {
        'name': name,
        'slug': slug,
        'cat': category,
        'description': description,
        'settings': json.dumps(settings),
        'table_field': json.dumps(table_field),
        'access': access,
        'priority': priority
    }

    endpoints = get_endpoints(conf['STACKN_URL'])
    url = endpoints['admin']['apps']  # .format(project[0]['id'])
    r = requests.post(url, headers=auth_header, files=file_ob,
                      data=payload, verify=conf['STACKN_SECURE'])

    os.system('rm {}'.format(chart_uid))

    if r:
        print("Created app {}.".format(name))
    else:
        print("Failed to create app {}.".format(name))
        print(r.status_code)
        print(r.text)
        print(r.reason)


def create_project(name,
                   description="",
                   repository="",
                   template="stackn-default",
                   studio_url=[],
                   secure_mode=True):

    conf = {
        'STACKN_URL': studio_url,
        'STACKN_SECURE': secure_mode
    }

    conf, status = stackn.auth.get_config(conf, required=['STACKN_URL'])

    if not status:
        print("Failed to get current STACKn configuration file.")
        return False

    auth_header, conf = get_auth_header(conf)
    if not auth_header:
        return False

    endpoints = get_endpoints(conf['STACKN_URL'])
    url = endpoints['projects']
    data = {'name': name, 'description': description,
            'repository': repository, 'template': template}
    res = requests.post(url, headers=auth_header, json=data,
                        verify=conf['STACKN_SECURE'])
    if res:
        print('Created project: '+name)
        conf['STACKN_PROJECT'] = name
        set_current(conf)
    else:
        print('Failed to create project.')
        print('Status code: {}'.format(res.status_code))
        print(res.text)


def create_meta_resource(filename, studio_url, project, secure):
    conf = {
        'STACKN_URL': studio_url,
        'STACKN_PROJECT': project,
        'STACKN_SECURE': secure
    }
    conf, status = stackn.auth.get_config(conf, required=['STACKN_URL'])

    if not status:
        print("Failed to get current STACKn configuration file.")
        return False

    auth_header, conf = get_auth_header(conf)
    if not auth_header:
        return False

    project = get_projects(conf=conf['STACKN_URL'], params={
                           'name': conf['STACKN_PROJECT']}, auth_header=auth_header)
    if len(project) > 1:
        print('Found several matching projects.')
        return
    if not project:
        print("Project {} not found.".format(conf['STACKN_PROJECT']))
        return False

    project = project[0]
    endpoints = get_endpoints(conf['STACKN_URL'])
    url = endpoints['resources'].format(project['id'])
    try:
        fin = open(filename, 'r')
        app_data = json.load(fin)
    except:
        print("Failed to load JSON data from file {}.".format(filename))

    res = requests.post(url, headers=auth_header,
                        json=app_data, verify=conf['STACKN_SECURE'])
    if res:
        print('Created resource.')
    else:
        print('Failed to create resource.')
        print('Status code: {}'.format(res.status_code))
        print(res.text)


def create_object(model_name,
                  studio_url=[],
                  model_file='',
                  project_name=[],
                  release_type='minor',
                  version='',
                  object_type='model',
                  model_description=None,
                  model_card=None,
                  s3storage=None,
                  is_file=True,
                  secure_mode=True):
    """ Publish an object to Studio. """
    conf = {
        'STACKN_MODEL': model_name,
        'STACKN_URL': studio_url,
        'STACKN_PROJECT': project_name,
        'STACKN_RELEASE_TYPE': release_type,
        'STACKN_OBJECT_TYPE': object_type,
        'STACKN_S3': s3storage,
        'STACKN_SECURE': secure_mode
    }

    conf, status = stackn.auth.get_config(conf, required=['STACKN_URL',
                                                          'STACKN_PROJECT'])

    if not status:
        print("Failed to get current STACKn configuration file.")
        return False

    auth_header, conf = get_auth_header(conf)
    if not auth_header:
        return False

    project = get_projects(
        conf=conf, params={'name': conf['STACKN_PROJECT']}, auth_header=auth_header)
    if len(project) > 1:
        print('Found several matching projects.')
        return
    if not project:
        print("Project {} not found.".format(conf['STACKN_PROJECT']))
        return False

    project = project[0]
    if s3storage == None:
        s3storage = project['s3storage']
        print("S3 storage set to: {}".format(s3storage))
    else:
        # TODO: Fetch S3 settings from Studio...
        print("Passing S3 storage as an option is not implemented yet.")
        s3storage = None

    if s3storage == None:
        print("S3 storage not set.")
        return False

    model_uid = str(uuid.uuid1().hex)
    building_from_current = False

    if model_file == "":
        building_from_current = True
        model_file = '{}.tar.gz'.format(model_uid)
        f = open(model_file, 'w')
        f.close()
        res = subprocess.run(['tar', '--exclude={}'.format(model_file),
                             '-czvf', model_file, '.'], stdout=subprocess.PIPE)

    if model_card == "" or model_card == None:
        model_card_html_string = ""
    else:
        with open(model_card, 'r') as f:
            model_card_html_string = f.read()

    status = stackn.s3.set_artifact(model_uid,
                                    model_file,
                                    'models',
                                    s3storage,
                                    is_file=is_file,
                                    secure_mode=secure_mode)

    if not status:
        print("Failed to upload model to S3 storage")
        return False

    model_data = {"uid": model_uid,
                  "name": model_name,
                  "release_type": release_type,
                  "version": version,
                  "description": model_description,
                  "model_card": model_card_html_string,
                  "object_type": object_type}

    endpoints = get_endpoints(conf['STACKN_URL'])
    url = endpoints['models'].format(project['id'])
    r = requests.post(url, json=model_data,
                      headers=auth_header, verify=secure_mode)

    if not _check_status(r, error_msg="Failed to create model."):
        # Delete model object from storage.
        repo.delete_artifact(model_uid)
        return False

    if building_from_current:
        # Delete temporary archive file.
        os.system('rm {}'.format(model_file))

    print('Released model: {}, release_type: {}'.format(model_name, release_type))

    return True


def create_appinstance(studio_url=[], project=[], data={}, secure_mode=True):
    conf = {
        "STACKN_URL": studio_url,
        "STACKN_PROJECT": project,
        "STACKN_SECURE": secure_mode
    }

    conf, auth_header, url = setup_project_endpoint_call(conf, 'appinstances')

    if not conf or not auth_header or not url:
        print("Failed to set up project API endpoint call.")
        return False
    res = requests.post(url, headers=auth_header, data=data,
                        verify=conf['STACKN_SECURE'])
    print(res.text)


# Delete functions

def delete_app(name, studio_url=[], project=[], secure=True):

    conf = {
        "STACKN_URL": studio_url,
        "STACKN_PROJECT": project,
        "STACKN_SECURE": secure
    }

    conf, auth_header, url = setup_project_endpoint_call(conf, 'appinstances')

    if not conf or not auth_header or not url:
        print("Failed to set up project API endpoint call.")
        return False

    params = {
        "name": name
    }

    apps = call_project_endpoint('appinstances', conf, params=params)

    if not apps:
        return False

    if len(apps) > 1:
        print("Found multiple apps with that name, deleting all...")
    elif len(apps) == 0:
        print("Found no app with that name, aborting...")
        return False

    for app in apps:
        ai_id = app['id']
        tmp_url = url+str(ai_id)+'/'
        res = requests.delete(tmp_url, headers=auth_header,
                              verify=conf['STACKN_SECURE'])
        if res:
            print("Deleted app: {}".format(name))
        else:
            print("Failed to delete app.")
            print('Status code: {}'.format(res.status_code))
            print(res.text)


def delete_object(name, version=None, studio_url=[], project=[], secure=True):
    if version:
        params = {'name': name, 'version': version}
    else:
        params = {'name': name}

    conf = {
        "STACKN_URL": studio_url,
        "STACKN_PROJECT": project,
        "STACKN_SECURE": secure
    }

    conf, auth_header, url = setup_project_endpoint_call(conf, 'models')

    if not conf or not auth_header or not url:
        print("Failed to setup project API endpoint.")
        return False

    objects = call_project_endpoint('models', conf=conf, params=params)

    if objects == False:
        return False
    elif len(objects) == 0:
        print("No model objects found with the given name and/or version.")

    for obj in objects:
        tmp_url = '{}{}/'.format(url, obj['id'])
        res = requests.delete(tmp_url, headers=auth_header,
                              verify=conf['STACKN_SECURE'])
        if res:
            print("Deleted model object: {}".format(name))
        else:
            print("Failed to delete model object.")
            print('Status code: {}'.format(res.status_code))
            print(res.text)


def delete_project(name, studio_url=[], secure=True):

    conf = {
        "STACKN_URL": studio_url,
        "STACKN_SECURE": secure,
        "STACKN_PROJECT": name
    }

    conf, auth_header, url = setup_project_endpoint_call(conf, 'project_del')

    if not conf or not auth_header or not url:
        print("Failed to set up project API endpoint")
        return False

    res = requests.delete(url, headers=auth_header,
                          verify=conf['STACKN_SECURE'])

    if res:
        print("Deleted project: {}".format(name))
    else:
        print("Failed to delete project.")
        print('Status code: {}'.format(res.status_code))
        print(res.text)


def delete_meta_resource(resource_type, name, project=[], studio_url=[], secure=True):

    conf = {
        "STACKN_PROJECT": project,
        "STACKN_URL": studio_url,
        "STACKN_SECURE": secure
    }

    conf, auth_header, url = setup_project_endpoint_call(conf, resource_type)

    if not conf or not auth_header or not url:
        print("Failed to setup project API endpoint.")
        return False

    params = {
        "name": name
    }

    prj_endpts = call_project_endpoint(resource_type, conf=conf, params=params)

    if prj_endpts == False:
        return False
    elif len(prj_endpts) == 0:
        print("No {}: \'{}\' associated with the current project".format(
            resource_type, name))
        return False
    elif len(prj_endpts) > 1:
        print("Found multiple resources with the passed name.")
        return False

    endpt = prj_endpts[0]

    if resource_type == "mlflow" or resource_type == "s3":
        url = '{}{}/'.format(url, endpt['name'])
    else:
        url = '{}{}/'.format(url, endpt['id'])

    res = requests.delete(url, headers=auth_header,
                          verify=conf['STACKN_SECURE'])
    if res:
        print("Deleted {}: {}".format(resource_type, name))
    else:
        print("Failed to delete {}.".format(resource_type))
        print('Status code: {}'.format(res.status_code))
        print(res.text)

# Set Function


def set_current(conf):
    res = stackn.auth._set_current(conf)
    if not res:
        print('Failed to set current remote URL/project.')
        if 'STACKN_URL' in conf:
            print(conf['STACKN_URL'])
        if 'STACKN_PROJECT' in conf:
            print(conf['STACKN_PROJECT'])
    else:
        pass

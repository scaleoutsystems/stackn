import os
import json
import uuid
import requests
import subprocess
import urllib.parse

import stackn.auth
import stackn.s3
import stackn.error_msg


def _check_status(r, error_msg="Failed"):
    if (r.status_code < 200 or r.status_code > 299):
        print(error_msg)
        print('Returned status code: {}'.format(r.status_code))
        print('Reason: {}'.format(r.reason))
        print(r.text)
        return False
    else:
        return True 

def get_endpoints(studio_url):
    endpoints = dict()
    if (not 'http://' in studio_url) and (not 'https://' in studio_url):
        studio_url = 'https://'+studio_url
    base = studio_url.strip('/')+'/api'
    endpoints['models'] = base+'/projects/{}/models/'
    endpoints['resources'] = base+'/projects/{}/resources/'
    endpoints['appinstances'] = base+'/projects/{}/appinstances/'
    endpoints['objecttypes'] = base+'/projects/{}/objecttype'
    endpoints['members'] = base+'/projects/{}/members/'
    endpoints['flavors'] = base+'/projects/{}/flavors/'
    endpoints['environments'] = base+'/projects/{}/environments/'
    endpoints['s3'] = base+'/projects/{}/s3/'
    endpoints['mlflow'] = base+'/projects/{}/mlflow/'
    endpoints['releasenames'] = base+'/projects/{}/releasenames/'
    endpoints['projects'] = base+'/projects/'
    return endpoints

def get_auth_headers(conf):
    conf, status = stackn.auth.get_token(conf)
    if not status:
        return False, False
    auth_headers = {"Authorization": "Token {}".format(conf['STACKN_ACCESS_TOKEN'])}
    return auth_headers, conf

def get_remote():
    conf, status = stackn.auth.get_config()
    keys = stackn.auth._get_remote(conf)
    return keys

def get_current():
    res = {'STACKN_URL': False, 'STACKN_PROJECT': False}
    conf, status = stackn.auth.get_config()
    if not status:
        print("Failed to get current STACKn and project.")
    else:
        if 'STACKN_URL' in conf:
            res['STACKN_URL'] = conf['STACKN_URL']
        if 'STACKN_PROJECT' in conf:
            res['STACKN_PROJECT'] = conf['STACKN_PROJECT']
    
    return res

def get_projects(conf={}, params=[], auth_headers=[]):
    conf, status = stackn.auth.get_config(conf)
    if not status:
        print('Cannot list projects.')
        return False
    if not auth_headers:
        auth_headers, conf = get_auth_headers(conf)
    endpoints = get_endpoints(conf['STACKN_URL'])
    url = endpoints['projects']
    if params:
        r = requests.get(url, headers=auth_headers, params=params, verify=conf['STACKN_SECURE'])
    else:
        r = requests.get(url, headers=auth_headers, verify=conf['STACKN_SECURE'])
    if r:
        projects = json.loads(r.content)
        return projects
    else:
        print("Fetching projects failed.")
        print('Returned status code: {}'.format(r.status_code))
        print('Reason: {}'.format(r.reason))
        return None

def call_project_endpoint(name, conf={}, params=[]):
    conf, status = stackn.auth.get_config(conf)
    auth_headers, conf = get_auth_headers(conf)
    endpoints = get_endpoints(conf['STACKN_URL'])
    if conf['STACKN_PROJECT']:
        project = get_projects(conf, params={'name': conf['STACKN_PROJECT']})
    else:
        print("No project name specified.")
        return False
    if len(project)>1:
        print('Found several matching projects.')
        return
    if not project:
        print("Project {} not found.".format(conf['STACKN_PROJECT']))
        return False
    project = project[0]
    url = endpoints[name].format(project['id'])
    if params:
        r = requests.get(url, headers=auth_headers, params=params, verify=conf['STACKN_SECURE'])
    else:
        r = requests.get(url, headers=auth_headers, verify=conf['STACKN_SECURE'])
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
        print("Missing required input (studio URL, project name).")
        return False

    auth_headers, conf = get_auth_headers(conf)
    if not auth_headers:
        print("Failed to set authentication headers.")
        return False

    project = get_projects(conf=conf['STACKN_URL'], params={'name': conf['STACKN_PROJECT']}, auth_headers=auth_headers)
    if len(project)>1:
        print('Found several matching projects.')
        return
    if not project:
        print("Project {} not found.".format(conf['STACKN_PROJECT']))
        return False

    project = project[0]
    endpoints = get_endpoints(conf['STACKN_URL'])
    url = endpoints[endpoint_type].format(project['id'])
    return conf, auth_headers, url

def create_project(name, 
                   description="",
                   repository="",
                   template="stackn-default",
                   studio_url=[],
                   secure_mode=True):
    # Get STACKn config
    conf = {
        'STACKN_URL': studio_url,
        'STACKN_SECURE': secure_mode
    }

    conf, status = stackn.auth.get_config(conf, required=['STACKN_URL'])

    if not status:
        print("Missing required input (studio URL, project name).")
        return False

    auth_headers, conf = get_auth_headers(conf)
    if not auth_headers:
        print("Failed to set authentication headers.")
        return False
    
    endpoints = get_endpoints(conf['STACKN_URL'])
    url = endpoints['projects']
    data = {'name': name, 'description': description, 'repository': repository, 'template': template}
    res = requests.post(url, headers=auth_headers, json=data, verify=conf['STACKN_SECURE'])
    if res:
        print('Created project: '+name)
        # print('Setting {} as the active project.'.format(name))
        # self.set_project(name)
    else:
        print('Failed to create project.')
        print('Status code: {}'.format(res.status_code))
        print(res.text)

def create_resource(filename, studio_url, project, secure):
    conf = {
        'STACKN_URL': studio_url,
        'STACKN_PROJECT': project,
        'STACKN_SECURE': secure
    }
    conf, status = stackn.auth.get_config(conf, required=['STACKN_URL'])

    if not status:
        print("Missing required input (studio URL, project name).")
        return False

    auth_headers, conf = get_auth_headers(conf)
    if not auth_headers:
        print("Failed to set authentication headers.")
        return False

    project = get_projects(conf=conf['STACKN_URL'], params={'name': conf['STACKN_PROJECT']}, auth_headers=auth_headers)
    if len(project)>1:
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
    
    res = requests.post(url, headers=auth_headers, json=app_data, verify=conf['STACKN_SECURE'])
    if res:
        print('Created resource.')
    else:
        print('Failed to create resource.')
        print('Status code: {}'.format(res.status_code))
        print(res.text)

def create_object(model_name,
                  studio_url=[],
                  model_file="",
                  project_name=[],
                  release_type='minor',
                  object_type='model',
                  model_description=None,
                  s3storage=None,
                  is_file=True,
                  secure_mode=True):

    """ Publish an object to Studio. """

    # Get STACKn config
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
        print("Missing required input (studio URL, project name).")
        return False

    auth_headers, conf = get_auth_headers(conf)
    if not auth_headers:
        print("Failed to set authentication headers.")
        return False

    project = get_projects(conf=conf['STACKN_URL'], params={'name': conf['STACKN_PROJECT']}, auth_headers=auth_headers)
    if len(project)>1:
        print('Found several matching projects.')
        return
    if not project:
        print("Project {} not found.".format(conf['STACKN_PROJECT']))
        return False

    project = project[0]
    if s3storage == None:
        s3storage = project['s3storage']
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
        res = subprocess.run(['tar', '--exclude={}'.format(model_file), '-czvf', model_file, '.'], stdout=subprocess.PIPE)

    # # Upload model.
    status = stackn.s3.set_artifact(model_uid,
                                    model_file,
                                    'models',
                                    s3storage,
                                    is_file=is_file,
                                    secure_mode=secure_mode)

    if not status:
        print("Failed to upload model to S3 storage")
        return False
    
    # Register model in STACKn
    model_data = {"uid": model_uid,
                  "name": model_name,
                  "release_type": release_type,
                  "description": model_description,
                  "object_type": object_type}

    endpoints = get_endpoints(conf['STACKN_URL'])
    url = endpoints['models'].format(project['id'])

    r = requests.post(url, json=model_data, headers=auth_headers, verify=secure_mode)
    if not _check_status(r, error_msg="Failed to create model."):
        # Delete model object from storage.
        repo.delete_artifact(model_uid)
        return False

    if building_from_current:
        # Delete temporary archive file.
        os.system('rm {}'.format(model_file))
    print('Released model: {}, release_type: {}'.format(model_name, release_type))
    return True

def create_releasename(name, studio_url, project, secure):
    conf = {
        'STACKN_URL': studio_url,
        'STACKN_PROJECT': project,
        'STACKN_SECURE': secure
    }
    conf, auth_headers, url = setup_project_endpoint_call(conf, 'releasenames')
    params = {
        "name": name
    }
    res = requests.post(url, json=params, headers=auth_headers, verify=conf['STACKN_SECURE'])
    if res:
        print(res.text)
    else:
        print("Failed to create release name.")
        print('Status code: {}'.format(res.status_code))
        print(res.text)


def delete_app(name, studio_url=[], project=[], secure=True):
    conf = {
        "STACKN_URL": studio_url,
        "STACKN_PROJECT": project,
        "STACKN_SECURE": secure
    }
    conf, auth_headers, url = setup_project_endpoint_call(conf, 'appinstances')
    params = {
        "name": name
    }
    apps = call_project_endpoint('appinstances', params=params)
    if len(apps) > 1:
        print("Found multiple apps with that name, deleting all...")
    if len(apps) == 0:
        print("Found no app with that name, aborting...")
        return False

    for app in apps:
        ai_id = app['id']
        tmp_url = url+str(ai_id)+'/'
        res = requests.delete(tmp_url, headers=auth_headers, verify=conf['STACKN_SECURE'])
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
    conf, auth_headers, url = setup_project_endpoint_call(conf, 'models')
    objects = call_project_endpoint('models', conf=conf, params=params)
    # models  = self.get_models(self.project['id'], params)
    if not objects:
        print("No objects found with the given name and/or version.")
    for obj in objects:
        tmp_url = '{}{}/'.format(url, obj['id'])
        res = requests.delete(tmp_url, headers=auth_headers, verify=conf['STACKN_SECURE'])
        if res:
            print("Deleted object: {}".format(name))
        else:
            print("Failed to delete object.")
            print('Status code: {}'.format(res.status_code))
            print(res.text)

def delete_project(name, studio_url=[], secure=True):
    conf = {
        "STACKN_URL": studio_url,
        "STACKN_SECURE": secure
    }
    conf, auth_headers, url = setup_project_endpoint_call(conf, 'project_del')
    res = requests.delete(url, headers=auth_headers, verify=conf['STACKN_SECURE'])
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
    conf, auth_headers, url = setup_project_endpoint_call(conf, resource_type)
    params = {
        "name": name
    }
    envs = call_project_endpoint(resource_type, conf=conf, params=params)
    if len(envs) == 0:
        print("Didn't find environment with that name.")
        return False
    elif len(envs) > 1:
        print("Found multiple environments with that name.")
        return False
    
    env = envs[0]
    url = '{}{}/'.format(url, env['id'])
    res = requests.delete(url, headers=auth_headers, verify=conf['STACKN_SECURE'])
    if res:
        print("Deleted {}: {}".format(resource_type, name))
    else:
        print("Failed to delete {}.".format(resource_type))
        print('Status code: {}'.format(res.status_code))
        print(res.text)



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
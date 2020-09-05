import os
import scaleout.auth as sauth
from scaleout.utils.file import dump_to_file, load_from_file
import subprocess
import requests
import json
import uuid
from urllib.parse import urljoin

def _check_status(r,error_msg="Failed"):
    if (r.status_code < 200 or r.status_code > 299):
        print(error_msg)
        print('Returned status code: {}'.format(r.status_code))
        print('Reason: {}'.format(r.reason))
        print(r.text)
        return False
    else:
        return True 



class StudioClient():

    def __init__(self, config=None):
        self.found_project = False
        self.access_token, self.token_config = sauth.get_token()
        self.api_url = urljoin(self.token_config['studio_url'], '/api')
        self.auth_headers = {'Authorization': 'Token {}'.format(self.access_token)}

        # Fetch and set all active API endpoints
        self.get_endpoints()

        self.stackn_config, load_status = sauth.get_stackn_config()
        if not load_status:
            print('Failed to load stackn config')

        self.project = []
        self.project_slug = []
        active_dir = self.stackn_config['active']
        if 'active_project' in self.stackn_config:
            project_dir = os.path.expanduser('~/.scaleout/'+active_dir+'/projects')
            self.project, load_status = load_from_file(self.stackn_config['active_project'], project_dir)
            if load_status:
                self.found_project = True
                self.project_slug = self.project['slug']
                # else:
                #     print('Could not load project config for '+self.stackn_config['active_project'])
            else:
                print('You must set an active valid project.')
        # self.project = self.get_projects({'slug': self.project_slug})
        if not self.project:
            print('Did not find existing config')
            self.project_id = -1
        else:
            self.project_id = self.project['id']
            self.project_slug = self.project['slug']

    def get_endpoints(self):
        # endpoints = self.list_endpoints()
        self.endpoints = dict()
        self.endpoints['models'] = self.api_url+'/projects/{}/models'
        self.endpoints['labs'] = self.api_url + '/projects/{}/labs'
        self.reports_api = self.api_url+'/reports'
        self.endpoints['projects'] = self.api_url+'/projects/'
        self.generators_api = self.api_url+'/generators' #endpoints['generators']
        self.endpoints['deploymentInstances'] = self.api_url+'/deploymentInstances/'
        self.deployment_definition_api = self.api_url+'/deploymentDefinitions' #endpoints['deploymentDefinitions']

    def _get_repository_conf(self):
        """ Return the project minio keys. """
        #TODO: If we have multiple repositories configured, studio, minio, s3, etc, we 
        # neet to supply repository name.
        project = self.project
        # project = self.get_projects({'slug': self.project_slug})
        # print(project)
        # TODO: Obtain port and host from Studio backend API, this assumes a certain naming schema  
        data = {
            'minio_host': '{}-minio.{}'.format(self.project_slug,
                                               self.token_config['studio_url'].replace('https://', '').replace('http://', '')),
            'minio_port': 9000,
            'minio_access_key': self.decrypt_key(project['project_key']),
            'minio_secret_key': self.decrypt_key(project['project_secret']),
            'minio_secure_mode': True,
        }
        return data

    def decrypt_key(self, encrypted_key):
        import base64

        base64_bytes = encrypted_key.encode('ascii')
        result = base64.b64decode(base64_bytes)
        return result.decode('ascii')

    def get_repository(self):
        from scaleout.repository.helpers import get_repository as gr
        repository_config = self._get_repository_conf()
        repo = gr(repository_config)
        return repo

    def list_endpoints(self):
        """ List api endpoints """

        # TODO: "studio" subdomain hardcoded here
        #url = "https://studio.{}/api/".format(self.config['so_domain_name'])
    
        r = requests.get(self.api_url, headers=self.auth_headers)

        if (r.status_code < 200 or r.status_code > 299):
            print("Endpoint list failed.")
            print('Returned status code: {}'.format(r.status_code))
            print('Reason: {}'.format(r.reason))
            return None
        else:
            return json.loads(r.content)


    ### Projects api  ####
    
    def create_project(self, name, description, repository):
        url = self.endpoints['projects']+'create_project/'
        data = {'name': name, 'description': description, 'repository': repository}
        res = requests.post(url, headers=self.auth_headers, json=data)
        if res:
            print('Created project: '+name)
            print('Setting {} as the active project.'.format(name))
            self.set_project(name)
        else:
            print('Failed to create project.')
            print('Status code: {}'.format(res.status_code))
            print(res.text)


    def list_projects(self):
        """ List all projects a user has access to. """
        url = self.endpoints['projects']
        r = requests.get(url, headers=self.auth_headers)
        if (r.status_code < 200 or r.status_code > 299):
            print("List projects failed.")
            print('Returned status code: {}'.format(r.status_code))
            print('Reason: {}'.format(r.reason))
            return None
        else:
            return json.loads(r.content)

    def get_projects(self, params=[]):
        url = self.endpoints['projects']
        if params:
            r = requests.get(url, headers=self.auth_headers, params=params)
        else:
            r = requests.get(url, headers=self.auth_headers)
        if r:
            projects = json.loads(r.content)
            if len(projects) == 1:
                projects = projects[0]
            return projects
        else:
            print("Fetching projects failed.")
            print('Returned status code: {}'.format(r.status_code))
            print('Reason: {}'.format(r.reason))
            return None

    def set_project(self, project_name):
        # Set active project
        stackn_config, load_status = sauth.get_stackn_config()
        if not load_status:
            print('Failed to load STACKn config.')
            return False
        active_dir = stackn_config['active']
        project_dir = os.path.expanduser('~/.scaleout/'+active_dir+'/projects')
        proj_path = project_dir+'/'+project_name+'.json'
        # Update STACKN config
        stackn_config['active_project'] = project_name
        sauth.write_stackn_config(stackn_config)
        if not os.path.exists(proj_path):
            if not os.path.exists(project_dir):
                os.makedirs(project_dir)
            # Fetch and write project settings file
            print('Writing new project config file.')
            project = self.get_projects({'name': project_name})
            status = dump_to_file(project, project_name, project_dir)
            if not status:
                print('Failed to set project -- could not write to config.')
            

    def create_deployment_definition(self, name, filepath, path_predict=''):

        if filepath[-6:] != 'tar.gz':
            print('Deployment definition should have extension tar.gz')
            return None

        bucket = 'deploy'
        # Create unique file name
        filename = uuid.uuid1().hex+'.tar.gz'
        repo = self.get_repository()
        repo.set_artifact(filename, filepath, is_file=True, bucket=bucket)
        depde_data = {"project": self.project_id,
                      "name": name,
                      "bucket": bucket,
                      "filename": filename,
                      "path_predict": path_predict}

        url = self.deployment_definition_api
        r = requests.post(url, json=depde_data, headers=self.auth_headers)
        status1 = _check_status(r, error_msg='Failed to create deployment definition')
        
        if not status1:
            repo.delete_artifact(filename, bucket)
            return False

        url_build = url+'build_definition/'
        r = requests.post(url_build, json={'name':name}, headers=self.auth_headers)
        status2 = _check_status(r, error_msg='Failed to start building of definition.')
        if not status2:
            repo.delete_artifact(filename, bucket)
            # TODO: Delete from database as well.
            return False

        print('Created deployment definition: {}'.format(name))
        return True
            

    

    def get_deployment_definition(self, name):
        url = os.path.join(self.deployment_definition_api, '?name={}'.format(name))
        r = requests.get(url, headers=self.auth_headers)
        if _check_status(r,error_msg="Get deployment definition failed."):
            return json.loads(r.content)
        else:
            return []

    ### Datasets API ###


    def list_datasets(self):
        # TODO: This only lists datasets in Minio, not the ones in Studio (Django-managed). 
        # We should here use the Studio datasets api when it is available
        from minio.error import NoSuchBucket
        repo = self.get_repository()
        try:
            objs = repo.client.list_objects(bucket_name="dataset")
        except NoSuchBucket as e:
            print("The datasets repository has not been initialized yet.", e)
        return objs


    ### Models API ###

    

    def show_model(self, model_id=None):
        """ Get all metadata associated with a model. """
        try:
            for model in self.get_models():
                if model['uid'] == model_id:
                    return model
        except:
            raise
        
        print("No model found with id: ", model_id)
        return None

    def create_model(self, model_file, model_name, release_type='', model_description=None,is_file=True):
        """ Publish a model to Studio. """

        import uuid
        model_uid = str(uuid.uuid1().hex)
        building_from_current = False
        if model_file == "":
            building_from_current = True
            model_file = '{}.tar.gz'.format(model_uid)
            # Find latest serialized model
            path = 'models'
            os.chdir(path)
            files = sorted(os.listdir(os.getcwd()), key=os.path.getmtime)
            os.chdir('../')
            newest = ''
            if files:
                newest = os.path.join('models', files[-1])
            print(newest)
            res = subprocess.run(['tar', 'czvf', model_file, newest, 'requirements.txt', 'src'], stdout=subprocess.PIPE)

        repo = self.get_repository()
        repo.bucket = 'models'
        # Upload model.
        repo.set_artifact(model_uid, model_file, is_file)
 
        model_data = {"uid": model_uid,
                      "name": model_name,
                      "release_type": release_type,
                      "description": model_description}

        url = self.endpoints['models'].format(self.project['id'])+'/'
        # url = url.replace('http:', 'https:')

        r = requests.post(url, json=model_data, headers=self.auth_headers)
        if not _check_status(r, error_msg="Failed to create model."):
            repo.delete_artifact(model_uid)
            return False

        if building_from_current:
            os.system('rm {}'.format(model_file))
        print('Released model: {}, release_type: {}'.format(model_name, release_type))
        return True

    def deploy_model(self, model_name, model_version, deploy_context):

        url = self.endpoints['deploymentInstances']+'build_instance/'
        bd_data = {"project": self.project['id'], "name": model_name, "version": model_version, "depdef": deploy_context}
        r = requests.post(url, json=bd_data, headers=self.auth_headers)
        if not r:
            print('Failed to deploy model.')
            print('Status code: {}'.format(r.status_code))
            msg = r.text
            if len(msg) > 500:
                msg = msg[0:500]
            print('Reason: {}'.format(msg))
        # if not _check_status(r, error_msg="Failed to create deployment."):
        #     # Delete registered deployment instance from db
        #     return False

        print('Created deployment: {}'.format(model_name))
        return True

    def update_deployment(self, name, version, params):
        url = self.endpoints['deploymentInstances']+'update_instance/'
        params['name'] = name
        params['version'] = version
        r = requests.post(url, headers=self.auth_headers, json=params)
        if r:
            print('Updated deployment: ')
            print(params)
        else:
            print('Failed to update deployment.')
            print('Status code: {}'.format(r.status_code))
            print(r.text)
    
    def create_list(self, resource):
        if resource == 'deploymentInstances':
            if self.found_project:
                return self.list_deployments()
            else:
                return []
        if resource == 'models':
            if self.found_project:
                models = self.get_models(self.project['id'])
                return models
            else:
                return []

        url = self.endpoints[resource]

        r = requests.get(url, headers=self.auth_headers)
        if not _check_status(r, error_msg="Failed to list {}.".format(resource)):
            return False
        else:
            return json.loads(r.content)

    def get_models(self, project_id, params=[]):
        url = self.endpoints['models'].format(project_id)
        r = requests.get(url, headers=self.auth_headers, params=params)
        try:
            models = json.loads(r.content)
        except Exception as err:
            print('Failed to list models.')
            print('Status code: {}'.format(r.status_code))
            print('Message: {}'.format(r.text))
            print('Error: {}'.format(err))
            return []
        return models

    def get_lab_sessions(self, params=[]):
        url = self.endpoints['labs'].format(self.project['id']) + '/'
        r = requests.get(url, headers=self.auth_headers, params=params)
        try:
            labs = json.loads(r.content)
        except Exception as err:
            print('Failed to list Lab Sessions.')
            print('Status code: {}'.format(r.status_code))
            print('Message: {}'.format(r.text))
            print('Error: {}'.format(err))
            return []
        return labs
    
    def get_model(self, project_id, model_id):
        url = '{}/{}'.format(self.endpoints['models'].format(project_id),model_id)
        r = requests.get(url, headers=self.auth_headers)
        model = json.loads(r.content)
        return model
        
    def list_deployments(self):
        url = self.endpoints['deploymentInstances']
        r = requests.get(url, headers=self.auth_headers, params={'project':self.project['id']})
        if not _check_status(r, error_msg="Failed to fetch deployments"):
            return False
        deployments = json.loads(r.content)
        depjson = []
        for deployment in deployments:

            model = self.get_model(self.project['id'], deployment['model'])
            dep = {'name': model['name'],
                   'version': model['version'],
                   'endpoint': deployment['endpoint'],
                   'created_at': deployment['created_at']}
            depjson.append(dep)
        return depjson

    def get_deployment(self, params):
        url = self.endpoints['deploymentInstances']
        r = requests.get(url, params=params, headers=self.auth_headers)
        return json.loads(r.content)

    def delete_model(self, name, version=None):
        if version:
            params = {'name': name, 'version': version}
        else:
            params = {'name': name}
        models  = self.get_models(self.project['id'], params)
        for model in models:
            url = '{}/{}'.format(self.endpoints['models'].format(self.project['id']), model['id'])
            r = requests.delete(url, headers=self.auth_headers)
            if not _check_status(r, error_msg="Failed to delete model {}:{}.".format(name, version)):
                pass
            else:
                print("Deleted model {}:{}.".format(name, model['version']))

    def delete_deployment(self, name, version=None):
        if version:
            params = {'name': name, 'version': version}
        else:
            params = {'name': name}
        models  = self.get_models(self.project['id'], params)
        for model in models:
            deployment = self.get_deployment({'model':model['id'],'project':self.project['id']})
            if deployment:
                deployment = deployment[0]
                url = self.endpoints['deploymentInstances']+'destroy'
                r = requests.delete(url, headers=self.auth_headers, params=params)
                if not _check_status(r, error_msg="Failed to delete deployment {}:{}.".format(model['name'], model['version'])):
                    pass
                else:
                    print("Deleted deployment {}:{}.".format(model['name'], model['version']))

    def add_members(self, users):
        url = self.endpoints['projects'] + 'add_members/'
        data = {'slug': self.project_slug, 'selected_users': users}

        r = requests.post(url, headers=self.auth_headers, json=data)

        if r:
            print('New members: ' + users)
            print('Successfully added the selected users as members to project {}.'.format(self.project['name']))
        else:
            print('Failed to add members to project {}.'.format(self.project['name']))
            print('Status code: {}'.format(r.status_code))
            print('Reason: {}'.format(r.reason))

    def create_session(self, flavor_slug, environment_slug):
        url = self.endpoints['labs'].format(self.project['id']) + '/'
        data = {'flavor': flavor_slug, 'environment': environment_slug}

        r = requests.post(url, headers=self.auth_headers, json=data)

        if r:
            print('Successfully created Lab Session.')
            print('Flavor: ' + flavor_slug)
            print('Environment: ' + environment_slug)
        else:
            print('Failed to create Lab Session.')
            print('Status code: {}'.format(r.status_code))
            print('Reason: {} - {}'.format(r.reason, r.text))

if __name__ == '__main__':

    client = StudioClient()
    p = client.get_projects({'slug': 'Test'})
    print("Project:", p)
    e = client.list_endpoints()
    print("Endpoints: ", e)
    data = client._get_repository_conf()
    print("Minio settings: ", data)

    print(client.token)


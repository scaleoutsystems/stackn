import os
import scaleout.auth as sauth
from scaleout.utils.file import dump_to_file, load_from_file
import subprocess
import requests
import json
import uuid
from urllib.parse import urljoin
from datetime import datetime
from .details import get_run_details

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
        
        self.secure_mode = True
        if 'secure' in self.stackn_config:
            self.secure_mode = self.stackn_config['secure']
        if self.secure_mode == False:
            print("WARNING: Running in insecure mode.")
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # self.project = self.get_projects({'slug': self.project_slug})
        if not self.project:
            print('Did not find active project in config')
            self.project_id = -1
        else:
            self.project_id = self.project['id']
            self.project_slug = self.project['slug']

        self.access_token, self.token_config = sauth.get_token(secure=self.secure_mode)
        if self.token_config['studio_url'][-1] == '/':
            self.token_config['studio_url'] = self.token_config['studio_url'][:-1]
        self.api_url = urljoin(self.token_config['studio_url'], '/api')
        self.auth_headers = {'Authorization': 'Token {}'.format(self.access_token)}
        # Fetch and set all active API endpoints
        self.get_endpoints()

    def get_endpoints(self):
        self.endpoints = dict()
        self.endpoints['models'] = self.api_url+'/projects/{}/models'
        self.endpoints['modellogs'] = self.api_url+'/projects/{}/modellogs'
        self.endpoints['metadata'] = self.api_url+'/projects/{}/metadata'
        self.endpoints['labs'] = self.api_url + '/projects/{}/labs'
        self.endpoints['members'] = self.api_url+'/projects/{}/members'
        self.endpoints['dataset'] = self.api_url+'/projects/{}/dataset'
        self.endpoints['volumes'] = self.api_url+'/projects/{}/volumes/'
        self.endpoints['jobs'] = self.api_url+'/projects/{}/jobs/'
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
            'minio_secure_mode': self.secure_mode,
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
    
        r = requests.get(self.api_url, headers=self.auth_headers, verify=self.secure_mode)

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
        res = requests.post(url, headers=self.auth_headers, json=data, verify=self.secure_mode)
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
        r = requests.get(url, headers=self.auth_headers, verify=self.secure_mode)
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
            r = requests.get(url, headers=self.auth_headers, params=params, verify=self.secure_mode)
        else:
            r = requests.get(url, headers=self.auth_headers, verify=self.secure_mode)
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
        r = requests.get(url, headers=self.auth_headers, verify=self.secure_mode)
        if _check_status(r,error_msg="Get deployment definition failed."):
            return json.loads(r.content)
        else:
            return []

    def get_members(self):
        url = self.endpoints['members'].format(self.project['id']) + '/'
        r = requests.get(url, headers=self.auth_headers, verify=self.secure_mode)
        try:
            members = json.loads(r.content)
        except Exception as err:
            print('Failed to list Lab Sessions.')
            print('Status code: {}'.format(r.status_code))
            print('Message: {}'.format(r.text))
            print('Error: {}'.format(err))
            return []
        return members

    ### Jobs API ###
    def get_jobs(self, data={}):
        url = self.endpoints['jobs'].format(self.project['id'])
        try:
            r = requests.get(url, headers=self.auth_headers, params=data, verify=self.secure_mode)
            jobs = json.loads(r.content)
            return jobs
        except Exception as err:
            print('Failed to list jobs.')
            print('Status code: {}'.format(r.status_code))
            print('Message: {}'.format(r.text))
            print('Error: {}'.format(err))
            return []

    def create_job(self, config):
        settings_file = open(config, 'r')
        job_config = json.loads(settings_file.read())
        url = self.endpoints['jobs'].format(self.project['id'])
        try:
            r = requests.post(url, headers=self.auth_headers, json=job_config, verify=self.secure_mode)
        except Exception as err:
            print('Failed to list jobs.')
            print('Status code: {}'.format(r.status_code))
            print('Message: {}'.format(r.text))
            print('Error: {}'.format(err))
            return []

    ### Volumes API ###

    def get_volumes(self, data={}):
        url = self.endpoints['volumes'].format(self.project['id'])
        try:
            r = requests.get(url, headers=self.auth_headers, params=data, verify=self.secure_mode)
            volumes = json.loads(r.content)
            return volumes
        except Exception as err:
            print('Failed to list volumes.')
            print('Status code: {}'.format(r.status_code))
            print('Message: {}'.format(r.text))
            print('Error: {}'.format(err))
            return []


    def create_volume(self, size, name):
        url = self.endpoints['volumes'].format(self.project['id'])
        data = {'name': name, 'size': size}
        r = requests.post(url, headers=self.auth_headers, json=data, verify=self.secure_mode)
        if r:
            print('Created volume: {}'.format(name))
        else:
            print('Failed to create volume.')
            print('Status code: {}'.format(r.status_code))
            print(r.text)

    def delete_volume(self, name):
        try:
            volume = self.get_volumes({"name": name, "project_slug": self.project['slug']})[0]
        except:
            print('Volume {} not found.'.format(name))
            return
        url = self.endpoints['volumes'].format(self.project['id'])+str(volume['id'])
        r = requests.delete(url, headers=self.auth_headers, verify=self.secure_mode)
        if r:
            print('Deleted volume: {}'.format(volume['name']))
        else:
            print('Failed to delete volume.')
            print('Status code: {}'.format(r.status_code))
            print(r.text)


    ### Datasets API ###

    def delete_dataset(self, name, version):
        dataset = self.get_dataset({"name":name, "version": version})[0]
        url = self.endpoints['dataset'].format(self.project['id']) + '/'+str(dataset['id'])
        r = requests.delete(url, headers=self.auth_headers, verify=self.secure_mode)
        if r:
            print('Deleted dataset: {}'.format(dataset['name']))
        else:
            print('Failed to delete dataset.')
            print('Status code: {}'.format(r.status_code))
            print(r.text)

    def create_dataset(self, name, release_type, filenames, directory=[], description='', bucket='dataset'):
        if not filenames:
            if not directory:
                print('You need to specify either files or a directory.')
                return []
            filenames = ''
            for root, dirs, files in os.walk(directory):
                for fname in files:
                    tmp_fn = os.path.join(root, fname)
                    filenames += tmp_fn+','

            if filenames == '':
                print('Directory is empty.')
                return []
            else:
                filenames = filenames[:-1]

        url = self.endpoints['dataset'].format(self.project['id']) + '/'
        payload = {
          "name": name,
          "release_type": release_type,
          "filenames": filenames,
          "description": description,
          "bucket": bucket,
          "url": url
        }
        print(payload)
        r = requests.post(url, json=payload, headers=self.auth_headers, verify=self.secure_mode)
        if r:
            print('Created dataset: {}'.format(name))
        else:
            print('Failed to create dataset.')
            print('Status code: {}'.format(r.status_code))
            print(r.text)

    def get_dataset(self, params=[]):
        url = self.endpoints['dataset'].format(self.project['id']) + '/'
        r = requests.get(url, headers=self.auth_headers, params=[], verify=self.secure_mode)
        try:
            dataset = json.loads(r.content)
        except Exception as err:
            print('Failed to list datasets.')
            print('Status code: {}'.format(r.status_code))
            print('Message: {}'.format(r.text))
            print('Error: {}'.format(err))
            return []
        return dataset

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
            res = subprocess.run(['tar', 'czvf', model_file, 'models', 'requirements.txt', 'setup.py', 'src'], stdout=subprocess.PIPE) #, 'dataset/interim/preprocessed'

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

        r = requests.post(url, json=model_data, headers=self.auth_headers, verify=self.secure_mode)
        if not _check_status(r, error_msg="Failed to create model."):
            repo.delete_artifact(model_uid)
            return False

        if building_from_current:
            os.system('rm {}'.format(model_file))
        print('Released model: {}, release_type: {}'.format(model_name, release_type))
        return True

    def deploy_model(self, model_name, model_version, deploy_context, settings=[]):
        deploy_config = ""
        if settings:
            settings_file = open(settings, 'r')
            deploy_config = json.loads(settings_file.read())
        url = self.endpoints['deploymentInstances']+'build_instance/'
        bd_data = {"project": self.project['id'], "name": model_name, "version": model_version, "depdef": deploy_context, "deploy_config": deploy_config}
        r = requests.post(url, json=bd_data, headers=self.auth_headers, verify=self.secure_mode)
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
        r = requests.post(url, headers=self.auth_headers, json=params, verify=self.secure_mode)
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
        if resource == 'labs':
            if self.found_project:
                labs = self.get_lab_sessions()
                return labs
            else:
                return []
        if resource == 'members':
            if self.found_project:
                members = self.get_members()
                return members
            else:
                return []
        if resource == 'dataset':
            if self.found_project:
                dataset = self.get_dataset()
                return dataset
            else:
                return []
        if resource == 'volumes':
            if self.found_project:
                volumes = self.get_volumes()
                return volumes
            else:
                return []
        if resource == 'jobs':
            if self.found_project:
                jobs = self.get_jobs()
                return jobs
            else:
                return []
        
        url = self.endpoints[resource]

        r = requests.get(url, headers=self.auth_headers, verify=self.secure_mode)
        if not _check_status(r, error_msg="Failed to list {}.".format(resource)):
            return False
        else:
            return json.loads(r.content)

    def get_models(self, project_id, params=[]):
        url = self.endpoints['models'].format(project_id)
        r = requests.get(url, headers=self.auth_headers, params=params, verify=self.secure_mode)
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
        r = requests.get(url, headers=self.auth_headers, params=params, verify=self.secure_mode)
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
        r = requests.get(url, headers=self.auth_headers, verify=self.secure_mode)
        model = json.loads(r.content)
        return model
        
    def list_deployments(self):
        url = self.endpoints['deploymentInstances']
        r = requests.get(url, headers=self.auth_headers, params={'project':self.project['id']}, verify=self.secure_mode)
        if not _check_status(r, error_msg="Failed to fetch deployments"):
            return False
        deployments = json.loads(r.content)
        depjson = []
        for deployment in deployments:

            model = self.get_model(self.project['id'], deployment['model'])
            dep = {'name': model['name'],
                   'version': model['version'],
                   'endpoint': 'https://'+deployment['endpoint']+deployment['path']+'predict/',
                   'created_at': deployment['created_at']}
            depjson.append(dep)
        return depjson

    def get_deployment(self, params):
        url = self.endpoints['deploymentInstances']
        r = requests.get(url, params=params, headers=self.auth_headers, verify=self.secure_mode)
        if r:
            return json.loads(r.content)
        else:
            print("Failed to load deployments.")
            print("Status code: {}".format(r.status_code))
            print("Reason: {}".format(r.reason))

    def delete_model(self, name, version=None):
        if version:
            params = {'name': name, 'version': version}
        else:
            params = {'name': name}
        models  = self.get_models(self.project['id'], params)
        if not models:
            print("No models found with the given name and/or version.")
        for model in models:
            url = '{}/{}'.format(self.endpoints['models'].format(self.project['id']), model['id'])
            r = requests.delete(url, headers=self.auth_headers, verify=self.secure_mode)
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
                r = requests.delete(url, headers=self.auth_headers, params=params, verify=self.secure_mode)
                if not _check_status(r, error_msg="Failed to delete deployment {}:{}.".format(model['name'], model['version'])):
                    pass
                else:
                    print("Deleted deployment {}:{}.".format(model['name'], model['version']))

    def add_members(self, users, role):
        # url = self.endpoints['projects'] + 'add_members/'
        url = self.endpoints['members'].format(self.project['id']) + '/'
        data = {'selected_users': users, 'role': role}
        r = requests.post(url, headers=self.auth_headers, json=data, verify=self.secure_mode)
        if r:
            print('New members: ' + users)
            print('Successfully added the selected users as members to project {}.'.format(self.project['name']))
        else:
            print('Failed to add members to project {}.'.format(self.project['name']))
            print('Status code: {}'.format(r.status_code))
            print('Reason: {}'.format(r.reason))

    def remove_members(self, users):          
        members = self.get_members()
        users = users.split(',')
        for user in users:
            for member in members:
                if member['username'] == user:
                    url = self.endpoints['members'].format(self.project['id']) + '/'+str(member['id'])
                    r = requests.delete(url, headers=self.auth_headers, verify=self.secure_mode)
                    if r:
                        print('Removed member: {}'.format(user))
                    else:
                        print('Failed to remove member {}.'.format(user))
                        print('Status code: {}'.format(r.status_code))
                        print('Reason: {}'.format(r.reason))
                    break

    def create_session(self, flavor_slug, environment_slug, volumes=[]):
        url = self.endpoints['labs'].format(self.project['id']) + '/'
        data = {'flavor': flavor_slug, 'environment': environment_slug, 'extraVols': volumes}

        r = requests.post(url, headers=self.auth_headers, json=data, verify=self.secure_mode)

        if r:
            print('Successfully created Lab Session.')
            print('Flavor: ' + flavor_slug)
            print('Environment: ' + environment_slug)
        else:
            print('Failed to create Lab Session.')
            print('Status code: {}'.format(r.status_code))
            print('Reason: {} - {}'.format(r.reason, r.text))

    """
    def log_to_db(self, data_to_log):
        try:
            from pymongo import MongoClient
        except ImportError:
            print('Failed to import MongoClient')
            return None
        myclient = MongoClient("localhost:27017", username = 'root', password = 'tvJdjZm6PG')
        db = myclient["test"]
        Collection = db["testCollection"]
        if isinstance(data_to_log, list): 
            Collection.insert_many(data_to_log)   
        else: 
            Collection.insert_one(data_to_log)
    """     


    def retrieve_metadata(self, model, run_id):
        """ Retrieve metadata logged during model training """

        md_file = 'src/models/tracking/metadata/{}.pkl'.format(run_id)
        if os.path.isfile(md_file):
            print('Retrieving metadata for current training session for storage in Studio...')
            try:
                import pickle
                with open(md_file, 'rb') as metadata_file:
                    metadata_json = pickle.load(metadata_file)
                    print("Metadata was retrieved successfully from local file.")
                repo = self.get_repository()
                repo.bucket = 'metadata'
                if not 'model' in metadata_json:
                    metadata_json['model'] = ''
                if not 'params' in metadata_json:
                    metadata_json['params'] = {}
                if not 'metrics' in metadata_json:
                    metadata_json['metrics'] = {}

                metadata = {"run_id": run_id,
                            "trained_model": model,
                            "model_details": metadata_json["model"],
                            "parameters": metadata_json["params"],
                            "metrics": metadata_json["metrics"]
                }
                url = self.endpoints['metadata'].format(self.project['id'])+'/'
                r = requests.post(url, json=metadata, headers=self.auth_headers, verify=self.secure_mode)
                if not _check_status(r, error_msg="Failed to create metadata log in Studio for run with ID '{}'".format(run_id)):
                    return 
                print("Created metadata log in Studio for run with ID '{}'".format(run_id))
            except Exception as e: # Should catch more specific error here
                print("Error")
                print(e)
                return 
        else:
            print("No metadata available for current training session.")
            return 


    def run_training_file(self, model, training_file, run_id):
        """ Run training file and return date and time for training, and execution time """

        start_time = datetime.now()
        training = subprocess.run(['python3', training_file, run_id])
        end_time = datetime.now()
        execution_time = str(end_time - start_time)
        start_time = start_time.strftime("%Y/%m/%d, %H:%M:%S")
        if training.returncode != 0:
            training_status = 'FA'
            print("Training of the model was not executed properly.")
        else:
            training_status = 'DO'
        self.retrieve_metadata(model, run_id)
        return (start_time, execution_time, training_status)


    def train(self, model, run_id, training_file, code_version):
        """ Train a model and log corresponding data in Studio. """
        
        system_details, cpu_details, git_details = get_run_details(code_version)
        print('Running training script...')
        training_output = self.run_training_file(model, training_file, run_id) # Change output of run_training_file
        repo = self.get_repository()
        repo.bucket = 'training'

        training_data = {"run_id": run_id,
                         "trained_model": model,
                         "training_started_at": training_output[0],
                         "execution_time": training_output[1],
                         "code_version": code_version,
                         "current_git_repo": str(git_details[0]),
                         "latest_git_commit": git_details[1],
                         "system_details": system_details,
                         "cpu_details": cpu_details,
                         "training_status": training_output[2]}  
        url = self.endpoints['modellogs'].format(self.project['id'])+'/'
        print(git_details)
        r = requests.post(url, json=training_data, headers=self.auth_headers, verify=self.secure_mode)
        if not _check_status(r, error_msg="Failed to create training session log in Studio for {}".format(model)):
            return False
        else:
            print("Created training log for {}".format(model))
            return True


    def predict(self, model, inp, version=None):
        if version:
            params = {'name': model, 'version': version}
        else:
            params = {'name': model}
        models  = self.get_models(self.project['id'], params)
        model = models[0]
        # for model in models:
        #     deployment = self.get_deployment({'model':model['id'],'project':self.project['id']})
        
        params = {"project": self.project['id'], "model": model['id']}
        res = self.get_deployment(params)
        url = 'https://'+res[0]['endpoint']+res[0]['path']+'predict/'
        res = requests.post(url,
                     headers=self.auth_headers,
                     json=json.loads(inp),
                     verify=self.secure_mode)
        print(res.json())

if __name__ == '__main__':

    client = StudioClient()
    p = client.get_projects({'slug': 'Test'})
    print("Project:", p)
    e = client.list_endpoints()
    print("Endpoints: ", e)
    data = client._get_repository_conf()
    print("Minio settings: ", data)

    print(client.token)
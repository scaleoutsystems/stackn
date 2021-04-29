
import os
import requests
from scaleout.errors import AuthenticationError
import json
import jwt
import base64
from getpass import getpass
from scaleout.utils.file import dump_to_file, load_from_file
import logging

logger = logging.getLogger('cli')

def keycloak_user_auth(username, password, keycloak_url, client_id='studio-api', realm='STACKn', secure=True):
    discovery_url = os.path.join(keycloak_url, 'auth/realms/{}'.format(realm))
    res = requests.get(discovery_url, verify=secure)
    if res:
        realm_info = res.json()
        public_key = realm_info['public_key']
    else:
        print('Failed to discover realm settings: '+realm)
        return None
    token_url = os.path.join(keycloak_url, 'auth/realms/{}/protocol/openid-connect/token'.format(realm))
    req = {'client_id': client_id,
           'grant_type': 'password',
           'username': username,
           'password': password}
    res = requests.post(token_url, data=req, verify=secure)
    if res:
        res = res.json()
    else:
        print('Failed to authenticate.')
        print(res.text)
    if 'access_token' in res:
        return res['access_token'], res['refresh_token'], public_key
    else:
        print('User: '+username+' denied access to client: '+client_id)
        return False

def write_stackn_config(updated_values):
    dirpath = os.path.expanduser('~/.scaleout/')
    if os.path.exists(dirpath+'stackn.json'):
        stackn_config, load_status = load_from_file('stackn', dirpath)
        if not load_status:
            print('Failed to load stackn config (~/.scaleout/stackn.json)')
            return False
    else:
        stackn_config = dict()

    for key, value in updated_values.items():
        stackn_config[key] = value
    
    status = dump_to_file(stackn_config, 'stackn', dirpath)
    if not status:
        logger.info('Failed to update config -- could not write to file.')

    

def write_tokens(deployment, token, refresh_token, public_key, keycloak_host, studio_host):
    dirpath = os.path.expanduser('~/.scaleout/'+deployment)
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
    dep_config = {'access_token': token,
                  'refresh_token': refresh_token,
                  'public_key': public_key,
                  'keycloak_url': keycloak_host,
                  'studio_url': studio_host}
    status = dump_to_file(dep_config, 'user', dirpath)
    if not status:
        logger.info('Could not write tokens -- failed to write to file.')

def get_stackn_config(secure=True):
    # if not os.path.exists(os.path.expanduser('~/.scaleout/stackn.json')):
    #     print('You need to setup STACKn first.')
    #     login()

    stackn_config, load_status = load_from_file('stackn', os.path.expanduser('~/.scaleout'))
    if not load_status:
        print('Failed to load stackn config file.')
        print('You need to setup STACKn first.')
        login(secure=secure)
        stackn_config, load_status = load_from_file('stackn', os.path.expanduser('~/.scaleout'))
        # return None

    return stackn_config, load_status

def get_remote_config():
    stackn_config, load_status = get_stackn_config()
    if not load_status:
        print('Failed to load STACKn config.')
        return [], False

    active_dir = stackn_config['active']
    if 'active_project' in stackn_config:
        active_path = os.path.expanduser('~/.scaleout/'+active_dir)
        remote_config, load_status = load_from_file('user', active_path)
        return remote_config, load_status
    else:
        print('No active project: Create a new project or set an existing project.')
        return [], False

def get_token(client_id='studio-api', realm='STACKn', secure=True):
    # stackn_config, load_status = load_from_file('stackn', os.path.expanduser('~/.scaleout/'))
    # if not load_status:
    #     print('Failed to load stackn config file.')
    #     return None
    stackn_config, load_status = get_stackn_config()

    active_dir = os.path.expanduser('~/.scaleout/')+stackn_config['active']
    token_config, load_status = load_from_file('user', active_dir)
    if not load_status:
        print('Failed to load user config file.')
        return None
    
    access_token = token_config['access_token']

    try:
        public_key_full = '-----BEGIN PUBLIC KEY-----\n'+token_config['public_key']+'\n-----END PUBLIC KEY-----'
        access_token_json = jwt.decode(access_token,
                                    public_key_full,
                                    algorithms='RS256',
                                    audience='studio-api')
        # print('Token valid for user '+access_token_json['preferred_username'])
    except:
        # Try to refresh token
        token_url = os.path.join(token_config['keycloak_url'], 'auth/realms/{}/protocol/openid-connect/token'.format(realm))
        req = {'grant_type': 'refresh_token',
               'client_id': client_id,
               'refresh_token': token_config['refresh_token']}
        res = requests.post(token_url, data=req, verify=secure)
        resp = res.json()
        if 'access_token' in resp:
            access_token = resp['access_token']
            refresh_token = resp['refresh_token']
            write_tokens(stackn_config['active'],
                         access_token,
                         refresh_token,
                         token_config['public_key'],
                         token_config['keycloak_url'],
                         token_config['studio_url'])
            # return res['access_token'], res['refresh_token'], public_key
        else:
            print('Failed to authenticate with token, please login again.')
            print(res.text)
            access_token = login(deployment=stackn_config['active'], keycloak_host=token_config['keycloak_url'], studio_host=token_config['studio_url'], secure=secure)

    return access_token, token_config



def login(client_id='studio-api', realm='STACKn', deployment=[], keycloak_host=[], studio_host=[], username=[], secure=True):
    """ Login to Studio services. """
    if not deployment:
        deployment = input('Name: ')
    if not studio_host:
        studio_host = input('Studio host: ')

    url = "{}/api/settings".format(studio_host)
    r = requests.get(url)
    if (r.status_code >= 200 or r.status_code <= 299):
        studio_settings = json.loads(r.content)["data"]
        keycloak_host = next(item for item in studio_settings if item["name"] == "keycloak_host")["value"]

    if not keycloak_host:
        keycloak_host = input('Keycloak host: ')
    if not username:
        username = input('Username: ')
    password = getpass()
    access_token, refresh_token, public_key = keycloak_user_auth(username, password, keycloak_host, secure=secure)
    # dirname = base64.urlsafe_b64encode(host.encode("utf-8")).decode("utf-8")
    dirpath = os.path.expanduser('~/.scaleout/'+deployment)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    write_tokens(deployment, access_token, refresh_token, public_key, keycloak_host, studio_host)
    write_stackn_config({'active': deployment, 'client_id': client_id, 'realm': realm})
    return access_token


def get_bearer_token(url, username, password):
    """ Exchange username,password for an auth token.
        TODO: extend to get creds from keyring. """
    data = {
        'username': username,
        'password': password
    }

    r = requests.post(url, data=data)

    if r.status_code == 200:
        return json.loads(r.content)['token']
    else:
        print('Authentication failed!')
        print("Requesting an authorization token failed.")
        print('Returned status code: {}'.format(r.status_code))
        print('Reason: {}'.format(r.reason))
        raise AuthenticationError


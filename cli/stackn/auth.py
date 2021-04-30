
import os
import requests
import json
import jwt
import base64
from getpass import getpass
from pathlib import Path
import urllib.parse

import stackn.error_msg

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

STACKN_CONFIG_PATH = '~/.scaleout'
STACKN_CONFIG_FILE = 'stackn.json'

global_vars = {
    'STACKN_CONFIG_PATH': '~/.scaleout',
    'STACKN_CONFIG_FILE': 'stackn.json'
}

env_vars = {
    'STACKN_REALM': 'STACKn',
    'STACKN_CLIENT_ID': 'studio-api',
    'STACKN_URL': [],
    'STACKN_USER': [],
    'STACKN_PASS': [],
    'STACKN_PROJECT': [],
    'STACKN_S3': [],
    'STACKN_MODEL': [],
    'STACKN_RELEASE_TYPE': [],
    'STACKN_OBJECT_TYPE': [],
    'STACKN_KEYCLOAK_URL': [],
    'STACKN_ACCESS_TOKEN': [],
    'STACKN_REFRESH_TOKEN': [],
    'STACKN_SECURE': True
}

def _get_stackn_config_path():
    if 'STACKN_CONFIG_PATH' in os.environ:
        config_path = os.environ['STACKN_CONFIG_PATH']
    else:
        config_path = global_vars['STACKN_CONFIG_PATH']
    dirpath = os.path.expanduser(config_path)
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
    if 'STACKN_CONFIG_FILE' in os.environ:
        config_file_path = os.environ['STACKN_CONFIG_FILE']
    else:
        config_file_path = global_vars['STACKN_CONFIG_FILE']
    path_to_config = os.path.join(dirpath, config_file_path)
    return path_to_config

def _get_studio_url_key(studio_url):
    return studio_url.replace('https://', '').replace('http://', '').strip('/')  


def _get_config_file(rw='r'):
    path_to_config = _get_stackn_config_path()
    try:
        fin = open(path_to_config, rw)
    except Exception as err:
        return []
    
    return fin

def _load_config_file_full(conf):
    stackn_config = []
    fin = _get_config_file()
    if fin:
        try:
            stackn_config = json.load(fin)
        except:
            return []
    return stackn_config

def _load_config_file_url(conf, is_login=False):
    stackn_config_full = _load_config_file_full(conf)
    if stackn_config_full:
        try:
            stackn_config = stackn_config_full[_get_studio_url_key(conf['STACKN_URL'])]
        except:
            if conf['STACKN_URL'] and not is_login:
                print("Failed to load config file from URL: {} not set up.".format(conf['STACKN_URL']))
                return False
            else:
                stackn_config = []
    else:
        stackn_config = []
    
    return stackn_config

def _get_remote(conf):
    stackn_config_full = _load_config_file_full(conf)
    try:
        del stackn_config_full['current']
    except:
        pass
    keys = stackn_config_full.keys()
    return keys
    

def _get_current(conf):
    stackn_config_full = _load_config_file_full(conf)
    if stackn_config_full and 'current' in stackn_config_full:
        return stackn_config_full['current']
    
    return False

def _set_current(conf):
    
    current = {
        'STACKN_URL': False,
        'STACKN_PROJECT': False,
        'STACKN_SECURE': 'NOTSET'
    }
    if 'STACKN_URL' in conf:
        current['STACKN_URL'] = conf['STACKN_URL']
    if 'STACKN_PROJECT' in conf:
        current['STACKN_PROJECT'] = conf['STACKN_PROJECT']
    if 'STACKN_SECURE' in conf:
        current['STACKN_SECURE'] = conf['STACKN_SECURE']

    # Write settings to config file.

    # First read settings:
    conf, status = get_config(conf)
    if not status:
        print("Failed to load config")
        return []

    stackn_config = _load_config_file_full(conf)
    if not 'current' in stackn_config:
        stackn_config['current'] = {'STACKN_URL': '', 'STACKN_PROJECT': '', 'STACKN_SECURE': ''}
    if current['STACKN_URL']:
        stackn_config['current']['STACKN_URL'] = current['STACKN_URL']
        if current['STACKN_PROJECT']:
            stackn_config['current']['STACKN_PROJECT'] = current['STACKN_PROJECT']
        else:
            stackn_config['current']['STACKN_PROJECT'] = ''
    elif current['STACKN_PROJECT']:
        stackn_config['current']['STACKN_PROJECT'] = current['STACKN_PROJECT']
    if current['STACKN_SECURE'] != 'NOTSET':
        stackn_config['current']['STACKN_SECURE'] = current['STACKN_SECURE']


    if 'STACKN_URL' in os.environ and stackn_config['current']['STACKN_URL'] != '':
        print("STACKN_URL set as environment variable and this takes priority.")
        print("Set by 'export STACKN_URL={}'".format(stackn_config['current']['STACKN_URL']))
    if 'STACKN_PROJECT' in os.environ and stackn_config['current']['STACKN_PROJECT'] != '':
        print("STACKN_PROJECT set as environment variable and this takes priority.")
        print("Set by 'export STACKN_PROJECT={}'".format(stackn_config['current']['STACKN_PROJECT']))
    if 'STACKN_SECURE' in os.environ and stackn_config['current']['STACKN_SECURE'] != '':
        print("STACKN_SECURE set as environment variable and this takes priority.")
        print("Set by 'export STACKN_SECURE={}'".format(stackn_config['current']['STACKN_SECURE']))
    
    # Write to file
    fout = _get_config_file('w')
    if fout:
        json.dump(stackn_config, fout)
        fout.close()
        return True
    else:
        print("Failed to write current settings to file.")
        return []

    



def get_config(inp_config=dict(), required=[], is_login=False, print_warnings=True):
    # Order of priority:
    # 1. Values in inp_config
    # 2. Environment variables
    # 3. Config file
    # Exception is STACKN_ACCESS_TOKEN, and STACKN_REFRESH_TOKEN, where config file
    # takes priority over environment variable (as they need to be updated)

    conf = dict()
    # Fetch from environment variables
    for var, val in env_vars.items():
        if var in inp_config and inp_config[var] != None:
            conf[var] = inp_config[var]
        elif var in os.environ:
            conf[var] = os.environ[var]
        else:
            conf[var] = val

    # Fetch "current" remote, project, secure_mode
    config_file_full = _load_config_file_full(conf)
    try:
        current = config_file_full['current']
    except:
        current = {}
    if not conf['STACKN_URL']:
        if 'STACKN_URL' in current:
            conf['STACKN_URL'] = current['STACKN_URL']
    if not conf['STACKN_PROJECT']:
        if 'STACKN_PROJECT' in current:
            conf['STACKN_PROJECT'] = current['STACKN_PROJECT']
    # if 'STACKN_SECURE' not in conf:
    if 'STACKN_SECURE' in current:
        if print_warnings and current['STACKN_SECURE'] == False:
            print("Insecure mode is set in config, will not verify certificates.")
            print("Use stackn set current --secure to disable.")
        conf['STACKN_SECURE'] = current['STACKN_SECURE']
    # If we have a currently set remote URL, fetch from config file.
    if conf['STACKN_URL']:
        try:
            conf['STACKN_KEYCLOAK_URL'] = get_keycloak_url(conf['STACKN_URL'], secure=conf['STACKN_SECURE'])
        except:
            print("Failed to call studio endpoint at: {}".format(conf['STACKN_URL']))
            return conf, False
        config_file = _load_config_file_url(conf, is_login)
        if config_file:
            for key, val in config_file.items():
                if not (key in conf) or not conf[key] or key=='STACKN_ACCESS_TOKEN' or key=='STACKN_REFRESH_TOKEN':
                    conf[key] = val
        elif not is_login:
            return conf, False

    # Check that we have all required keys
    for key in required:
        if not (key in conf) or not conf[key]:
            return conf, False
    return conf, True

def _keycloak_user_auth(conf):
    username = conf['STACKN_USER']
    password = conf['STACKN_PASS']
    keycloak_url = conf['STACKN_KEYCLOAK_URL']
    client_id = conf['STACKN_CLIENT_ID']
    realm = conf['STACKN_REALM']
    secure = conf['STACKN_SECURE']
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

def get_token(conf={}, write_to_file=True):
    
    conf, status = get_config(conf, required=['STACKN_REFRESH_TOKEN'])
    if not status:
        print("Failed to get required config.")
        return conf, False

    token_url = urllib.parse.urljoin(conf["STACKN_KEYCLOAK_URL"], 'auth/realms/{}/protocol/openid-connect/token'.format(conf['STACKN_REALM']))
    
    req = {'grant_type': 'refresh_token',
           'client_id': conf['STACKN_CLIENT_ID'],
           'refresh_token': conf['STACKN_REFRESH_TOKEN']}
    res = requests.post(token_url, data=req, verify=conf['STACKN_SECURE'])
    resp = res.json()
    
    if 'access_token' in resp:
        conf['STACKN_ACCESS_TOKEN'] = resp['access_token']
        conf['STACKN_REFRESH_TOKEN'] = resp['refresh_token']
        if write_to_file:
            write_config(conf)
    else:
        print('Failed to authenticate with token, please login again.')
        print(res.text)
        return conf, False

    return conf, True


def write_config(conf):

    studio_url = conf['STACKN_URL']
    
    path_to_config = _get_stackn_config_path()
    Path(path_to_config).touch()

    f = open(path_to_config, 'r')
    try:
        current_config = json.load(f)
    except:
        current_config = dict()
    f.close()

    studio_url_key = _get_studio_url_key(studio_url)
    current_config[studio_url_key] = conf

    try:
        fout = open(path_to_config, 'w')
        json.dump(current_config, fout)
        fout.close()
    except Exception as err:
        print('Could not write tokens -- failed to write to file.')
        print(err)

def get_keycloak_url(studio_url, secure=True):
    url = studio_url.strip('/')+'/api/settings'
    try:
        r = requests.get(url, verify=secure)
    except requests.exceptions.MissingSchema as e:
        r = requests.get('https://'+url, verify=secure)

    if (r.status_code >= 200 or r.status_code <= 299):
        studio_settings = json.loads(r.content)["data"]
        keycloak_host = next(item for item in studio_settings if item["name"] == "keycloak_host")["value"]
    
    return keycloak_host

def stackn_login(studio_url=[], client_id=[], realm=[], username=[], password=[], secure=True):
    """ Login to Studio services. """
    inp_config = {
        'STACKN_URL': studio_url,
        'STACKN_CLIENT_ID': client_id,
        'STACKN_REALM': realm,
        'STACKN_USER': username,
        'STACKN_PASS': password,
        'STACKN_SECURE': secure
    }

    conf, status = get_config(inp_config=inp_config, is_login=True)

    if not conf['STACKN_URL']:
        conf['STACKN_URL'] = input('Studio URL: ')
        conf['STACKN_KEYCLOAK_URL'] = get_keycloak_url(conf['STACKN_URL'])

    if not conf['STACKN_USER']:
        conf['STACKN_USER'] = input('Username: ')

    if not conf['STACKN_PASS']:
        if conf['STACKN_REFRESH_TOKEN'] and conf['STACKN_REFRESH_TOKEN'] != '':
            try:
                conf, status = get_token(conf, write_to_file=False)
            except:
                pass
            if not status:
                print("Failed to login with set refresh token.")
                print("Try with password instead.")
                conf['STACKN_PASS'] = getpass()
        else:
            conf['STACKN_PASS'] = getpass()
    if conf['STACKN_PASS']:
        access_token, refresh_token, public_key = _keycloak_user_auth(conf)
        conf['STACKN_ACCESS_TOKEN'] = access_token
        conf['STACKN_REFRESH_TOKEN'] = refresh_token
        conf['PUBLIC_KEY'] = public_key

    write_config(conf)
    _set_current(conf)
    return conf


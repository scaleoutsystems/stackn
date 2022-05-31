
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
    'STACKN_CLIENT_ID': 'studio-api',
    'STACKN_URL': [],
    'STACKN_USER': [],
    'STACKN_PASS': [],
    'STACKN_PROJECT': [],
    'STACKN_S3': [],
    'STACKN_MODEL': [],
    'STACKN_RELEASE_TYPE': [],
    'STACKN_OBJECT_TYPE': [],
    'STACKN_ACCESS_TOKEN': [],
    'STACKN_SECURE': True
    #'STACKN_REFRESH_TOKEN': []
}


# STACKN_SECURE is by default always set to True. However we allow to deploy STACKn locally for development and testing purposes.
# That's when a user needs to login with the flag --insecure, and thus STACKN_SECURE will be False
# The util function make sure to remind the user to use --insecure if set in the ~/.scaleout/stackn.json configuration file
def _check_flag_insecure(inp_conf):
    stackn_conf_file = _load_config_file_full({})

    # If the general default STACKN_SECURE is still True, but in the configuration file shows that 
    # it is set to False instead (because the user has logged in with --insecure) Then we remind the user to use --insecure
    if stackn_conf_file['current']['STACKN_SECURE'] == False and inp_conf['STACKN_SECURE']:
        print("Do you perhaps have a local STACKn deployment? If so, don't forget to use --insecure to make stackn API calls working.")
        return True
    else:
        return False


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


# Checking if a user is logged. Promtping it if otherwise
def _is_user_logged():
    stackn_conf_file = _load_config_file_full({})

    if not stackn_conf_file:
        print("You are not logged in.")
        print("Please use the command: 'stackn login -u <your-user> -p <your-user-password>' --url <your-studio-url>")
        return False
    else:
        return True


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
            no_scheme_url = _get_studio_url_key(conf['STACKN_URL'])
            if no_scheme_url in stackn_config_full.keys():
                stackn_config = stackn_config_full[no_scheme_url]
            else:
                stackn_config = stackn_config_full[conf['STACKN_URL']]
        except KeyError as e:
            if conf['STACKN_URL'] and not is_login:
                print("Failed to load config file from URL: {} not set up.".format(conf['STACKN_URL']))
                print(e)
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

    # First read settings:

    # If _set_current is invoked by stackn_login, then pass is_login
    if 'is_login' in conf and conf['is_login']:
        conf, status = get_config(conf, is_login=True)
    else:
        conf, status = get_config(conf)

    if not status:
        print("Failed to get current STACKn configuration file.")
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

    # Checking if the user is logged in. Skipping if when the user needs to login instead
    if not is_login and not _is_user_logged():
        return False, False

    # Checking if user has forgot to use --insecure flag
    if is_login:
        pass
    else:
        if _check_flag_insecure(inp_config):
            return False, False

    conf = dict()
    # Fetch from environment variables
    for var, val in env_vars.items():
        if var in inp_config and inp_config[var] != None:
            conf[var] = inp_config[var]
        elif var in os.environ:
            conf[var] = os.environ[var]
        else:
            conf[var] = val


    # Fetch "current" context: remote_url, project and secure_mode
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


    # Checking flag STACKN_SECURE and initialize it if needed
    if 'STACKN_SECURE' in current and (conf['STACKN_SECURE']=="" or conf['STACKN_SECURE']==None):
        if print_warnings and current['STACKN_SECURE'] == False:
            print("Insecure mode is set in config, will not verify certificates.")
            print("Use stackn set current --secure to disable.")
        conf['STACKN_SECURE'] = current['STACKN_SECURE']
    # If we have a currently set remote URL, fetch from config file.
    if conf['STACKN_URL']:
        config_file = _load_config_file_url(conf, is_login)
        if config_file:
            for key, val in config_file.items():
                if not (key in conf) or not conf[key] or key=='STACKN_ACCESS_TOKEN':
                    conf[key] = val
        elif not is_login:
            return conf, False

    # Check that we have all required keys
    for key in required:
        if not (key in conf) or not conf[key]:
            return conf, False
    return conf, True


def get_token(conf={}):
    # It send a POST request to /api/token-auth/
    # components/studio/api/views.py --> CustomAuthToken
    if not "http" in conf['STACKN_URL']:
        studio_url = "http://" + conf['STACKN_URL']
    else:
        studio_url = conf['STACKN_URL']
    token_url = studio_url.strip('/')+'/api/token-auth/' # previously keycloak token url
    
    print("INFO: Token URL is: {}".format(token_url))

    req = {'username': conf['STACKN_USER'],
           'password': conf['STACKN_PASS'],
    }
    res = requests.post(token_url, json=req, verify=conf['STACKN_SECURE'])
    resp = res.json()
    
    if 'token' in resp:
        print('Token retrieved successfully.')
        return resp['token']
    else:
        print('Failed to fetch token.')
        print(res.text)
        return False


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


def stackn_login(studio_url=[], client_id=[], username=[], password=[], secure=True):
    """ Login to Studio services. """
    if not "http" in studio_url:
        studio_url = "http://" + studio_url

    inp_config = {
        'STACKN_URL': studio_url,
        'STACKN_CLIENT_ID': client_id,
        'STACKN_USER': username,
        'STACKN_PASS': password,
        'STACKN_SECURE': secure
    }

    conf, status = get_config(inp_config=inp_config, is_login=True)

    if not conf['STACKN_URL']:
        conf['STACKN_URL'] = input('Studio URL: ')

    if not conf['STACKN_USER']:
        conf['STACKN_USER'] = input('Username: ')

    if not conf['STACKN_PASS']:
        # if conf['STACKN_REFRESH_TOKEN'] and conf['STACKN_REFRESH_TOKEN'] != '':
        #     try:
        #         conf, status = get_token(conf, write_to_file=False)
        #     except:
        #         pass
        #     if not status:
        #         print("Failed to login with set refresh token.")
        #         print("Try with password instead.")
        #         conf['STACKN_PASS'] = getpass()
        # else:
        conf['STACKN_PASS'] = getpass()

    if conf['STACKN_PASS']:
        conf['STACKN_ACCESS_TOKEN'] = get_token(conf)
        #conf['STACKN_REFRESH_TOKEN'] = refresh_token

    write_config(conf)

    # adding flag in conf for informing  that set_current is begin invoked by stackn_login
    conf.update(is_login = "True")
    _set_current(conf)

    return conf


import os
import requests
from scaleout.errors import AuthenticationError
import json
import jwt
import base64
from getpass import getpass
from scaleout.utils.file import dump_to_file, load_from_file


def keycloak_user_auth(username, password, host_url, client_id='studio-api', realm='STACKn'):
    discovery_url = '{}/auth/realms/{}'.format(host_url, realm)
    res = requests.get(discovery_url)
    if res:
        realm_info = res.json()
        public_key = realm_info['public_key']
    else:
        print('Failed to discover realm settings: '+realm)
        return None
    
    token_url = '{}/auth/realms/{}/protocol/openid-connect/token'.format(host_url, realm)
    req = {'client_id': client_id,
           'grant_type': 'password',
           'username': username,
           'password': password}
    res = requests.post(token_url, data=req)
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
    
    dump_to_file(stackn_config, 'stackn', dirpath)

    

def write_tokens(deployment, token, refresh_token, public_key, host_url):
    dirpath = os.path.expanduser('~/.scaleout/'+deployment)
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
    dep_config = {'access_token': token,
                  'refresh_token': refresh_token,
                  'public_key': public_key,
                  'host_url': host_url}
    dump_to_file(dep_config, 'user', dirpath)

def get_token(client_id='studio-api', realm='STACKn'):
    stackn_config, load_status = load_from_file('stackn', os.path.expanduser('~/.scaleout/'))
    if not load_status:
        print('Failed to load stackn config file.')
        return None

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
                                       audience='account')
        # print('Token valid for user '+access_token_json['preferred_username'])
    except:
        # Try to refresh token
        print('Refreshing token...')
        token_url = '{}/auth/realms/{}/protocol/openid-connect/token'.format(token_config['host_url'], realm)
        req = {'grant_type': 'refresh_token',
               'client_id': client_id,
               'refresh_token': token_config['refresh_token']}
        res = requests.post(token_url, data=req)
        resp = res.json()
        if 'access_token' in resp:
            access_token = resp['access_token']
            refresh_token = resp['refresh_token']
            write_tokens(stackn_config['active'],
                         access_token,
                         refresh_token,
                         token_config['public_key'],
                         token_config['host_url'])
            # return res['access_token'], res['refresh_token'], public_key
        else:
            print('Failed to authenticate with token, please login again.')
            print(res.text)
            access_token = login()


    return access_token



def login():
    """ Login to Studio services. """
    deployment = input('Name: ')
    host = input('Host: ')
    username = input('Username: ')
    password = getpass()
    access_token, refresh_token, public_key = keycloak_user_auth(username, password, host)
    # dirname = base64.urlsafe_b64encode(host.encode("utf-8")).decode("utf-8")
    dirpath = os.path.expanduser('~/.scaleout/'+deployment)
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
    write_tokens(deployment, access_token, refresh_token, public_key, host)
    write_stackn_config({'active': deployment})
    return access_token
    # token_file = open(dirpath+'/token', 'w')
    # refresh_token_file = open(dirpath+'/refresh_token', 'w')
    # public_key_file = open(dirpath+'/public_key', 'w')
    # active_host = open(os.path.expanduser('~/.scaleout/active'), 'w')
    # token_file.write(token)
    # token_file.close()
    # refresh_token_file.write(refresh_token)
    # refresh_token_file.close()
    # active_host.write(deployment)
    # active_host.close()
    # public_key_file.write(public_key)
    # public_key_file.close()

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


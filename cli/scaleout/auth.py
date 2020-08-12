
import os
import requests
from scaleout.errors import AuthenticationError
import json
import jwt
import base64
from getpass import getpass


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


def write_tokens(deployment, token, refresh_token, public_key, host_url):
    dirpath = os.path.expanduser('~/.scaleout/'+deployment)
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
    token_file = open(dirpath+'/token', 'w')
    refresh_token_file = open(dirpath+'/refresh_token', 'w')
    public_key_file = open(dirpath+'/public_key', 'w')
    active_host = open(os.path.expanduser('~/.scaleout/active'), 'w')
    file_host_url = open(os.path.expanduser(dirpath+'/host'), 'w')
    token_file.write(token)
    token_file.close()
    refresh_token_file.write(refresh_token)
    refresh_token_file.close()
    active_host.write(deployment)
    file_host_url.write(host_url)
    active_host.close()
    public_key_file.write(public_key)
    public_key_file.close()
    file_host_url.close()

def verify_or_refresh_jwt_token(deployment, access_token, refresh_token, public_key, host_url, client_id='studio-api', realm='STACKn'):
    try:
        public_key_full = '-----BEGIN PUBLIC KEY-----\n'+public_key+'\n-----END PUBLIC KEY-----'
        access_token_json = jwt.decode(access_token, public_key_full, algorithms='RS256', audience='account')
        # print('Token valid for user '+access_token_json['preferred_username'])
    except:
        # Try to refresh token
        print('Refreshing token...')
        token_url = '{}/auth/realms/{}/protocol/openid-connect/token'.format(host_url, realm)
        req = {'grant_type': 'refresh_token',
               'client_id': client_id,
               'refresh_token': refresh_token}
        res = requests.post(token_url, data=req)
        resp = res.json()
        if 'access_token' in resp:
            access_token = resp['access_token']
            refresh_token = resp['refresh_token']
            write_tokens(deployment, access_token, refresh_token, public_key, host_url)
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


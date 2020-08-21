from django.conf import settings
import requests as r
import logging
import jwt

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class KeycloakInit:
    admin_url: str
    realm: str
    token: str
    def __init__(self, admin_url, realm, token):
        self.admin_url = admin_url
        self.realm = realm
        self.token = token



def keycloak_user_auth(username, password, client_id, admin_url, realm):
    token_url = '{}/realms/{}/protocol/openid-connect/token'.format(admin_url, realm)
    req = {'client_id': client_id,
           'grant_type': 'password',
           'username': username,
           'password': password}
    res = r.post(token_url, data=req)
    if res:
        res = res.json()
    else:
        print('Failed to authenticate.')
        print(res.text)
    if 'access_token' in res:
        return res['access_token']
    else:
        print('User: '+username+' denied access to client: '+client_id)
        return False


def keycloak_client_auth(client_id, client_secret, admin_url, realm):
    token_url = '{}/realms/{}/protocol/openid-connect/token'.format(admin_url, realm)
    payload = 'grant_type=client_credentials'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    res = r.post(token_url, headers=headers,
                            data=payload,
                            auth=r.auth.HTTPBasicAuth(client_id, client_secret)) 
    if res:
        res = res.json()
    else:
        print('Failed to authenticate.')
        print(res.text)
    if 'access_token' in res:
        return res['access_token']
    else:
        print('Failed to authenticate as client: '+client_id)
        return False

def keycloak_token_exchange_studio(kc, user_id):
    token_url = '{}/realms/{}/protocol/openid-connect/token'.format(kc.admin_url, kc.realm)
    req = {'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
           'client_id': 'studio-api',
           'requested_subject': user_id,
           'subject_token': kc.token}
    res = r.post(token_url, data=req)
    token = res.json()['access_token']
    refresh_token = res.json()['refresh_token']
    discovery_url = settings.OIDC_OP_REALM_AUTH+'/'+settings.KC_REALM
    res = r.get(discovery_url)
    if res:
        realm_info = res.json()
        public_key = '-----BEGIN PUBLIC KEY-----\n'+realm_info['public_key']+'\n-----END PUBLIC KEY-----'
    else:
        print('Failed to discover realm settings: '+settings.KC_REALM)
        return False
    return token, refresh_token, token_url, public_key

def keycloak_init():
    admin_url = settings.KC_ADMIN_URL
    realm = settings.KC_REALM
    token = keycloak_client_auth(settings.OIDC_RP_CLIENT_ID,
                                 settings.OIDC_RP_CLIENT_SECRET,
                                 admin_url,
                                 realm)
    if token:
        kc = KeycloakInit(admin_url, realm, token)
        return kc
    else:
        print('Failed to init Keycloak auth')
        return False

def keycloak_get_detailed_user_info(request):
    if not ('oidc_access_token' in request.session):
        logger.warn('No access token in request session -- unable to authorize user.')
        return []
        
    access_token = request.session['oidc_access_token']

    user_json = []
    discovery_url = settings.OIDC_OP_REALM_AUTH+'/'+settings.KC_REALM
    res = r.get(discovery_url)
    if res:
        realm_info = res.json()
        public_key = '-----BEGIN PUBLIC KEY-----\n'+realm_info['public_key']+'\n-----END PUBLIC KEY-----'
    else:
        print('Failed to discover realm settings: '+settings.KC_REALM)
        return None
    try:
        user_json = jwt.decode(access_token, public_key, algorithms='RS256', audience='account')
    except:
        logger.info('Failed to authenticate user.')
    return user_json

def keycloak_verify_user_role(request, resource, role):
    user_info = keycloak_get_detailed_user_info(request)
    print(user_info)
    if user_info:
        try:
            resource_info = user_info['resource_access'][resource]
        except:
            logger.info('User not authorized to access resource {}'.format(resource))
            return False

        resource_roles = resource_info['roles']
        print(resource_roles)
        if role in resource_roles:
            return True
    
    return False


def keycloak_get_clients(kc, payload):
    get_clients_url = '{}/admin/realms/{}/clients'.format(kc.admin_url, kc.realm)
    res = r.get(get_clients_url, headers={'Authorization': 'bearer '+kc.token}, params=payload)
    if res:
        clients = res.json() 
        return clients
    else:
        print('Failed to fetch clients.')
        print('Request returned status: '+str(res.status_code))
        print(res.text)

def keycloak_delete_client(kc, client_id):
    # Get id (not clientId)
    clients = keycloak_get_clients(kc, {'clientId': client_id})
    client_nid = clients[0]['id']
    # Delete client
    delete_client_url = '{}/admin/realms/{}/clients/{}'.format(kc.admin_url, kc.realm, client_nid)
    res = r.delete(delete_client_url, headers={'Authorization': 'bearer '+kc.token})
    if res:
        return True
    else:
        print('Failed to delete client: '+client_id)
        print('Status code: '+str(res.status_code))
        print(res.text)

def keycloak_create_client(kc, client_id, base_url, root_url=[], redirectUris=[]):
    if not root_url:
        root_url = base_url
    if not redirectUris:
        redirectUris = [base_url+'/*']
    create_client_url = '{}/admin/realms/{}/clients'.format(kc.admin_url, kc.realm)
    logger.debug("Create client endpoint: "+create_client_url)
    client_rep = {'clientId': client_id,
                  'baseUrl': base_url,
                  'rootUrl': root_url,
                  'redirectUris': redirectUris}
    logger.debug("Client rep: ")
    logger.debug(client_rep)
    res = r.post(create_client_url, json=client_rep, headers={'Authorization': 'bearer '+kc.token})
    if res:
        logger.debug('Created new client with clientId {}'.format(client_id))
        logger.debug('Status code returned: {}'.format(res.status_code))
        return True
    else:
        print('Failed to create new client.')
        print('Status code: '+str(res.status_code))
        print(res.text)
        return False

def keycloak_get_client_secret(kc, client_nid):
    get_client_secret_url = '{}/admin/realms/{}/clients/{}/client-secret'.format(kc.admin_url, kc.realm, client_nid)
    res = r.get(get_client_secret_url, headers={'Authorization': 'bearer '+kc.token})
    if res:
        res = res.json()
        if 'value' in res:
            return res['value']
    print('Failed to get client secret for client: '+client_nid)
    print('Status code: '+str(res.status_code))
    print(res.text)

def keycloak_create_client_scope(kc, scope_name, protocol='openid-connect', 
                                                 attributes={'include.in.token.scope': 'true',
                                                             'display.on.consent.screen': 'true'}):
    client_scope_url = '{}/admin/realms/{}/client-scopes'.format(kc.admin_url, kc.realm)
    client_scope_body = {'name': scope_name,
                        'protocol': 'openid-connect',
                        'attributes': {'include.in.token.scope': 'true', 'display.on.consent.screen': 'true'}}
    res = r.post(client_scope_url, json=client_scope_body, headers={'Authorization': 'bearer '+kc.token})
    if res:
        return True
    else:
        print('Failed to create client scope '+scope_name)
        print('Status code: '+str(res.status_code))
        print(res.text)
        return False

def keycloak_get_client_scope_id(kc, scope_name):
    client_scope_url = '{}/admin/realms/{}/client-scopes'.format(kc.admin_url, kc.realm)
    res = r.get(client_scope_url, headers={'Authorization': 'bearer '+kc.token})
    if res:
        scopes = res.json()
        scope_id = None
        for scope in scopes:
            if scope['name'] == scope_name:
                scope_id = scope['id']
        return scope_id
    else:
        print('Failed to get client scopes.')
        print('Status code: '+str(res.status_code))
        print(res.text)
        return False

def keycloak_delete_client_scope(kc, scope_id):
    # /{realm}/client-scopes/{id}
    client_scope_url = '{}/admin/realms/{}/client-scopes/{}'.format(kc.admin_url, kc.realm, scope_id)
    res = r.delete(client_scope_url, headers={'Authorization': 'bearer '+kc.token})
    if res:
        return True
    else:
        print('Failed to delete client scope '+scope_id)
        print('Status code: '+str(res.status_code))
        print(res.text)
        return False

def keycloak_create_scope_mapper(kc, scope_id, mapper_name, client_audience):
    create_client_scope_mapper_url = '{}/admin/realms/{}/client-scopes/{}/protocol-mappers/models'.format(kc.admin_url, kc.realm, scope_id)
    scope_mapper = {'name': mapper_name,
                    'protocol': 'openid-connect',
                    'protocolMapper': 'oidc-audience-mapper',
                    'consentRequired': False,
                    'config': {'included.client.audience': client_audience,
                               'id.token.claim': 'false',
                               'access.token.claim': 'true'}}

    res = r.post(create_client_scope_mapper_url,
                 json=scope_mapper,
                 headers={'Authorization': 'bearer '+kc.token})
    if res:
        return True
    else:
        print('Failed to create scope mapper.')
        print('Status code: '+str(res.status_code))
        print(res.text)
        return False

def keycloak_add_scope_to_client(kc, client_id, scope_id):
    add_default_scope_url = '{}/admin/realms/{}/clients/{}/default-client-scopes/{}'.format(kc.admin_url, kc.realm, client_id, scope_id)
    res = r.put(add_default_scope_url, headers={'Authorization': 'bearer '+kc.token})
    if res:
        return True
    else:
        print('Failed to add scope to client.')
        print('Status code: '+str(res.status_code))
        print(res.text)
        return False        

def keycloak_create_client_role(kc, client_nid, role_name, session):
    client_role_url = '{}/admin/realms/{}/clients/{}/roles'.format(kc.admin_url, kc.realm, client_nid)
    role_rep = {'name': role_name}
    res = session.post(client_role_url, json=role_rep, headers={'Authorization': 'bearer '+kc.token, })
    if res:
        return True
    else:
        print('Failed to create client role.')
        print('Status code: '+str(res.status_code))
        print(res.text)
        return False

def keycloak_get_user_id(kc, username):
    get_users_url =  '{}/admin/realms/{}/users'.format(kc.admin_url, kc.realm)
    res = r.get(get_users_url, params={'username': username}, headers={'Authorization': 'bearer '+kc.token}).json()
    if not res:
        print('Failed to get user id.')
        print('Status code: '+str(res.status_code))
        print(res.text)
        return False
    if len(res) != 1:
        print("Didn't find user: "+username+" in realm: "+kc.realm)
        return False
    res = res[0]
    return res['id']

def keycloak_get_client_role_id(kc, role_name, client_nid, session=[]):
    if not session:
        session = r.session()
    client_role_url = '{}/admin/realms/{}/clients/{}/roles'.format(kc.admin_url, kc.realm, client_nid)
    res = r.get(client_role_url, headers={'Authorization': 'bearer '+kc.token})
    if res:
        client_roles = res.json()
        for role in client_roles:
            if role['name'] == role_name:
                return role['id']
    else:
        print('Failed to get client role id.')
        print('Status code: '+str(res.status_code))
        print(res.text)
        return False

def keycloak_add_user_to_client_role(kc, client_nid, username, role_name, session=[]):
    if not session:
        session = r.session()
    user_id = keycloak_get_user_id(kc, username)
    add_user_to_role_url = '{}/admin/realms/{}/users/{}/role-mappings/clients/{}'.format(kc.admin_url,
                                                                                         kc.realm,
                                                                                         user_id,
                                                                                         client_nid)
    
    # Get role id
    role_id = keycloak_get_client_role_id(kc, role_name, client_nid, session)

    role_rep = [{'name': role_name, 'id': role_id}]
    res = session.post(add_user_to_role_url, json=role_rep, headers={'Authorization': 'bearer '+kc.token})
    if res:
        return True
    else:
        print('Failed to add user {} to client role {}.'.format(username, role_name))
        print('Status code: '+str(res.status_code))
        print(res.text)
        return False

def keycloak_add_role_to_user(clientId, username, role):
    logger.info('Adding role {} to user {}. Client is {}.'.format(role, username, clientId))
    kc = keycloak_init()
    # Get client id
    clients = keycloak_get_clients(kc, {'clientId': clientId})
    client_nid = clients[0]['id']
    # Add role to user
    keycloak_add_user_to_client_role(kc, client_nid, username, role)

def keycloak_setup_base_client(base_url, client_id, username, roles=['default'], default_user_role=['default']):
    kc = keycloak_init()
    client_status = keycloak_create_client(kc, client_id, base_url)
    # Create client
    if not client_status:
        return False
    # Fetch client info
    clients = keycloak_get_clients(kc, {'clientId': client_id})
    client_nid = clients[0]['id']
    client_secret = keycloak_get_client_secret(kc, client_nid)
    # Create client scope
    if not keycloak_create_client_scope(kc, client_id+'-scope'):
        return False
    # __Create mapper__
    # Get scope id
    scope_id = keycloak_get_client_scope_id(kc, client_id+'-scope')
    #Create mapper
    keycloak_create_scope_mapper(kc, scope_id, client_id+'-audience', client_id)
    # _________________
    # Add the scope to the client
    keycloak_add_scope_to_client(kc, client_nid, scope_id)
    # Create client roles
    session = r.session()
    for role in roles:
        res = keycloak_create_client_role(kc, client_nid, role, session)
        if res:
            print(role)
    

    # Give user default roles
    for default_role in default_user_role:
        res = keycloak_add_user_to_client_role(kc, client_nid, username, default_role, session)
        if res:
            print(default_role)
    
    session.close()

    return client_id, client_secret
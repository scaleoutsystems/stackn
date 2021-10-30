"""
from django.conf import settings
import requests as r
import logging
import jwt
import time
import json

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


def keycloak_output(res, caller):
    success = False
    if res:
        success = True
    return {"success": success, "info":{"status_code": res.status_code, "msg": res.text, "caller": caller}}

def keycloak_user_auth(username, password, client_id, admin_url, realm):
    token_url = '{}/realms/{}/protocol/openid-connect/token'.format(admin_url, realm)
    req = {'client_id': client_id,
           'grant_type': 'password',
           'username': username,
           'password': password}
    res = r.post(token_url, data=req, verify=settings.OIDC_VERIFY_SSL)
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
                            auth=r.auth.HTTPBasicAuth(client_id, client_secret),
                            verify=settings.OIDC_VERIFY_SSL) 
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
    res = r.post(token_url, data=req, verify=settings.OIDC_VERIFY_SSL)
    token = res.json()['access_token']
    refresh_token = res.json()['refresh_token']
    discovery_url = settings.OIDC_OP_REALM_AUTH+'/'+settings.KC_REALM
    res = r.get(discovery_url, verify=settings.OIDC_VERIFY_SSL)
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

def keycloak_get_detailed_user_info(request, aud='account', renew_token_if_expired=True):
    if not ('oidc_access_token' in request.session):
        logger.warn('No access token in request session -- unable to authorize user.')
        return []

    access_token = request.session['oidc_access_token']
    user_json = []
    discovery_url = settings.OIDC_OP_REALM_AUTH+'/'+settings.KC_REALM
    res = r.get(discovery_url, verify=settings.OIDC_VERIFY_SSL)
    if res:
        realm_info = res.json()
        public_key = '-----BEGIN PUBLIC KEY-----\n'+realm_info['public_key']+'\n-----END PUBLIC KEY-----'
    else:
        print('Failed to discover realm settings: '+settings.KC_REALM)
        return None
    try:
        # print('Decoding user token: {}'.format(request.user))
        # print(access_token)
        user_json = jwt.decode(access_token, public_key, algorithms='RS256', audience=aud)
        # print('Successfully decoded token.')
        # print('Token expires: {}'.format(request.session['oidc_id_token_expiration']))
        # print('Time now: {}'.format(time.time()))
        # time_left = (request.session['oidc_id_token_expiration']-time.time())/60
        # print(time_left)
        # print(request.session.keys())
        logger.debug(user_json)
    except jwt.ExpiredSignatureError:
        print('Token has expired.')
        print('Attempting renewal.')
        if renew_token_if_expired:
            kc = keycloak_init()
            token, refresh_token, token_url, public_key = keycloak_token_exchange_studio(kc, request.user.username)
            request.session['oidc_access_token'] = token
            request.session.save()
            return keycloak_get_detailed_user_info(request, aud='account', renew_token_if_expired=False)

    except Exception as err:
        print('Failed to authenticate user.')
        print('Reason: ')
        print(err)
        print(request.session.keys())
        print(request.session['oidc_id_token_expiration'])
        print(request.session['oidc_id_token'])
        print(time.time())

        
    return user_json

def keycloak_get_user_roles(request, resource, aud='account'):
    ''' 
    Checks if user has on of the roles in 'role' for resource given by 'resource'
    Variable 'role' has to be iterable.
    '''
    user_info = keycloak_get_detailed_user_info(request, aud)
    if user_info:
        try:
            resource_info = user_info['resource_access'][resource]
        except:
            logger.info('User not authorized to access resource {}'.format(resource))
            return False

        return resource_info['roles']

    return []

def keycloak_verify_user_role(request, resource, roles, aud='account'):
    ''' 
    Checks if user has on of the roles in 'role' for resource given by 'resource'
    Variable 'role' has to be iterable.
    '''
    user_info = keycloak_get_detailed_user_info(request, aud)
    if user_info:
        try:
            resource_info = user_info['resource_access'][resource]
        except:
            logger.info('User not authorized to access resource {}'.format(resource))
            return False

        resource_roles = resource_info['roles']
        for role in roles:
          if role in resource_roles:
              return True
    
    return False

def keycloak_update_client(kc, client_id, client_rep):
    get_clients_url = '{}/admin/realms/{}/clients/{}'.format(kc.admin_url, kc.realm, client_id)
    print(client_rep[0])
    res = r.put(get_clients_url, headers={'Authorization': 'bearer '+kc.token}, json=client_rep[0], verify=settings.OIDC_VERIFY_SSL)
    if res:
        print("UPDATED CLIENT")
        success = True
    else:
        print('Failed to update client.')
        print('Request returned status: '+str(res.status_code))
        print(res.text)
        success = False

    return {"success": success, "info":{"status_code": res.status_code, "msg": res.text}}

def keycloak_get_clients(kc, payload):
    get_clients_url = '{}/admin/realms/{}/clients'.format(kc.admin_url, kc.realm)
    res = r.get(get_clients_url, headers={'Authorization': 'Bearer '+kc.token}, params=payload, verify=settings.OIDC_VERIFY_SSL)
    clients = []
    if res:
        clients = res.json()
        success = True
        # return clients
    else:
        # print('Failed to fetch clients.')
        # print('Request returned status: '+str(res.status_code))
        # print(get_clients_url)
        # print('Payload: ')
        # print(payload)
        # print({'Authorization': 'Bearer '+kc.token})
        # print(res.text)
        success = False
    return clients, keycloak_output(res, "keycloak_get_clients")

def keycloak_delete_client(kc, client_id):
    # Get id (not clientId)
    clients, res = keycloak_get_clients(kc, {'clientId': client_id})
    try:
        client_nid = clients[0]['id']
    except:
        print('Cannot find client with clientId: {}'.format(client_id))
        return False
    # Delete client
    delete_client_url = '{}/admin/realms/{}/clients/{}'.format(kc.admin_url, kc.realm, client_nid)
    res = r.delete(delete_client_url,
                   headers={'Authorization': 'bearer '+kc.token},
                   verify=settings.OIDC_VERIFY_SSL)
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
                  'redirectUris': redirectUris,
                  'fullScopeAllowed': "False"}
    logger.debug("Client rep: ")
    logger.debug(client_rep)

    res = r.post(create_client_url,
                 json=client_rep,
                 headers={'Authorization': 'bearer '+kc.token},
                 verify=settings.OIDC_VERIFY_SSL)
    if res:
        logger.debug('Created new client with clientId {}'.format(client_id))
        logger.debug('Status code returned: {}'.format(res.status_code))
        success = True
    else:
        print(client_rep)
        print(create_client_url)
        success = False

    return keycloak_output(res, "keycloak_create_client")

def keycloak_client_allow_implicit_flow(kc, client_id):
    clients, res_json = keycloak_get_clients(kc, {'clientId': client_id})
    if not res_json['success']:
        return res_json

    try:
        clients[0]['implicitFlowEnabled'] = "True"
    except Exception as err:
        res_json['success'] = False
        res_json['info']['msg'] = "Failed to set implicit flow in client rep."
        return res_json

    
    res = keycloak_update_client(kc, clients[0]['id'], clients)
    
    if res['success']:
        print("Allowed implicit flow for client: {}.".format(client_id))
    else:
        print("Failed to allow implicit flow for client: {}.".format(client_id))
    return res

def keycloak_add_client_valid_redirect(kc, client_id, redirectUri):    
    clients, res_json = keycloak_get_clients(kc, {'clientId': client_id})
    if not res_json['success']:
        return res_json

    try:
        clients[0]['redirectUris'].append(redirectUri)
    except Exception as err:
        print("Failed to find redirectUris in client[0]")
        print(err)
        res_json['success'] = False
        res_json['info']['msg'] = "Failed to find redirectUris in client[0]"
        return res_json

    
    res = keycloak_update_client(kc, clients[0]['id'], clients)
    
    if res['success']:
        print("Added valid redirect URI: {} to client: {}.".format(redirectUri, client_id))
    else:
        print("Failed to add valid redirect URI: {} to client: {}.".format(redirectUri, client_id))
    return res

def keycloak_remove_client_valid_redirect(kc, client_id, redirectUri):
    print("GETTING CLIENT: {}".format(client_id))
    clients, res = keycloak_get_clients(kc, {'clientId': client_id})
    print(clients[0]['redirectUris'])
    try:
        clients[0]['redirectUris'].remove(redirectUri)
    except:
        print("WARN: Client didn't contain redirect URI.")
        return False
    res = keycloak_update_client(kc, clients[0]['id'], clients)
    if res:
        print("Removed redirect URI: {} to client: {}.".format(redirectUri, client_id))
    else:
        print("Failed to remove valid redirect URI: {} to client: {}.".format(redirectUri, client_id))
    return res

def keycloak_get_client_secret(kc, client_nid):
    get_client_secret_url = '{}/admin/realms/{}/clients/{}/client-secret'.format(kc.admin_url, kc.realm, client_nid)
    res = r.get(get_client_secret_url, headers={'Authorization': 'bearer '+kc.token}, verify=settings.OIDC_VERIFY_SSL)
    client_secret = []
    if res:
        client_secret = res.json()
        if 'value' in client_secret:
            client_secret = client_secret['value']

    # print('Failed to get client secret for client: '+client_nid)
    # print('Status code: '+str(res.status_code))
    # print(res.text)
    return client_secret, keycloak_output(res, "keycloak_get_client_secret")

def keycloak_get_client_secret_by_id(kc, client_id):
    clients, res = keycloak_get_clients(kc, {'clientId': client_id})
    client_nid = clients[0]['id']
    return keycloak_get_client_secret(kc, client_nid)

def keycloak_create_client_scope(kc, scope_name, protocol='openid-connect', 
                                                 attributes={'include.in.token.scope': 'true',
                                                             'display.on.consent.screen': 'true'}):
    client_scope_url = '{}/admin/realms/{}/client-scopes'.format(kc.admin_url, kc.realm)
    client_scope_body = {'name': scope_name,
                        'protocol': 'openid-connect',
                        'attributes': {'include.in.token.scope': 'true', 'display.on.consent.screen': 'true'}}
    res = r.post(client_scope_url,
                 json=client_scope_body,
                 headers={'Authorization': 'bearer '+kc.token},
                 verify=settings.OIDC_VERIFY_SSL)
    success = False
    if res:
        success = True
    # else:
    #     print('Failed to create client scope '+scope_name)
    #     print('Status code: '+str(res.status_code))
    #     print(res.text)
    #     return False
    return keycloak_output(res, "keycloak_create_client_scope")

def keycloak_get_client_scope_id(kc, scope_name):
    client_scope_url = '{}/admin/realms/{}/client-scopes'.format(kc.admin_url, kc.realm)
    res = r.get(client_scope_url, headers={'Authorization': 'bearer '+kc.token}, verify=settings.OIDC_VERIFY_SSL)
    # TODO: There has to be a better way to fetch scope id than to loop over all scopes...!?
    success = False
    scope_id = []
    if res:
        success = True
        scopes = res.json()
        scope_id = None
        for scope in scopes:
            if scope['name'] == scope_name:
                scope_id = scope['id']
        # return scope_id
    # else:
    #     print('Failed to get client scopes.')
    #     print('Status code: '+str(res.status_code))
    #     print(res.text)
    #     return False
    return scope_id, keycloak_output(res, "keycloak_get_client_scope_id")

def keycloak_delete_client_scope(kc, scope_id):
    # /{realm}/client-scopes/{id}
    client_scope_url = '{}/admin/realms/{}/client-scopes/{}'.format(kc.admin_url, kc.realm, scope_id)
    res = r.delete(client_scope_url,
                   headers={'Authorization': 'bearer '+kc.token},
                   verify=settings.OIDC_VERIFY_SSL)
    if res:
        return True
    else:
        print('Failed to delete client scope '.format(scope_id))
        print('Status code: '+str(res.status_code))
        print(res.text)
        return False


# Audience mapper
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
                 headers={'Authorization': 'bearer '+kc.token},
                 verify=settings.OIDC_VERIFY_SSL)
    success = False
    if res:
        success = True

    return keycloak_output(res, "keycloak_create_scope_mapper")

# User role mapper
def keycloak_create_scope_mapper_roles(kc, scope_id, client_id, mapper_name, claim_name):
    create_client_scope_mapper_url = '{}/admin/realms/{}/client-scopes/{}/protocol-mappers/models'.format(kc.admin_url, kc.realm, scope_id)
    scope_mapper = {'name': mapper_name,
                    'protocol': 'openid-connect',
                    'protocolMapper': 'oidc-usermodel-client-role-mapper',
                    "consentRequired": False,
                    "config": {
                        "multivalued": "true",
                        "id.token.claim": "true",
                        "access.token.claim": "true",
                        "userinfo.token.claim": "true",
                        "usermodel.clientRoleMapping.clientId": client_id,
                        "claim.name": claim_name,
                        "jsonType.label": "String"
                    }}

    res = r.post(create_client_scope_mapper_url,
                 json=scope_mapper,
                 headers={'Authorization': 'bearer '+kc.token},
                 verify=settings.OIDC_VERIFY_SSL)
    success = False
    if res:
        success = True

    return keycloak_output(res, "keycloak_create_scope_mapper_roles")

def keycloak_add_scope_to_client(kc, client_id, scope_id):
    add_default_scope_url = '{}/admin/realms/{}/clients/{}/default-client-scopes/{}'.format(kc.admin_url, kc.realm, client_id, scope_id)
    res = r.put(add_default_scope_url,
                headers={'Authorization': 'bearer '+kc.token},
                verify=settings.OIDC_VERIFY_SSL)
    success = False
    if res:
        success = True
    return keycloak_output(res, "keycloak_add_scope_to_client")    

def keycloak_create_client_role(kc, client_nid, role_name, session):
    client_role_url = '{}/admin/realms/{}/clients/{}/roles'.format(kc.admin_url, kc.realm, client_nid)
    role_rep = {'name': role_name}
    res = session.post(client_role_url,
                      json=role_rep,
                      headers={'Authorization': 'bearer '+kc.token},
                      verify=settings.OIDC_VERIFY_SSL)
    success = False
    if res:
        success = True
    # else:
    #     print('Failed to create client role.')
    #     print('Status code: '+str(res.status_code))
    #     print(res.text)
    #     return False
    return keycloak_output(res, "keycloak_create_client_role")

def keycloak_get_user_id(kc, username):
    user_id = []
    get_users_url =  '{}/admin/realms/{}/users'.format(kc.admin_url, kc.realm)
    res = r.get(get_users_url,
                params={'username': username},
                headers={'Authorization': 'bearer '+kc.token},
                verify=settings.OIDC_VERIFY_SSL).json()
    

    if not res:
        print('Failed to get user id.')
        res_json = {"success": False, "info": {"status_code":"-1", "msg": "Failed to get user id.", "caller": "keycloak_get_user_id"}}
        return user_id, res_json

    if len(res) != 1:
        print("Didn't find user: "+username+" in realm: "+kc.realm)
        res_json = {"success": False, "info": {"status_code":"-1", "msg": "Didn't find user: "+username+" in realm: "+kc.realm, "caller": "keycloak_get_user_id"}}
        return user_id, res_json

    try:
        user_id = res[0]['id']
    except Exception as err:
        res_json = {"success": False, "info": {"status_code":"-1", "msg": "Failed to find id in user: "+username+" in realm: "+kc.realm, "caller": "keycloak_get_user_id"}}
        return user_id, res_json
    
    res_json = {"success": True, "info": {"status_code":"200", "msg": "", "caller": "keycloak_get_user_id"}}
    return user_id, res_json

def keycloak_get_client_role_id(kc, role_name, client_nid, session=[]):
    if not session:
        session = r.session()
    client_role_url = '{}/admin/realms/{}/clients/{}/roles'.format(kc.admin_url, kc.realm, client_nid)
    res = r.get(client_role_url,
                headers={'Authorization': 'bearer '+kc.token},
                verify=settings.OIDC_VERIFY_SSL)
    success = True
    client_role_id = []
    if res:
        try:
            client_roles = res.json()
            for role in client_roles:
                if role['name'] == role_name:
                    client_role_id = role['id']
        except Exception as err:
            print("Failed to find role_id in client.")
            print(err)
            success = False
    else:
        print('Failed to get client role id.')
        print('Status code: '+str(res.status_code))
        print(res.text)
        success = False
    
    return client_role_id, keycloak_output(res, "keycloak_get_client_role_id")

def keycloak_add_user_to_client_role(kc, client_nid, username, role_name, session=[], action='add'):
    if not session:
        session = r.session()
    user_id, res_json = keycloak_get_user_id(kc, username)
    if not res_json['success']:
        return res_json

    add_user_to_role_url = '{}/admin/realms/{}/users/{}/role-mappings/clients/{}'.format(kc.admin_url,
                                                                                         kc.realm,
                                                                                         user_id,
                                                                                         client_nid)
    
    # Get role id
    role_id, res_json = keycloak_get_client_role_id(kc, role_name, client_nid, session)
    if not res_json['success']:
        return res_json

    role_rep = [{'name': role_name, 'id': role_id}]
    if action=='add':
        print(add_user_to_role_url)
        res = session.post(add_user_to_role_url,
                           json=role_rep,
                           headers={'Authorization': 'bearer '+kc.token},
                           verify=settings.OIDC_VERIFY_SSL)
    elif action=='delete':
        import json
        print('deleting...')
        print(add_user_to_role_url)
        print(json.dumps(role_rep))
        res = r.delete(add_user_to_role_url,
                       json=role_rep,
                       headers={'Authorization': 'bearer '+kc.token},
                       verify=settings.OIDC_VERIFY_SSL)
    success = True
    if not res:
        success = False
    # else:
    #     print('Failed to {} user {} to client role {}.'.format(action, username, role_name))
    #     print('Status code: '+str(res.status_code))
    #     print(res.text)
    #     return False
    return keycloak_output(res, "keycloak_add_user_to_client_role")

def keycloak_add_role_to_user(clientId, username, role, action='add'):
    logger.info('Adding role {} to user {}. Client is {}.'.format(role, username, clientId))
    kc = keycloak_init()
    # Get client id
    clients, res_json = keycloak_get_clients(kc, {'clientId': clientId})
    if not res_json['success']:
        return res_json
    client_nid = clients[0]['id']
    # Add role to user
    res_json = keycloak_add_user_to_client_role(kc, client_nid, username, role, action=action)
    return res_json

def keycloak_remove_role_from_user(clientId, username, roles):
    kc = keycloak_init()
    clients, res = keycloak_get_clients(kc, {'clientId': clientId})
    client_nid = clients[0]['id']
    for role in roles:
        logger.info('Removing role {} from user {}. Client is {}.'.format(role, username, clientId))


def keycloak_setup_base_client(base_url, client_id, username, roles=['default'], default_user_role=['default']):
    client_secret = []
    kc = keycloak_init()

    res_json = keycloak_create_client(kc, client_id, base_url)
    # Create client
    if not res_json['success']:
        return client_id, client_secret, res_json
    
    # Fetch client info
    clients, res_json = keycloak_get_clients(kc, {'clientId': client_id})
    if not res_json['success']:
        return client_id, client_secret, res_json

    try:
        client_nid = clients[0]['id']
    except Exception as err:
        print("keycloak_setup_base_client:ERROR: Didn't find client_nid in client_id.")
        print(err)
        res_json['success'] = False
        res_json['info']['msg'] = "Didn't find client_nid in client_id."
        res_json['info']['caller'] = "keycloak_setup_base_client"
        return client_id, client_secret, res_json

    client_secret, res_json = keycloak_get_client_secret(kc, client_nid)
    if not res_json['success']:
        return client_id, client_secret, res_json

    # Create client scope
    res_json = keycloak_create_client_scope(kc, client_id+'-scope')
    if not res_json['success']:
        return client_id, client_secret, res_json

    # __Create mapper__
    # Get scope id
    scope_id, res_json = keycloak_get_client_scope_id(kc, client_id+'-scope')
    if not res_json['success']:
        return client_id, client_secret, res_json

    #Create mapper
    res_json = keycloak_create_scope_mapper(kc, scope_id, client_id+'-audience', client_id)
    if not res_json['success']:
        return client_id, client_secret, res_json
    # _________________
   

    # Add the scope to the client
    res_json = keycloak_add_scope_to_client(kc, client_nid, scope_id)
    if not res_json['success']:
        return client_id, client_secret, res_json

    # Create client roles
    session = r.session()
    for role in roles:
        res_json = keycloak_create_client_role(kc, client_nid, role, session)
        if not res_json['success']:
            return client_id, client_secret, res_json
    
    # Give user default roles
    for default_role in default_user_role:
        res_json = keycloak_add_user_to_client_role(kc, client_nid, username, default_role, session=session)
        if not res_json['success']:
            return client_id, client_secret, res_json
    session.close()

    res_json = {"success": True,
                "info": {
                    "msg": "",
                    "status_code": "200",
                    "caller": "keycloak_setup_base_client"
                }}
    return client_id, client_secret, res_json


"""
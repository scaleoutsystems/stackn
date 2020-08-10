from django.conf import settings
import logging
import requests as r

logger = logging.getLogger(__file__)

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

def keycloak_get_clients(kc, payload):
    get_clients_url = '{}/admin/realms/{}/clients'.format(kc.admin_url, kc.realm)
    res = r.get(get_clients_url, headers={'Authorization': 'bearer '+kc.token}, params=payload)
    if res:
        clients = res.json() 
        return clients
    else:
        print('Failed to fetch clients.')
        print('Request returned status: '+res.status_code)
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
        print('Status code: '+res.status_code)
        print(res.text)

def keycloak_create_client(kc, client_id, base_url, root_url=[], redirectUris=[]):
    if not root_url:
        root_url = base_url
    if not redirectUris:
        redirectUris = [base_url+'/*']
    create_client_url = '{}/admin/realms/{}/clients'.format(kc.admin_url, kc.realm)

    client_rep = {'clientId': client_id,
                  'baseUrl': base_url,
                  'rootUrl': root_url,
                  'redirectUris': redirectUris}
    res = r.post(create_client_url, json=client_rep, headers={'Authorization': 'bearer '+kc.token})
    if res:
        return True
    else:
        print('Failed to create new client.')
        print('Status code: '+res.status_code)
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
    print('Status code: '+res.status_code)
    print(res.text)

def keycloak_create_client_scope(kc, scope_name, protocol='openid-connect', 
                                                 attributes={'include.in.token.scope': 'true',
                                                             'display.on.consent.screen': 'true'}):
    client_scope_url = '{}/admin/realms/{}/client-scopes'.format(kc.admin_url, kc.realm)
    client_scope_body = {'name': scope_name,
                        'protocol': 'openid-connect',
                        'attributes': {'include.in.token.scope': 'true', 'display.on.consent.screen': 'true'}}
    res = r.post(client_scope_url, client_scope_body)
    if res:
        return True
    else:
        print('Failed to create client scope '+scope_name)
        print('Status code: '+res.status_code)
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
        print('Status code: '+res.status_code)
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
        print('Status code: '+res.status_code)
        print(res.text)
        return False

def keycloak_add_scope_to_client(kc, client_id, scope_id):
    add_default_scope_url = '{}/admin/realms/{}/clients/{}/default-client-scopes/{}'.format(kc.admin_url, kc.realm, client_id, scope_id)
    res = r.put(add_default_scope_url, headers={'Authorization': 'bearer '+kc.token})
    if res:
        return True
    else:
        print('Failed to add scope to client.')
        print('Status code: '+res.status_code)
        print(res.text)
        return False        

def keycloak_create_client_role(kc, client_nid, role_name):
    client_role_url = '{}/admin/realms/{}/clients/{}/roles'.format(kc.admin_url, kc.realm, client_nid)
    role_rep = {'name': role_name}
    res = r.post(client_role_url, json=role_rep, headers={'Authorization': 'bearer '+kc.token})
    if res:
        return True
    else:
        print('Failed to create client role.')
        print('Status code: '+res.status_code)
        print(res.text)
        return False

def keycloak_get_user_id(kc, username):
    get_users_url =  '{}/admin/realms/{}/users'.format(kc.admin_url, kc.realm)
    res = r.get(get_users_url, params={'username': username}, headers={'Authorization': 'bearer '+kc.token}).json()
    if not res:
        print('Failed to get user id.')
        print('Status code: '+res.status_code)
        print(res.text)
        return False
    if len(res) != 1:
        print("Didn't find user: "+username+" in realm: "+kc.realm)
        return False
    res = res[0]
    return res['id']

def keycloak_get_client_role_id(kc, role_name, client_nid):
    client_role_url = '{}/admin/realms/{}/clients/{}/roles'.format(kc.admin_url, kc.realm, client_nid)
    res = r.get(client_role_url, headers={'Authorization': 'bearer '+kc.token})
    if res:
        client_roles = res.json()
        for role in client_roles:
            if role['name'] == role_name:
                return role['id']
    else:
        print('Failed to get client role id.')
        print('Status code: '+res.status_code)
        print(res.text)
        return False

def keycloak_add_user_to_client_role(kc, client_nid, username, role_name):
    user_id = keycloak_get_user_id(kc, username)
    add_user_to_role_url = '{}/admin/realms/{}/users/{}/role-mappings/clients/{}'.format(kc.admin_url,
                                                                                         kc.realm,
                                                                                         user_id,
                                                                                         client_nid)
    
    # Get role id
    role_id = keycloak_get_client_role_id(kc, role_name, client_nid)

    role_rep = [{'name': role_name, 'id': role_id}]
    res = r.post(add_user_to_role_url, json=role_rep, headers={'Authorization': 'bearer '+kc.token})
    if res:
        return True
    else:
        print('Failed to add user {} to client role {}.'.format(username, role_name))
        print('Status code: '+res.status_code)
        print(res.text)
        return False

def setup_labs_client(request, req_user, session):

    HOST = settings.DOMAIN
    RELEASE_NAME = str(session.slug)
    
    URL = 'https://'+RELEASE_NAME+'.'+HOST

    kc = keycloak_init()

    # Create client
    if not keycloak_create_client(kc, RELEASE_NAME, URL):
        return False

    # Fetch client info
    clients = keycloak_get_clients(kc, {'clientId': RELEASE_NAME})
    client_nid = clients[0]['id']
    client_secret = keycloak_get_client_secret(kc, client_nid)

    # Create client scope
    if not keycloak_create_client_scope(kc, RELEASE_NAME+'-scope'):
        return False

    # __Create mapper__
    # Get scope id
    scope_id = keycloak_get_client_scope_id(kc, RELEASE_NAME+'-scope')
    #Create mapper
    keycloak_create_scope_mapper(kc, scope_id, RELEASE_NAME+'-audience', RELEASE_NAME)
    # _________________

    # Add the scope to the client
    keycloak_add_scope_to_client(kc, client_nid, scope_id)
    
    # Create client role
    keycloak_create_client_role(kc, client_nid, RELEASE_NAME+'-role')

    # Add user to client role
    keycloak_add_user_to_client_role(kc, client_nid, req_user, RELEASE_NAME+'-role')

    return RELEASE_NAME, client_secret

def create_session_resources(request, user, session, prefs, project):

    print("1; going for the dispatch!")

    client_id, client_secret = setup_labs_client(request, user, session)

    parameters = {'release': str(session.slug),
                  'chart': session.chart,
                  'global.domain': settings.DOMAIN,
                  'project.name': project.slug,
                  'gatekeeper.realm': settings.KC_REALM,
                  'gatekeeper.client_secret': client_secret,
                  'gatekeeper.client_id': client_id,
                  'gatekeeper.auth_endpoint': settings.OIDC_OP_REALM_AUTH
                  }
    parameters.update(prefs)

    url = settings.CHART_CONTROLLER_URL + '/deploy'

    retval = r.get(url, parameters)
    print("CREATE_SESSION:helm chart creator returned {}".format(retval))

    if retval.status_code >= 200 or retval.status_code < 205:
        return True

    return False


def delete_session_resources(session):
    print("trying to delete {}".format(session.slug))
    parameters = {'release': str(session.slug)}
    retval = r.get(settings.CHART_CONTROLLER_URL + '/delete', parameters)
    kc = keycloak_init()
    keycloak_delete_client(kc, str(session.slug))
    if retval:
        print('delete success!')
        return True
    print('delete failed!?')
    return False

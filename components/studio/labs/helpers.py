from django.conf import settings
import logging
import requests as r

logger = logging.getLogger(__file__)

def delete_keycloak_client(client_id):
    realm = settings.KC_REALM
    user = settings.KC_USERNAME
    password = settings.KC_PASS
    admin_url = 'http://keycloak-http/auth'
    # Get Token

    token_url = '{}/realms/{}/protocol/openid-connect/token'.format(admin_url, realm)

    req = {'client_id': 'admin-cli',
          'grant_type': 'password',
          'username': user,
          'password': password}

    res = r.post(token_url, data=req)

    token =res.json()['access_token']
    
    get_clients_url = '{}/admin/realms/{}/clients'.format(admin_url, realm)
    res = r.get(get_clients_url, headers={'Authorization': 'bearer '+token})
    clients = res.json()
    lab_client = []
    for client in clients:
        if client['clientId'] == client_id:
            lab_client = client
    # Create client
    delete_client_url = '{}/admin/realms/{}/clients/{}'.format(admin_url, realm, lab_client['id'])

    res = r.delete(delete_client_url, headers={'Authorization': 'bearer '+token})

def create_keycloak_client(request, req_user, session):

    HOST = settings.DOMAIN
    RELEASE_NAME = str(session.slug)

    URL = 'https://'+RELEASE_NAME+'.'+HOST

    admin_url = settings.KC_ADMIN_URL
    realm = settings.KC_REALM

    user = settings.KC_USERNAME
    password = settings.KC_PASS

    # Get Token

    token_url = '{}/realms/{}/protocol/openid-connect/token'.format(admin_url, realm)

    req = {'client_id': 'admin-cli',
          'grant_type': 'password',
          'username': user,
          'password': password}

    res = r.post(token_url, data=req)

    token =res.json()['access_token']

    # Create client
    create_client_url = '{}/admin/realms/{}/clients'.format(admin_url, realm)

    client_rep = {'clientId': RELEASE_NAME,
                  'baseUrl': URL,
                  'rootUrl': URL,
                  'redirectUris': [URL+'/*']}
    print(client_rep)
    print(create_client_url)
    res = r.post(create_client_url, json=client_rep, headers={'Authorization': 'bearer '+token})
    print(res.text)
    # print(dir(res))

    # Fetch client info

    get_clients_url = '{}/admin/realms/{}/clients'.format(admin_url, realm)
    res = r.get(get_clients_url, headers={'Authorization': 'bearer '+token})
    clients = res.json()
    lab_client = []
    for client in clients:
        if client['clientId'] == RELEASE_NAME:
            lab_client = client

    # print(lab_client)
    get_client_secret_url = '{}/admin/realms/{}/clients/{}/client-secret'.format(admin_url, realm, lab_client['id'])
    res = r.get(get_client_secret_url, headers={'Authorization': 'bearer '+token})
    client_secret = res.json()['value']
    print(client_secret)

    # Create client scope
    create_client_scope_url = '{}/admin/realms/{}/client-scopes'.format(admin_url, realm)
    client_scope_body = {'name': RELEASE_NAME+'-scope'}
    res = r.post(create_client_scope_url, client_scope_body)

    # Create client scope
    client_scope_url = '{}/admin/realms/{}/client-scopes'.format(admin_url, realm)
    # protocolMapper = {'name': RELEASE_NAME+'audience'}
    client_scope_body = {'name': RELEASE_NAME+'-scope',
                        'protocol': 'openid-connect',
                        'attributes': {'include.in.token.scope': 'true', 'display.on.consent.screen': 'true'}}



    res = r.post(client_scope_url, json=client_scope_body, headers={'Authorization': 'bearer '+token})
    print(res.text)
    # Create mapper

    # Get scope id
    res = r.get(client_scope_url, headers={'Authorization': 'bearer '+token})
    scopes = res.json()
    scope_id = None
    for scope in scopes:
        if scope['name'] == RELEASE_NAME+'-scope':
            scope_id = scope['id']

    print(scope_id)
    # /{realm}/client-scopes/{id}/protocol-mappers/models
    create_client_scope_mapper_url = '{}/admin/realms/{}/client-scopes/{}/protocol-mappers/models'.format(admin_url, realm, scope_id)
    scope_mapper = {'name': RELEASE_NAME+'-audience',
                    'protocol': 'openid-connect',
                    'protocolMapper': 'oidc-audience-mapper',
                    'consentRequired': False,
                    'config': {'included.client.audience': RELEASE_NAME, 'id.token.claim': 'false', 'access.token.claim': 'true'}}

    res = r.post(create_client_scope_mapper_url, json=scope_mapper, headers={'Authorization': 'bearer '+token})
    print(res.text)
    
    # Add the scope to the client
    get_client_scopes_url = '{}/admin/realms/{}/client-scopes'.format(admin_url, realm)
    client_scopes = r.get(get_client_scopes_url, headers={'Authorization': 'bearer '+token}).json()
    scope_id = None
    for scope in client_scopes:
        if scope['name'] == RELEASE_NAME+'-scope':
            print(scope)
            scope_id = scope['id']

    add_default_scope_url = '{}/admin/realms/{}/clients/{}/default-client-scopes/{}'.format(admin_url, realm, lab_client['id'], scope_id)
    res = r.put(add_default_scope_url, headers={'Authorization': 'bearer '+token})
    
    # Create client role
    # POST /{realm}/clients/{id}/roles
    add_client_role_url = '{}/admin/realms/{}/clients/{}/roles'.format(admin_url, realm, lab_client['id'])
    role_rep = {'name': RELEASE_NAME+'-role'}
    r.post(add_client_role_url, json=role_rep, headers={'Authorization': 'bearer '+token})
    

    # Get user id
    get_users_url =  '{}/admin/realms/{}/users'.format(admin_url, realm)
    kc_user = r.get(get_users_url, params={'username': req_user}, headers={'Authorization': 'bearer '+token}).json()
    # print(user.text)
    kc_user = kc_user[0]
    print(kc_user)
    # Add user to client role
    #  /{realm}/users/{id}/role-mappings/clients/{client}
    user_id = kc_user['id']#'68e81a02-c680-45c2-a22d-67922cf90165'
    print(user_id)
    add_user_to_role_url = '{}/admin/realms/{}/users/{}/role-mappings/clients/{}'.format(admin_url,
                                                                                          realm,
                                                                                          user_id,
                                                                                          lab_client['id'])
    
    # Get role id
    client_roles = r.get(add_client_role_url, headers={'Authorization': 'bearer '+token}).json()
    for role in client_roles:
        if role['name'] == RELEASE_NAME+'-role':
            role_id = role['id']

    role_rep = [{'name': RELEASE_NAME+'-role', 'id': role_id}]
    r.post(add_user_to_role_url, json=role_rep, headers={'Authorization': 'bearer '+token})


    return RELEASE_NAME, client_secret

def create_session_resources(request, user, session, prefs, project):

    print("1; going for the dispatch!")

    client_id, client_secret = create_keycloak_client(request, user, session)

    parameters = {'release': str(session.slug),
                  'chart': session.chart,
                  'global.domain': settings.DOMAIN,
                  'project.name': project.slug,
                  'gatekeeper.realm': settings.KC_REALM,
                  'gatekeeper.client_secret': client_secret,
                  'gatekeeper.client_id': client_id
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
    delete_keycloak_client(str(session.slug))
    if retval:
        print('delete success!')
        return True
    print('delete failed!?')
    return False

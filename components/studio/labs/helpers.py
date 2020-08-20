from django.conf import settings
import logging
import requests as r
import modules.keycloak_lib as keylib
import json
import yaml
logger = logging.getLogger(__file__)

def create_user_settings(user):
    kc = keylib.keycloak_init()
    token, refresh_token, token_url, public_key = keylib.keycloak_token_exchange_studio(kc, user)
    user_settings = dict()
    user_settings['access_token'] = token
    user_settings['refresh_token'] = refresh_token
    user_settings['public_key'] = public_key
    user_settings['keycloak_url'] = settings.KC_ADMIN_URL.replace('/auth', '')
    user_settings['studio_url'] = 'https://'+settings.DOMAIN
    return json.dumps(user_settings)

def create_session_resources(request, user, session, prefs, project):

    print("1; going for the dispatch!")

    HOST = settings.DOMAIN
    RELEASE_NAME = str(session.slug)
    
    URL = 'https://'+RELEASE_NAME+'.'+HOST
    client_id, client_secret = keylib.keycloak_setup_base_client(URL, RELEASE_NAME, user)

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
    
    kc = keylib.keycloak_init()
    keylib.keycloak_delete_client(kc, str(session.slug))
    
    scope_id = keylib.keycloak_get_client_scope_id(kc, str(session.slug)+'-scope')
    keylib.keycloak_delete_client_scope(kc, scope_id)

    if retval:
        print('delete success!')
        return True
    print('delete failed!?')
    return False

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

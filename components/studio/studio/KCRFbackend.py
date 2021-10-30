from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
import jwt
import requests as r
#import modules.keycloak_lib as keylib

"""
class KeycloakAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token_str = request.META['HTTP_AUTHORIZATION']
        access_token = token_str.replace('Token ', '')
        discovery_url = settings.OIDC_OP_REALM_AUTH+'/'+settings.KC_REALM
        res = r.get(discovery_url, verify=settings.OIDC_VERIFY_SSL)
        if res:
            realm_info = res.json()
            public_key = '-----BEGIN PUBLIC KEY-----\n'+realm_info['public_key']+'\n-----END PUBLIC KEY-----'
        else:
            print('Failed to discover realm settings: '+settings.KC_REALM)
            return None
        try:
            access_token_json = jwt.decode(access_token, public_key, algorithms='RS256', audience='studio-api')
        except:
            print('Failed to authenticate.')
            return None
        
        username = access_token_json['preferred_username']
        user = User.objects.get(username=username)
        request.session['oidc_access_token'] = access_token
        request.session.save()
        return (user, None)
    
"""
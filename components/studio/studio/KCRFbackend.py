from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
import modules.keycloak_lib as keylib
import jwt

class KeycloakAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token_str = request.META['HTTP_AUTHORIZATION']
        access_token = token_str.replace('Token ', '')
        public_key = b'-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAhJMHP2WFMfUGJ1NYRU2JOdorNC96iIdWljLK4v0CjnVi3jRnIBQsnPMB6n1e7Iju2jB0R5gZkWFfhVxnlnJAMyYVZG1/VB/uNL84hywCedFXe3sPj+DUfhZpGirOjGnbtxhdY9qxsYo97H++APNv78RMf3bD04MeRZksxkcJ0SKDJYuXuvPuLdVjwLTSuhY4VJiQcMRrB9DY5ZoQhJMK4fedXOlks1u1IO/w/ArMRl5NLNe18vX4y5r0aGb+PpeCH14YdOvD08NJ3USA7ZOiOKj70xb+SA+lOPBfqU3ijfQe3SbBF9mhdkwSISJIcoNYb8rjNH80ZkoMenh+rRE+wwIDAQAB\n-----END PUBLIC KEY-----'
        try:
            access_token_json = jwt.decode(access_token, public_key, algorithms='RS256', audience='account')
        except:
            print('Failed to authenticate.')
            return None
        
        username = access_token_json['preferred_username']
        user = User.objects.get(username=username)

        return (user, None)
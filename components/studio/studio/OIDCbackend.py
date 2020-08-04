from mozilla_django_oidc.auth import OIDCAuthenticationBackend

class OIDCbackend(OIDCAuthenticationBackend):
    def get_username(self, claims):
        print('local')
        print(claims)
        return claims.get('preferred_username')
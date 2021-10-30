from django.conf import settings
from django.utils.http import urlencode

"""
def keycloak_logout(request):
  logout_url = settings.OIDC_OP_LOGOUT_ENDPOINT
  return_to_url = request.build_absolute_uri(settings.LOGOUT_REDIRECT_URL)
  return logout_url + '?' + urlencode({'redirect_uri': return_to_url, 'client_id': settings.OIDC_RP_CLIENT_ID})
  
"""
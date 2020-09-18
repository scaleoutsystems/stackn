import modules.keycloak_lib as keylib

def get_permissions(request, project):
    
    rules = {
      'view': ['guest', 'member', 'admin'],
      'create': ['member', 'admin'],
      'update': ['member', 'admin'],
      'delete': ['admin']
    }

    user_roles = set(keylib.keycloak_get_user_roles(request, project, aud=project))
    
    user_permissions = dict()
    for rule in rules:
        user_permissions[rule] = bool(set(rules[rule]) & user_roles)
    
    return user_permissions
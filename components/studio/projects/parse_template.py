# from .models import Flavor, Environment
# from apps.models import Apps
# import apps.views as appviews


# import collections
# import json
# import time

# def create_resources_from_template(request, user, project, template):
#     decoder = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)
#     template = decoder.decode(template)
#     print(template)

#     if 'flavors' in template:
#         flavors = template['flavors']
#         for key, item in flavors.items():
#             flavor = Flavor(name=key,
#                             cpu_req=item['cpu']['requirement'],
#                             cpu_lim=item['cpu']['limit'],
#                             mem_req=item['mem']['requirement'],
#                             mem_lim=item['mem']['limit'],
#                             gpu_req=item['gpu']['requirement'],
#                             gpu_lim=item['gpu']['limit'],
#                             ephmem_req=item['ephmem']['requirement'],
#                             ephmem_lim=item['ephmem']['limit'],
#                             project=project)
#             flavor.save()
#     if 'environments' in template:
#         environments = template['environments']
#         for key, item in environments.items():
#             app = Apps.objects.get(slug=item['app'])
#             environment = Environment(name=key,
#                                       project=project,
#                                       repository=item['repository'],
#                                       image=item['image'],
#                                       app=app)
#             environment.save()
    
#     if 'apps' in template:
#         apps = template['apps']
#         for key, item in apps.items():
#             app_name = key
#             data = {
#                 "app_name": app_name,
#                 "app_action": "Create"
#             }
#             data = {**data, **item}
#             print("DATA TEMPLATE")
#             print(data)
#             res = appviews.create(request, user, project.slug, app_slug=item['slug'], data=data)
#             print(res)

#     time.sleep(2)
#     if 'settings' in template:
#         print("PARSING SETTINGS")
#         if 'project-S3' in template['settings']:
#             print("SETTING DEFAULT S3")
#             from .views import set_s3storage
#             set_s3storage(request, user, project.slug, s3storage=template['settings']['project-S3'])

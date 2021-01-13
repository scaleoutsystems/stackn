import os
import requests
import json
import subprocess
import uuid
import time

resources_url = os.environ['RESOURCES_URL']
cluster = os.environ['CLUSTER_NAME']
poll_pause = float(os.environ['POLL_PAUSE'])

volume_root = "/"
if "TELEPRESENCE_ROOT" in os.environ:
    volume_root = os.environ["TELEPRESENCE_ROOT"]
kubeconfig = os.path.join(volume_root, '.kube/config')

while True:
    # Fetch list of resources (for my cluster) from Studio
    resources = []
    try:
        # resources_url = resources_url.strip('/')
        print(resources_url)
        print(cluster)
        resources = requests.get(resources_url, params={"cluster": cluster}).json()
        print(resources)
    except:
        print('Failed to fetch resources from Studio.')


    # For each resource, check status
    res = dict()
    for resource in resources:
        # try:
        # if resource['chart'] == 'lab':
        print("_______________{} RESOURCE______________".format(resource['chart']))
        print(resource['name'])
        print("Getting helm values")
        helm_exists = False
        labStatus = True
        try:
            helm_vals = subprocess.run(["helm", "--kubeconfig", kubeconfig, "status", resource['name'], "-o", "json"], capture_output=True)
            helm_vals = json.loads(helm_vals.stdout)
            helm_exists = True
        except Exception as e:
            labStatus = False
            print("Did not find helm release.")
            print(e)
        

        if helm_exists:
            
            msg = dict()
            appname = 'asdfk3978sdfk348'
            try:
                helm_conf = helm_vals['config']
                appname = helm_vals['config']['appname']
                print("appname: "+appname) 
                # print("Getting pod info")
            except Exception as e:
                labStatus = False
                print("No appname in config.")
                print(e)

            po_info = dict()
            po_info['items'] = []
            try:
                po_info = subprocess.run(["kubectl", "--kubeconfig", kubeconfig, "get", "po", "-l", "app={}".format(appname), "-o", "json"], capture_output=True)
                po_info = json.loads(po_info.stdout)
            except Exception as e:
                print(e)
            print("Number of pods: "+str(len(po_info['items'])))
            for item in po_info['items']:
                pod_name = item['metadata']['name']
                msg[pod_name] = dict()
                try:
                    for cstatus in item['status']['containerStatuses']:
                        # print(cstatus.keys())
                        container_name = cstatus['name']
                        msg[pod_name][container_name] = dict()
                        msg[pod_name][container_name]['ready'] = cstatus['ready']
                        msg[pod_name][container_name]['restartCount'] = cstatus['restartCount']
                        msg[pod_name][container_name]['state'] = cstatus['state']
                        if 'waiting' in cstatus['state']:
                            print('Container waiting to start')
                            print('Reason: {}'.format(cstatus['state']['waiting']['reason']))

                        if cstatus['ready'] == False:
                            labStatus = False
                except:
                    labStatus = False
                    container_name = uuid.uuid4().hex[0:6]
                    msg[pod_name][container_name] = dict()
                    cond = item['status']['conditions'][0]

                    msg[pod_name][container_name]['ready'] = False
                    msg[pod_name][container_name]['state'] = {"waiting": {"reason": cond["reason"], "message": cond['message']}}
            print(json.dumps(msg))
        else:
            msg = "NotExists"   
        print("_________________________________________________")
        # )
        res[str(resource['id'])] = {"ready": labStatus, "info": msg}
        # except:
        #     print("Failed checking resource...")

    # Report status back to Studio
    print("REPORTING STATUS...")
    requests.post(resources_url, json=res)
    print(json.dumps(res))
    time.sleep(poll_pause)


import subprocess
import json
import yaml
import tarfile
import os
import uuid
import yaml
from django.conf import settings
from apps.models import Apps

KUBEPATH='/root/.kube/config'

def deploy(options):
    volume_root = "/"
    if "TELEPRESENCE_ROOT" in os.environ:
        volume_root = os.environ["TELEPRESENCE_ROOT"]
    kubeconfig = os.path.join(volume_root, KUBEPATH)
    
    print("JOB DEPLOY")
    app = Apps.objects.get(slug=options['app_slug'], revision=options['app_revision'])
    if app.chart_archive and app.chart_archive != '':
        try:
            chart_file = volume_root+settings.MEDIA_ROOT+app.chart_archive.name
            print("CHART_FILE")
            print(chart_file)
            tar = tarfile.open(chart_file, "r:gz")
            extract_path = '/app/extracted_charts/'+app.slug+'/'+str(app.revision)
            tar.extractall(extract_path)
            # dirfiles = os.listdir(extract_path)
            # print(dirfiles)
            tar.close()
            chart = extract_path
        except Exception as err:
            print(err)
            chart = 'charts/'+options['chart']
    else:
        chart = 'charts/'+options['chart']

    if not 'release' in options:
        print('Release option not specified.')
        return json.dumps({'status':'failed', 'reason':'Option release not set.'})


    unique_filename = 'chartcontroller/values/{}.yaml'.format(str(uuid.uuid4()))
    f = open(unique_filename,'w')
    f.write(yaml.dump(options))
    f.close()
    # print(yaml.dump(options))

    args = ['helm', 'upgrade', '--install', '--kubeconfig', kubeconfig, '-n', options['namespace'], options['release'], chart, '-f', unique_filename]
    print("PROCESSING INPUT TO CONTROLLER")

    result = subprocess.run(args, capture_output=True)
    print(result, flush=True)
    print('JOB DEPLOY DONE')
    return result

def delete(options):
    volume_root = "/"
    if "TELEPRESENCE_ROOT" in os.environ:
        volume_root = os.environ["TELEPRESENCE_ROOT"]
    kubeconfig = os.path.join(volume_root, KUBEPATH)
    args = ['helm', '--kubeconfig', str(kubeconfig), '-n', options['namespace'], 'delete', options['release']]
    result = subprocess.run(args, capture_output=True)
    print("DELETE STATUS FROM CONTROLLER")
    print(result, flush=True)
    return result
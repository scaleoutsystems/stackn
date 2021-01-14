import subprocess
import json
import yaml
import shlex

import os
import uuid

def refresh_charts(branch='master'):

    cwd = os.getcwd()
    try:
        charts_url = os.environ['CHARTS_URL']
    except Exception:
        charts_url = 'https://github.com/scaleoutsystems/charts/archive/{}.zip'.format(branch)

    status = subprocess.run('rm -rf charts-{}'.format(branch).split(' '), cwd=cwd)
    status = subprocess.run('wget -O {}.zip {}'.format(branch.replace('/', '-'), charts_url).split(' '), cwd=cwd)
    status = subprocess.run('unzip {}.zip'.format(branch.replace('/', '-')).split(' '),cwd=cwd)


class Controller:

    def __init__(self, cwd):
        self.cwd = cwd
        self.branch = os.environ['BRANCH']
        self.default_args = ['helm']
        pass

    def deploy(self, options, action='install'):
        volume_root = "/"
        if "TELEPRESENCE_ROOT" in os.environ:
            volume_root = os.environ["TELEPRESENCE_ROOT"]
        kubeconfig = os.path.join(volume_root, 'root/.kube/config')
        if 'DEBUG' in os.environ and os.environ['DEBUG'] == 'true':
            if not 'chart' in options:
                print('Chart option not specified.')
                return json.dumps({'status':'failed', 'reason':'Option chart not set.'})
            chart = 'charts/scaleout/'+options['chart']
        else:
            refresh_charts(self.branch)
            fname = self.branch.replace('/', '-')
            chart = 'charts-{}/scaleout/{}'.format(fname, options['chart'])

        if not 'release' in options:
            print('Release option not specified.')
            return json.dumps({'status':'failed', 'reason':'Option release not set.'})

        args = ['helm', action, '--kubeconfig', kubeconfig, options['release'], chart]
 
        for key in options:
            try:
                args.append('--set')
                # If list, don't escape ,
                if len(options[key]) > 0 and options[key][0] == '{' and options[key][-1] == '}':
                    args.append(key+"="+options[key])
                # And if not list, we should escape ,
                else:
                    args.append(key+"="+options[key].replace(',', '\,'))
            except:
                print('Failed to process input arguments.')
                return json.dumps({"status": "failed", 'reason':'Failed to process input arguments.'})

        print(args)
        status = subprocess.run(args, cwd=self.cwd)
        print(status)
        return json.dumps({'helm': {'command': args, 'cwd': str(self.cwd), 'status': str(status)}})

    def delete(self, options):
        volume_root = "/"
        if "TELEPRESENCE_ROOT" in os.environ:
            volume_root = os.environ["TELEPRESENCE_ROOT"]
        kubeconfig = os.path.join(volume_root, 'root/.kube/config')
        print(type(options))
        print(options)
        # args = 'helm --kubeconfig '+str(kubeconfig)+' delete {release}'.format(release=options['release']) #.split(' ')
        args = ['helm', '--kubeconfig', str(kubeconfig), 'delete', options['release']]
        status = subprocess.run(args, cwd=self.cwd)

        return json.dumps({'helm': {'command': args, 'cwd': str(self.cwd), 'status': str(status)}})

    def update(self, options, chart):
        pass

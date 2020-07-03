from github import Github
import pygit2
import os
from flask import Flask
from flask import request
import json
from subprocess import run
import datetime
from pathlib import Path
import base64
app = Flask(__name__)


@app.route('/')
def index():
    cwd = os.getcwd()
    try:
        cwd = os.environ['PROJECT_DIR']
        print('got new cwd {}.'.format(cwd))
    except Exception as e:
        pass

    from os import walk

    f = []
    d = []
    for (dirpath, dirnames, filenames) in walk(cwd):
        for name in filenames:
            fobj = Path(os.path.join(dirpath,name)).stat()
            size = fobj.st_size/1024*1024
            created = str(datetime.datetime.fromtimestamp(fobj.st_ctime))
            modified = str(datetime.datetime.fromtimestamp(fobj.st_mtime))
            f.append({'name':name,'path':os.path.join(dirpath,name),'created':created,'modified':modified})
        for name in dirnames:
            d.append({'name':name,'path':os.path.join(dirpath,name)})

    return json.dumps({'status': 'OK', 'files': f, 'dirs': d})


@app.route('/readme')
def readme():
    cwd = "/app/work"

    filename = None
    readme = None
    try:
        if os.path.isfile(os.path.join(cwd, 'README.md')):
            filename = 'README.md'
            with open(os.path.join(cwd, 'README.md')) as f:
                readme = f.read()

        elif os.path.isfile(os.path.join(cwd, 'README.rst')):
            filename = 'README.rst'
            with open(os.path.join(cwd, 'README.rst')) as f:
                readme = f.read()

        elif os.path.isfile(os.path.join(cwd, 'README')):
            filename = 'README'
            with open(os.path.join(cwd, 'README')) as f:
                readme = f.read()

    except Exception as e:
        print(e)

    return json.dumps({'status': 'OK', 'filename': filename, 'readme': readme})


@app.route('/models/<model_name>/readme')
def model_readme(model_name):
    cwd = "/app/work/models/{}".format(model_name)

    filename = None
    readme = None
    try:
        if os.path.isfile(os.path.join(cwd, 'README.md')):
            filename = 'README.md'
            with open(os.path.join(cwd, 'README.md')) as f:
                readme = f.read()

        elif os.path.isfile(os.path.join(cwd, 'README.rst')):
            filename = 'README.rst'
            with open(os.path.join(cwd, 'README.rst')) as f:
                readme = f.read()

        elif os.path.isfile(os.path.join(cwd, 'README')):
            filename = 'README'
            with open(os.path.join(cwd, 'README')) as f:
                readme = f.read()

    except Exception as e:
        print(e)

    return json.dumps({'status': 'OK', 'filename': filename, 'readme': readme})


@app.route('/reports')
def get_report_generators():
    generators = []
    for root, _, files in os.walk("/app/work/reports", topdown=False):
        for name in files:
            stats = Path(os.path.join(root, name)).stat()
            size = stats.st_size / 1024 * 1024
            created = str(datetime.datetime.fromtimestamp(stats.st_ctime))
            modified = str(datetime.datetime.fromtimestamp(stats.st_mtime))
            generators.append({
                'name': name,
                'path': os.path.join(root, name),
                'created': created,
                'modified': modified,
                'size': size
            })

    return json.dumps({'status': 'OK', 'generators': generators})


@app.route('/file/<filename>')
def get_file_content(filename):
    cwd = "/app/work/reports"

    content = None
    try:
        if os.path.isfile(os.path.join(cwd, filename)):
            with open(os.path.join(cwd, filename)) as f:
                content = f.read()
    except Exception as e:
        print(e)

    return json.dumps({'status': 'OK', 'filename': filename, 'content': content})


@app.route('project/<project_name>/push/<user_name>/<user_password>')
def push_project_to_github(project_name, user_name, user_password):
    base64_bytes = user_password.encode('ascii')
    user_password_bytes = base64.b64decode(base64_bytes)
    decoded_user_password = user_password_bytes.decode('ascii')

    g = Github(user_name, decoded_user_password)
    user = g.get_user()
    repo = user.create_repo(project_name)

    repoClone = pygit2.clone_repository(repo.git_url, '{}'.format(project_name))
    repoClone.remotes.set_url('origin', repo.clone_url)

    os.system('cp -r work/ {}/'.format(project_name))

    index = repoClone.index
    index.add_all()
    index.write()
    author = pygit2.Signature('Desislava', 'desislava@scaleoutsystems.com')
    committer = pygit2.Signature('Desislava', 'desislava@scaleoutsystems.com')
    tree = index.write_tree()

    repoClone.create_commit('HEAD', author, committer,
                            'Pushed project directory to GitHub through STACKn studio.', tree,
                            [repoClone.head.target])

    remote = repoClone.remotes['origin']
    credentials = pygit2.UserPass(user_name, decoded_user_password)
    remote.credentials = credentials

    callbacks = pygit2.RemoteCallbacks(credentials)

    remote.push(['refs/heads/master'], callbacks)

    os.system('rm -rf {}/'.format(project_name))

    return json.dumps({'status': 'OK', 'clone_url': repo.clone_url})


if __name__ == "__main__":
    import os

    app.run(debug=True, host='0.0.0.0')

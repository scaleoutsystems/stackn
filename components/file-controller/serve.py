import os
from flask import Flask
from flask import request
import json
from subprocess import run
import datetime
from pathlib import Path
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
    cwd = os.getcwd()
    try:
        cwd = os.environ['PROJECT_DIR']
    except Exception as e:
        pass

    filename = None
    readme = None
    # TODO check for flavors of README file
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


if __name__ == "__main__":
    import os

    app.run(debug=True, host='0.0.0.0')

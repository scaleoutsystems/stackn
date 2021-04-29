import click
from .main import main
import requests
import os
import tarfile

@main.command('init')

@click.pass_context
def init_cmd(ctx):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, 'default-project.tar.gz')
    import tarfile
    tf = tarfile.open(file_path)
    tf.extractall()
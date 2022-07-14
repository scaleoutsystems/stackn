import click

from .auth import stackn_login
from .main import main


@main.command('login')
@click.option('-h', '--url', required=False, default=[])
@click.option('--secure/--insecure', required=False, default=True)
@click.option('-u', '--username', required=False, default=[])
@click.option('-p', '--password', required=False, default=[])
@click.option('-c', '--client-id', required=False, default='studio-api')
def login(url, secure, username, password, client_id):
    stackn_login(studio_url=url,
                 username=username,
                 password=password,
                 client_id=client_id,
                 secure=secure)

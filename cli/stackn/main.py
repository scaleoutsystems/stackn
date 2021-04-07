import click
import logging
from .version import __version__ as version

logging.basicConfig(format='%(asctime)s [%(filename)s:%(lineno)d] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')  # , level=logging.DEBUG)

@click.version_option(
    version=version,
    prog_name='Scaleout STACKn CLI',
    message='%(prog)s, %(version)s'
)

@click.group()
def main():
    pass



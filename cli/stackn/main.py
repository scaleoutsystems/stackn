import click
import logging

import pkg_resources
version = pkg_resources.require("scaleout-cli")[0].version

logging.basicConfig(format='%(asctime)s [%(filename)s:%(lineno)d] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')  # , level=logging.DEBUG)

@click.version_option(
    version=version,
    prog_name='Scaleout STACKn CLI',
    message='%(prog)s, %(version)s'
)

@click.group()
def main():
    pass



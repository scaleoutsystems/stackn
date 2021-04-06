import click
import logging

logging.basicConfig(format='%(asctime)s [%(filename)s:%(lineno)d] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')  # , level=logging.DEBUG)

@click.group()
def main():
    pass



import click
import prettytable

from .main import main
from .stackn import set_current


class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        try:
            cmd_name = ALIASES[cmd_name].name
        except KeyError:
            pass
        return super().get_command(ctx, cmd_name)


@main.group('set', cls=AliasedGroup)
def set():
    pass


@set.command('current')
@click.option('-p', '--project', required=False, default='')
@click.option('-u', '--studio-url', required=False, default='')
@click.option('--secure/--insecure', required=False, default=True)
def setc(project, studio_url, secure):
    conf = {
        'STACKN_PROJECT': project,
        'STACKN_URL': studio_url,
        'STACKN_SECURE': secure
    }
    set_current(conf)


ALIASES = {
    "curr": setc
}

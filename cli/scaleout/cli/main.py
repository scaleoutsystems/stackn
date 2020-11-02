import click

import logging
from .. import version


logging.basicConfig(format='%(asctime)s [%(filename)s:%(lineno)d] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')  # , level=logging.DEBUG)

CONTEXT_SETTINGS = dict(
    # Support -h as a shortcut for --help
    help_option_names=['-h', '--help'],
)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    '--project',
    '-p',
    'project_dir',
    help=(
            "Supply a project directory"
    ),
    type=click.Path(exists=False, dir_okay=True),
)
@click.version_option(
    version=version.__version__,
    prog_name='Scaleout STACKn CLI',
    message='%(prog)s, %(version)s'
)

@click.pass_context
def main(ctx, project_dir):
    ctx.obj = dict()
    ctx.obj['PROJECT_DIR'] = project_dir
    if ctx.invoked_subcommand not in ('init','login','status','setup', 'set'):
        # TODO add support for cwd change, config-file specification
        from scaleout.project import Project
        from scaleout.runtime.runtime import Runtime
        from scaleout.errors import InvalidConfigurationError
        try:
            from scaleout.studioclient import StudioClient
            ctx.obj['CLIENT'] = StudioClient()
        except InvalidConfigurationError:
            pass

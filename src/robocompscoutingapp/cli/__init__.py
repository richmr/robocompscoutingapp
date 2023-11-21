# SPDX-FileCopyrightText: 2023-present Michael Rich <richmr2174@gmail.com>
#
# SPDX-License-Identifier: MIT
import click

from robocompscoutingapp.__about__ import __version__


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=True)
@click.version_option(version=__version__, prog_name="RoboCompScoutingApp")
def robocompscoutingapp():
    click.echo("Hello world!")

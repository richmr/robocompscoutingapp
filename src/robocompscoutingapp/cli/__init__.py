# SPDX-FileCopyrightText: 2023-present Michael Rich <richmr2174@gmail.com>
#
# SPDX-License-Identifier: MIT
import typer
from typing_extensions import Annotated
from pathlib import Path

from robocompscoutingapp.__about__ import __version__


cli_app = typer.Typer()

@cli_app.command()
def validate(html_file: Annotated[Path, typer.Argument(help="The finely crafted HTML file you wish to make sure is prepared to work with the RoboCompScoringApp server")],
             ):
    pass


def robocompscoutingapp():
    cli_app()

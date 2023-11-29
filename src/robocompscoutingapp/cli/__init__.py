# SPDX-FileCopyrightText: 2023-present Michael Rich <richmr2174@gmail.com>
#
# SPDX-License-Identifier: MIT
import typer
from typing_extensions import Annotated
from pathlib import Path

from robocompscoutingapp.__about__ import __version__
from robocompscoutingapp.GlobalItems import FancyText as ft
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing


cli_app = typer.Typer()

@cli_app.command()
def validate(html_file: Annotated[Path, typer.Argument(help="The finely crafted HTML file you wish to make sure is prepared to work with the RoboCompScoringApp server")],
             ):
    if html_file.exists():
        user_html_processing = UserHTMLProcessing(html_file)
        successful_validation = user_html_processing.validate()
        if not successful_validation:
            ft.error("Please fix the errors above and run validation again")
        else:
            ft.success(f"{html_file} passed validation!")
    else:
        ft.error(f"File {html_file} does not exist.")

def robocompscoutingapp():
    cli_app()

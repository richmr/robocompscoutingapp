# SPDX-FileCopyrightText: 2023-present Michael Rich <richmr2174@gmail.com>
#
# SPDX-License-Identifier: MIT
import typer
from typing_extensions import Annotated
from pathlib import Path
from rich.prompt import Confirm

from robocompscoutingapp.__about__ import __version__
from robocompscoutingapp.GlobalItems import FancyText as ft
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing
from robocompscoutingapp.Initialize import Initialize


cli_app = typer.Typer()

@cli_app.command()
def validate(html_file: Annotated[Path, typer.Argument(help="The finely crafted HTML file you wish to make sure is prepared to work with the RoboCompScoringApp server")],
             ):
    """
    Validates your scoring file has all the required hooks for the scoring mechanisms to work
    """
    if html_file.exists():
        user_html_processing = UserHTMLProcessing(html_file)
        successful_validation = user_html_processing.validate()
        if not successful_validation:
            ft.error("Please fix the errors above and run validation again")
        else:
            ft.success(f"{html_file} passed validation!")
    else:
        ft.error(f"File {html_file} does not exist.")

@cli_app.command()
def initialize(destination_path: Annotated[Path, typer.Argument(help="The destination path you want to intialize")],
               overwrite: Annotated[bool, typer.Option(help="Allow overwriting of existing files in the target directory")] = False):
    """
    Will set up a recommended file structure with a template scoring file as well as template configuration file
    """
    if destination_path.exists() and not overwrite:
        overwrite = Confirm.ask("[bold red]The target directory already exists, do you want to overwrite the files here?")
        if not overwrite:
            ft.print("No files written")
            return            

    try:
        init = Initialize(destination_path)
        init.initialize(overwrite=overwrite)
    except FileExistsError as badnews:
        if overwrite:
            # Re-raise
            raise badnews
        else:
            try_overwrite = Confirm.ask("[bold red]Do you want to overwrite the files that already exist in the destination?")
            if try_overwrite:
                initialize(destination_path=destination_path, overwrite=True)
    except Exception as badnews:
        ft.error(f"Unable to initialize the target directory because {badnews}")

    ft.success(f"File structure built at {destination_path.absolute()}.  Please see the readme.txt for more information")
    

def robocompscoutingapp():
    cli_app()

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
from robocompscoutingapp.GlobalItems import RCSA_Config


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
            # Update TOML?
            init = Initialize(html_file)
            # If user is following proscribed dir structure, the TOML should be one directory above this file
            path_to_toml = html_file.absolute().parents[1]
            if init.isTOMLInDir(tgt_dir=path_to_toml):
                ft.print("I found a rcsa_config.toml file in this directory.")
                doit = Confirm.ask(f"Would you like me to update the scoring_page setting to {html_file.name}?")
                if doit:
                    try:
                        init.updateTOML(["ServerConfig", "scoring_page"], html_file.name, tgt_dir=path_to_toml)
                    except Exception as badnews:
                        ft.error(f"Whoops.  I couldn't update because {badnews}.  You will need to do it manually")
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

from robocompscoutingapp.ScoringData import loadEventData

@cli_app.command()
def set_event():
    """
    Helps choose the event you are scoring
    """
    

@cli_app.command()
def prepare_event(
    refresh_match_data: Annotated[bool, typer.Option(help="Updates all unscored matches for the event.  Retains all scoring data")] = False,
    reset_all_data: Annotated[bool, typer.Option(help="Resets the match and team data and also deletes all existing scoring info")] = False, 
):
    """
    Loads or refreshes the match and team data for the chosen event
    """
    eventCode = RCSA_Config.getConfig().FRCEvents.first_event_id
    if eventCode == False:
        ft.error("Please specify a valid FRC Event code in the configuration file.  Use the 'set-event' command if you need guided assistance.")
        return
    
    if (refresh_match_data and reset_all_data):
        ft.error("Please choose either 'refresh-match-data' or 'reset-all-data' not both")
        return
    
    if refresh_match_data:
        ft.print("Removing all unscored matches and updating with fresh FRC Event data")
    elif reset_all_data:
        doit = Confirm.ask(f"Are you sure you want to delete all match, team, and scoring data for the {eventCode} event")
        if not doit:
            ft.warning("No changes made. If you aren't certain, backup the database just in case")
            return
        else:
            ft.print(f"Deleting all match, team, and scoring data for the {eventCode} event")
    else:
        ft.print(f"Loading matches and team data for the {eventCode} event")

    try:
        loadEventData(
            eventCode=eventCode,
            reset_all_data=reset_all_data,
            refresh_match_data=refresh_match_data
        )
        ft.success(f"{eventCode} event data loaded!")
    except ValueError:
        ft.error(f"{eventCode} is not a valid FRC event code.  Please use the set_event command if you need assistance.")
        return
    except Exception as badnews:
        ft.error(f"Unable to load event data because {badnews}")

# @cli_app.command()
# def run(
#     reset_event_data: Annotated[bool, typer.Option(help="Overwrite the existing match and team data for the selected event", default=False)],
#     erase_scoring_data: Annotated[bool, typer.Option(help="Erase all exisiting scoring data", default=False)],
#     reset_all_data: Annotated[bool, typer.Option(help="Resets the match and team data and also deletes all existing scoring info", default=False)], 
#     daemon: Annotated[bool, typer.Option(help="Run the server as a daemon.  This is generally used when an event is actually being scored.  If you don't run in daemon mode and you lose your session to the server, the app server will stop", default=False)]
# ):
#     """
#     Run the app server.
#     """
#     if reset_all_data:
#         reset_event_data = True
#         erase_scoring_data = True





def robocompscoutingapp():
    cli_app()

# SPDX-FileCopyrightText: 2023-present Michael Rich <richmr2174@gmail.com>
#
# SPDX-License-Identifier: MIT
import typer
from typer.core import TyperGroup
from click import Context

from typing_extensions import Annotated
from pathlib import Path
from rich.prompt import Confirm, Prompt
from rich.table import Table
import re


from robocompscoutingapp.FirstEventsAPI import FirstEventsAPI
from robocompscoutingapp.Integrate import Integrate
from robocompscoutingapp.RunAPIServer import RunAPIServer
from robocompscoutingapp.__about__ import __version__
from robocompscoutingapp.GlobalItems import FancyText as ft
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing
from robocompscoutingapp.Initialize import Initialize
from robocompscoutingapp.GlobalItems import RCSA_Config, GracefulInterruptHandler
from robocompscoutingapp.ScoringData import (
    getCurrentScoringPageData
)

# From: https://github.com/tiangolo/typer/issues/428
class OrderCommands(TyperGroup):
  def list_commands(self, ctx: Context):
    """Return list of commands in the order appear."""
    return list(self.commands)    # get commands using self.commands

cli_app = typer.Typer(cls=OrderCommands)

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
                        init.updateTOML(["ServerConfig", "scoring_page"], str(html_file.absolute()), tgt_dir=path_to_toml)
                    except Exception as badnews:
                        ft.error(f"Whoops.  I couldn't update because {badnews}.  You will need to do it manually")
    else:
        ft.error(f"File {html_file} does not exist.")


from robocompscoutingapp.ScoringData import loadEventData

@cli_app.command()
def set_event():
    """
    Helps choose the event you are scoring and updates your configuration file
    """
    try:
        ft.print("Collecting all FIRST Events for this season")
        fapi = FirstEventsAPI(RCSA_Config.getConfig())
        events = fapi.getEvents()
        name_filter = Prompt.ask(f"There are {len(events)} events this season.  Please enter a search term to narrow results or just hit Enter to see them all", default=None, show_default=False)
        table_title = "FIRST Events"
        if name_filter is not None:
            events = [e for e in events if bool(re.search(name_filter, e.name, re.IGNORECASE))]
            table_title = f"FIRST Events matching search term {name_filter}"
        #  Sort by earliest to latest
        events.sort(key=lambda e:e.dateStart)
        table = Table(title=table_title)
        table.add_column("Code", justify="left", style="green")
        table.add_column("Name", justify="center")
        table.add_column("Start Date", justify="center")
        for event in events:
            table.add_row(event.code, event.name, str(event.dateStart.strftime("%m-%d-%Y")))
        ft.print(table)
        choices = [e.code for e in events]
        choices.append(None)
        event_choice = Prompt.ask(
            prompt="Please enter the code (first column shown above) for the FIRST event you are scoring or just hit enter to exit",
            choices=choices,
            default=None,
            show_choices=False
        )
        if event_choice is not None:
            ft.print(f"Setting first_event_id in config file to {event_choice}")
            Initialize.updateTOML(["FRCEvents", "first_event_id"], event_choice)
            ft.success(f"first_event_id set successfully!")

        else:
            ft.print("No event choice set.  You will need to set the event code before the scoring app will work.")
        
    except Exception as badnews:
        ft.error(f"I can't set the district and event code for your event because {badnews}")

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


from robocompscoutingapp.SetupForTest import configure_for_testing

@cli_app.command()
def test(
    automate: Annotated[bool, typer.Option(help="Will automatically test your scoring page and verify the application scored correctly.")] = False,
    cleanup: Annotated[bool, typer.Option(help="Use --no-cleanup if you want to save the temporary database")] = True,
    use_config_ip: Annotated[bool, typer.Option(help="Set --use-config-ip to attach the server to the IP_Address in the TOML.  This can allow for network access.  Otherwise, the server is only attached to localhost")] = False,
    app_dev: Annotated[bool, typer.Option(help="This is for the very specific purpose of developing the sample files copied when 'initialize' is called.  You probably don't need to use this.")] = False
):
    """
    Start the application server in test mode.

    Test mode application server:\n
        - Uses a temporary database and removes it when complete (unless --no-cleanup is set)\n
        - Uses team and match data from the CALA event from the 2023 season (for consistency)\n
        - Will only attach to localhost unless --use-config-ip is set\n
    \n
    If you set --automate it will provide a link to click that will let you watch your scoring page be automatically tested.
    """
    # Set the global test flag
    RCSA_Config.getConfig().ServerConfig.test_mode = True

    if not use_config_ip:
        RCSA_Config.getConfig().ServerConfig.IP_Address = "127.0.0.1"

    if app_dev:
        RCSA_Config.getConfig().ServerConfig.user_static_folder = Path("static").absolute()
        RCSA_Config.getConfig().ServerConfig.log_filename = Path("logs/testlogs.log").absolute()
        RCSA_Config.getConfig().ServerConfig.scoring_database = Path("coretesting.db").absolute()
        user_html_processing = UserHTMLProcessing(Path("static/scoring.html"))
        successful_validation = user_html_processing.validate()

    with configure_for_testing(cleanup=cleanup):
        ft.print(f"Loading match and team data for the {RCSA_Config.getConfig().FRCEvents.first_event_id} from 2023")
        loadEventData(RCSA_Config.getConfig().FRCEvents.first_event_id, season=2023)
        ft.success("Match and team data loaded")
        spr = getCurrentScoringPageData()
        if (spr is None) or (not spr.validated):
            ft.error("Your scoring page has not been validated, please use the validate command!")
            return
        if not spr.integrated:
            ft.print("Your scoring page is not integrated into the database yet, attempting to integrate")
            try:
                integrate = Integrate()
                integrate.integrate()
                ft.success("Your scoring page was successfully integrated!")
            except Exception as badnews:
                ft.error("Unable to integrate your scoring page for the following reason")
                ft.error(str(badnews))
                return

        server = RunAPIServer()
        with GracefulInterruptHandler() as pause:
            server.run()
            pause.wait()
        server.stop()
    

@cli_app.command()
def run(
    daemon: Annotated[bool, typer.Option(help="Run the server as a daemon.  This is generally used when an event is actually being scored.  If you don't run in daemon mode and you lose your session to the server, the app server will stop")] = False,
):
    """
    Run the app server.
    """
    try:
        # Are conditions set
        eventCode = RCSA_Config.getConfig().FRCEvents.first_event_id
        if eventCode == False:
            ft.error("Please specify a valid FRC Event code in the configuration file.  Use the 'set-event' command if you need guided assistance.")
            return
        else:
            prepare_event()
        
        spr = getCurrentScoringPageData()
        if (spr is None) or (not spr.validated):
            ft.error("Your scoring page has not been validated, please use the validate command!")
            return
        if not spr.integrated:
            ft.print("Your scoring page is not integrated into the database yet, attempting to integrate")
            try:
                integrate = Integrate()
                integrate.integrate()
                ft.success("Your scoring page was successfully integrated!")
            except Exception as badnews:
                ft.error("Unable to integrate your scoring page for the following reason")
                ft.error(str(badnews))
                return
        if not spr.tested:
            ft.warning("You have not tested the chosen scoring page.  This may have unexpected results")
            ft.warning("I HIGHLY recommend running the 'test --automate' command before using this page to score your event")

        if RCSA_Config.getConfig().ServerConfig.IP_Address == "127.0.0.1":
            ft.warning("Your configuration file is set to host the app server on the localhost interface.  This will prevent anyone from connecting to the server.")
            ft.warning("I am setting it to 0.0.0.0 so that the app will be accessible on the network")
            ft.warning("Use the 'test' command to keep running on the localhost interface only")
            RCSA_Config.getConfig().ServerConfig.IP_Address = "0.0.0.0"
        
        # We make it here, time to run the app
        server = RunAPIServer(daemon=daemon)
        if not daemon:
            with GracefulInterruptHandler() as pause:
                server.run()
                pause.wait()
            server.stop()
            ft.print("Server stopped")
        else:
            ft.error("--daemon not implemented yet")
            ft.error("Please use 'nohup robocompscoutingapp run' for now (on linux)")            
        
    except Exception as badnews:
        ft.error("The server has failed because of the following reason")
        ft.error(f"{badnews}")






def robocompscoutingapp():
    cli_app()

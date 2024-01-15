from pathlib import Path
from contextlib import contextmanager
import os
import pytest

from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing
from robocompscoutingapp.Initialize import Initialize
from robocompscoutingapp.Integrate import Integrate
from robocompscoutingapp.FirstEventsAPI import FirstEventsAPI
from robocompscoutingapp.ScoringData import (
    getGameModeAndScoringElements,
    storeTeams,
    storeMatches,
    getMatchesAndTeams
)

@contextmanager
def gen_test_env_and_enter(temp_dir_path:Path):
    init = Initialize(temp_dir_path)
    init.initialize(overwrite=True)
    # Update the location of the scoring page
    init.updateTOML(["ServerConfig", "scoring_page"], f"{temp_dir_path}/static/scoring_sample.html", tgt_dir = temp_dir_path)
    # Now enter the directory
    cwd = os.getcwd() 
    # Validate the page
    try:
        os.chdir(temp_dir_path)
        uhp = UserHTMLProcessing(f"{temp_dir_path}/static/scoring_sample.html")
        uhp.validate()
        # Integrate it to set the data
        int = Integrate()
        int.integrate()

        config = RCSA_Config.getConfig()
        config.FRCEvents.first_event_id = "CALA"
        fapi = FirstEventsAPI(config=config, season=2023)

        # Go do what the test needs
        yield fapi
    except Exception as badnews:
        print("Failed test detected")
        print(f"Temp dir: {temp_dir_path}")
        print("API Config", RCSA_Config.getConfig())
        os.chdir(cwd)
        raise(badnews)
    finally:
        os.chdir(cwd)
        # API rate?
        # sleep(1.0)

def test_CALAFullLoad(tmpdir):
    with gen_test_env_and_enter(tmpdir) as fapi:
        # get all the teams
        allTeams = fapi.getTeamsAtEvent("CALA")
        # storethem
        storeTeams(allTeams)

        # get all the matches
        allMatches = fapi.getMatchesAtEvent("CALA")
        storeMatches(allMatches)

        # Retrieve and verify select
        matches_and_teams = getMatchesAndTeams("CALA")
        assert matches_and_teams.teams[2584].nameShort == "Flame of The West"
        assert matches_and_teams.matches[5].Blue3 == 2584

@pytest.mark.skip("This stress test takes a long time to run, only run to discover data issues")
def test_FRCStressTest(tmpdir):
    # This test loads all events and all matches from 2023
    # This is intended as a stress test to discover data issues across the FRC API
    with gen_test_env_and_enter(tmpdir) as fapi:
        # Get all the events for 2023
        allEvents = fapi.getEvents()
        for event in allEvents:
            storeTeams(fapi.getTeamsAtEvent(event.code))
            storeMatches(fapi.getMatchesAtEvent(event.code))
        # If we make it through all this, I suppose we are good.

import tempfile
import pytest
from pathlib import Path
# from tomlkit import TOMLDocument, table
from contextlib import contextmanager
import os
import yaml
import requests
import datetime
from time import sleep

from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.Initialize import Initialize
from robocompscoutingapp.Integrate import Integrate
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing
from robocompscoutingapp.FirstEventsAPI import (
    FirstEventsAPI, 
    FirstTeam
)

@contextmanager
def gen_test_env_and_enter(temp_dir_path:Path):
    init = Initialize(temp_dir_path)
    init.initialize(overwrite=True)
    # Update the location of the scoring page
    init.updateTOML(["Server_Config", "scoring_page"], f"{temp_dir_path}/static/scoring.html", tgt_dir = temp_dir_path)
    # Now enter the directory
    cwd = os.getcwd() 
    # Validate the page
    try:
        os.chdir(temp_dir_path)
        uhp = UserHTMLProcessing(f"{temp_dir_path}/static/scoring.html")
        uhp.validate()
        # Integrate it to set the data
        int = Integrate()
        int.integrate()

        # Go do what the test needs
        yield
    except Exception as badnews:
        print("Failed test detected")
        print(f"Temp dir: {temp_dir_path}")
        print("API Config", RCSA_Config.getFirstConfig())
        os.chdir(cwd)
        raise(badnews)
    finally:
        os.chdir(cwd)
        # API rate?
        # sleep(1.0)

def test_getDistricts(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        config = RCSA_Config.getFirstConfig()
        fapi = FirstEventsAPI(config=config)
        districts = fapi.getDistricts()
        assert len(districts) > 0

def test_getEvents(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        config = RCSA_Config.getFirstConfig(reset=True)
        fapi = FirstEventsAPI(config=config)
        events = fapi.getEvents()
        assert len(events) > 0
        assert isinstance(events[0].dateStart, datetime.datetime)
        # Make sure we found CALA
        cala = [e for e in events if e.code == "CALA"]
        assert len(cala) == 1

def test_getTeams(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        config = RCSA_Config.getFirstConfig(reset=True)
        fapi = FirstEventsAPI(config=config)
        # CALA is the Los Angeles Regional
        teams = fapi.getTeamsAtEvent(eventCode="CALA")
        assert len(teams) > 0
        # Make sure expected team is in list
        tofind = FirstTeam(nameShort="Flame of The West", teamNumber=2584, eventCode="CALA")
        assert tofind in teams

def test_getMatches(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        config = RCSA_Config.getFirstConfig(reset=True)
        fapi = FirstEventsAPI(config=config, season=2023)
        # CALA is the Los Angeles Regional
        matches = fapi.getMatchesAtEvent(eventCode="CALA")
        assert len(matches) > 0
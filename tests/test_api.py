import tempfile
import pytest
from pathlib import Path
# from tomlkit import TOMLDocument, table
from contextlib import contextmanager
import os
import yaml
import requests

from uvicorn import Config
from robocompscoutingapp.FirstEventsAPI import FirstMatch, FirstTeam

from robocompscoutingapp.GlobalItems import RCSA_Config, temp_chdir
from robocompscoutingapp.ScoringData import Score, ScoredMatchForTeam, storeMatches, storeTeams
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing
from robocompscoutingapp.Initialize import Initialize
from robocompscoutingapp.Integrate import Integrate
from robocompscoutingapp.ORMDefinitionsAndDBAccess import (
    ScoringPageStatus,
    ModesForScoringPage,
    ScoringItemsForScoringPage,
    RCSA_DB
)
from robocompscoutingapp.web.ThreadedUvicorn import ThreadedUvicorn
from robocompscoutingapp.RunAPIServer import RunAPIServer

# https://stackoverflow.com/questions/49753085/python-configure-logger-with-yaml-to-open-logfile-in-write-mode
# https://docs.python.org/3/howto/logging.html#configuring-logging




"""
Expected data
sqlite> select * from ModesForScoringPage ;
mode_id     scoring_page_id  mode_name 
----------  ---------------  ----------
1           1                Auton     
2           1                Teleop    
sqlite> select * from ScoringItemsForScoringPage ;
scoring_item_id  scoring_page_id  name        type       
---------------  ---------------  ----------  -----------
1                1                cone        score_tally
2                1                cube        score_tally
3                1                Attempted   score_flag 
4                1                Succeeded   score_flag 
5                1                Auton Mobi  score_flag 
6                1                Broke       score_flag 
sqlite> 
"""

class SingletonTestEnv:

    _server = None
    _temp_dir_obj = None
    _original_wd = None
    _instance_count = 0
    _ok_to_end = False
    _shutdown_received = False
    _success = True

    @classmethod
    @contextmanager
    def activateTestEnv(cls):
        """
        Starts server and generates temporary directory on first call
        Subsequent calls get the URL for server and the tempdir in a tuple
        After last return, the server is shutdown and the system directory is returned to previous
        """
        if cls._server is None:
            cls._original_wd = os.getcwd()
            cls._temp_dir_obj = tempfile.TemporaryDirectory()
            init = Initialize(cls._temp_dir_obj.name)
            init.initialize(overwrite=True)
            # Update the location of the scoring page
            init.updateTOML(["ServerConfig", "scoring_page"], f"{cls._temp_dir_obj.name}/static/scoring.html", tgt_dir = cls._temp_dir_obj.name)
            os.chdir(cls._temp_dir_obj.name)
            uhp = UserHTMLProcessing(f"{cls._temp_dir_obj.name}/static/scoring.html")
            uhp.validate()
            # Integrate it to set the data
            int = Integrate()
            int.integrate()
            # set the event code
            RCSA_Config.getConfig().FRCEvents.first_event_id="CALA"
            cls._server = RunAPIServer()
            cls._server.run()
        try:
            cls._instance_count += 1
            yield (serverBaseURL(), cls._temp_dir_obj.name)
        except Exception as badnews:
            print("Failed test detected")
            print(f"Temp dir: {cls._temp_dir_obj.name}")
            cls._success = False
            os.chdir(cls._original_wd)
            raise(badnews)
        finally:
            cls._instance_count -= 1
            if cls._instance_count == 0:
                if cls._shutdown_received:
                    cls._server.stop()
                    if cls._success:
                        cls._temp_dir_obj.cleanup()
                    os.chdir(cls._original_wd)

    @classmethod
    def shutdown(cls):
        cls._shutdown_received = True

   

@contextmanager
def gen_test_env_and_enter(temp_dir_path:Path):
    init = Initialize(temp_dir_path)
    init.initialize(overwrite=True)
    # Update the location of the scoring page
    init.updateTOML(["ServerConfig", "scoring_page"], f"{temp_dir_path}/static/scoring.html", tgt_dir = temp_dir_path)
    # Now enter the directory
    cwd = os.getcwd() 
    # Validate the page
    try:
        os.chdir(temp_dir_path)
        RCSA_Config.getConfig(reset=True)
        uhp = UserHTMLProcessing(f"{temp_dir_path}/static/scoring.html")
        uhp.validate()
        # Integrate it to set the data
        int = Integrate()
        int.integrate()

        # Go do what the test needs
        yield
    except Exception as badnews:
        print("Failed test detected")
        raise(badnews)
    finally:
        os.chdir(cwd)

def serverBaseURL():
    host = RCSA_Config.getConfig().ServerConfig.IP_Address
    port = RCSA_Config.getConfig().ServerConfig.port
    baseurl = f"http://{host}:{port}"
    return baseurl


def test_yaml_overwrite(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        RunAPIServer().setupLoggingYAML()
        with open("logs/rcsa_log_config.yaml") as f:
            y = yaml.safe_load(f)
            assert y["handlers"]["default"]["filename"] == f"{tmpdir}/logs/rcsa_logs.log"
            assert y["handlers"]["file"]["filename"] == f"{tmpdir}/logs/rcsa_logs.log"
            assert y["loggers"]["uvicorn.error"]["level"] == f"INFO"
            assert y["loggers"]["uvicorn.access"]["level"] == f"INFO"

def test_server_alive():
    with SingletonTestEnv.activateTestEnv() as (baseurl, temp_dir):
        url = baseurl+"/lifecheck"
        life = requests.get(url) # , auth=("no","no"))
        print(life.text)
        life = life.json()
        assert life["alive"] == True

def test_scoring_page():
    with SingletonTestEnv.activateTestEnv() as (baseurl, temp_dir):
        r = requests.get(f"{baseurl}/scoring/scoring.html")
        assert "<!-- EXISTS -->" in r.text

def test_analysis_page():
    with SingletonTestEnv.activateTestEnv() as (baseurl, temp_dir):
        r = requests.get(f"{baseurl}/analysis/foldercheck.html")
        assert "exists" in r.text

def test_gameModeandScoringElements():
    with SingletonTestEnv.activateTestEnv() as (baseurl, temp_dir):
        r = requests.get(f"{baseurl}/api/gameModesAndScoringElements")
        result = r.json()
        assert len(result["modes"]) == 2
        assert len(result["scoring_items"]) == 6

def fake_game_data():
    # Assumes already in a proper test environ
    # Teams
    team_list = [
        FirstTeam(eventCode="CALA", nameShort="Team 1", teamNumber=1),
        FirstTeam(eventCode="CALA", nameShort="Team 2", teamNumber=2),
        FirstTeam(eventCode="CALA", nameShort="Team 3", teamNumber=3),
    ]
    storeTeams(team_list)
    # Real matches don't have teams competing against themselves, but not relevant for testing purposes
    match_list = [
        FirstMatch(
            eventCode = "CALA",
            description = "Match 1",
            matchNumber = 1,
            Red1 = 1,
            Red2 = 2,
            Red3 = 3,
            Blue1 = 1,
            Blue2 = 2,
            Blue3 = 3
        ),
        FirstMatch(
            eventCode = "CALA",
            description = "Match 2",
            matchNumber = 2,
            Red1 = 1,
            Red2 = 2,
            Red3 = 3,
            Blue1 = 1,
            Blue2 = 2,
            Blue3 = 3
        )
    ]
    storeMatches(match_list=match_list)
    

def test_scoring_and_retrieval():
    with SingletonTestEnv.activateTestEnv() as (baseurl, temp_dir):
        fake_game_data()
        # Test matches and teams
        mat = requests.get(baseurl+"/api/getMatchesAndTeams").json()
        # Converting to json is making int dictionary keys into strings
        assert mat["matches"]['1']["description"] == "Match 1"
        assert mat["teams"]["3"]["nameShort"] == "Team 3"

        # Test matches
        omatch = requests.get(baseurl+"/api/getMatches").json()
        assert omatch["matches"]['1']["description"] == "Match 1"
        assert omatch["teams"] == {}

        # Add scores
        scores = [
            Score(scoring_item_id=1, mode_id=1, value=1),
            Score(scoring_item_id=1, mode_id=2, value=2),
            # Setting this to True did work, but please see notes in ScoringData.py:353
            Score(scoring_item_id=5, mode_id=1, value=True)
        ]
        score_obj = ScoredMatchForTeam(
            matchNumber=1,
            teamNumber=1,
            scores=scores
        )
        r = requests.post(baseurl+"/api/addScores", json=score_obj.model_dump())
        assert r.status_code == 200

        # Add another score
        scores = [
            Score(scoring_item_id=1, mode_id=1, value=1),
            Score(scoring_item_id=5, mode_id=1, value=0)
        ]
        score_obj = ScoredMatchForTeam(
            matchNumber=2,
            teamNumber=1,
            scores=scores
        )
        r = requests.post(baseurl+"/api/addScores", json=score_obj.model_dump())
        assert r.status_code == 200

        scores = [
            Score(scoring_item_id=1, mode_id=1, value=1),
            Score(scoring_item_id=5, mode_id=1, value=1)
        ]
        score_obj = ScoredMatchForTeam(
            matchNumber=2,
            teamNumber=3,
            scores=scores
        )
        r = requests.post(baseurl+"/api/addScores", json=score_obj.model_dump())
        # Retrieve scores
        sc = requests.get(baseurl+"/api/getAllScores").json()
        print(sc)
        assert sc["data"]["1"]["by_mode_results"]["Auton"]["scores"]["cone"]["count_of_scored_events"] == 2
        assert sc["data"]["2"]["totals"]["cone"]["count_of_scored_events"] == 0
        assert sc["data"]["3"]["totals"]["cone"]["total"] == 1


        pass


#### Keep this test last!

def test_shutdown():
    # Not really a test
    with SingletonTestEnv.activateTestEnv():
        SingletonTestEnv.shutdown()





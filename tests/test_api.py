import tempfile
import pytest
from pathlib import Path
# from tomlkit import TOMLDocument, table
from contextlib import contextmanager
import os
import yaml
import requests

from uvicorn import Config

from robocompscoutingapp.GlobalItems import RCSA_Config, temp_chdir
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
            init.updateTOML(["Server_Config", "scoring_page"], f"{cls._temp_dir_obj.name}/static/scoring.html", tgt_dir = cls._temp_dir_obj.name)
            os.chdir(cls._temp_dir_obj.name)
            uhp = UserHTMLProcessing(f"{cls._temp_dir_obj.name}/static/scoring.html")
            uhp.validate()
            # Integrate it to set the data
            int = Integrate()
            int.integrate()
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
    finally:
        os.chdir(cwd)

def serverBaseURL():
    host = RCSA_Config.getConfig().ServerConfig.IP_Address
    port = RCSA_Config.getConfig().ServerConfig.port
    baseurl = f"http://{host}:{port}"
    return baseurl

def gen_test_environment(temp_dir_path:Path):
    init = Initialize(temp_dir_path)
    init.initialize(overwrite=True)
    # Update the location of the scoring page
    init.updateTOML(["Server_Config", "scoring_page"], f"{temp_dir_path}/static/scoring.html", tgt_dir = temp_dir_path)
    # Validate the page
    with temp_chdir(temp_dir_path):
        uhp = UserHTMLProcessing(f"{temp_dir_path}/static/scoring.html")
        uhp.validate()
        # Integrate it to set the data
        int = Integrate()
        int.integrate()


def test_yaml_overwrite():
    with SingletonTestEnv.activateTestEnv() as (baseurl, temp_dir):
        with open("logs/rcsa_log_config.yaml") as f:
            y = yaml.safe_load(f)
            assert y["handlers"]["default"]["filename"] == f"{temp_dir}/logs/rcsa_logs.log"
            assert y["handlers"]["file"]["filename"] == f"{temp_dir}/logs/rcsa_logs.log"
            assert y["loggers"]["uvicorn.error"]["level"] == f"INFO"
            assert y["loggers"]["uvicorn.access"]["level"] == f"INFO"

def test_server_alive():
    with SingletonTestEnv.activateTestEnv() as (baseurl, temp_dir):
        url = serverBaseURL()+"/lifecheck"
        life = requests.get(url).json()
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

#### Keep this test last!

def test_shutdown():
    # Not really a test
    with SingletonTestEnv.activateTestEnv():
        SingletonTestEnv.shutdown()

# def test_modes_and_scoring_items_api(tmpdir):
#     gen_test_environment(tmpdir)
#     start_uvicorn_server




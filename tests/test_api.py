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

# class RCSAUvicornServer:

#     _server_instance = None
#     _checkouts = 0

#     @classmethod
#     def start(cls):
#         if cls._server_instance is None:
#             app_config = RCSA_Config.getConfig()
#             uv_config = Config("robocompscoutingapp.web:rcsa_api_app", 
#                                host=app_config["Server_Config"]["IP_Address"], 
#                                port=app_config["Server_Config"]["port"], 
#                                reload=False,
#                                log_config= 
#                                log_level=logging_level.value)
#     server = ThreadedUvicorn(config)
#     server.start()


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

@contextmanager
def gen_test_end_and_enter(temp_dir_path:Path):
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
    host = RCSA_Config.getConfig()["Server_Config"]["IP_Address"]
    port = RCSA_Config.getConfig()["Server_Config"]["port"]
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

def start_uvicorn_server():
    # return uvicorn server instance to allow clean stop
    pass



# def test_fake(tmpdir):
#     gen_test_environment(tmpdir)
#     assert False



def test_yaml_overwrite(tmpdir):
    with gen_test_end_and_enter(tmpdir):
        server = RunAPIServer()
        server.setupLoggingYAML()
        # Verify 
        with open("logs/rcsa_log_config.yaml") as f:
            y = yaml.safe_load(f)
            assert y["handlers"]["default"]["filename"] == f"{tmpdir}/logs/rcsa_logs.log"
            assert y["handlers"]["access"]["filename"] == f"{tmpdir}/logs/rcsa_logs.log"
            assert y["loggers"]["uvicorn.error"]["level"] == f"INFO"
            assert y["loggers"]["uvicorn.access"]["level"] == f"INFO"
            
def test_server_alive(tmpdir):
    with gen_test_end_and_enter(tmpdir):
        server = RunAPIServer()
        server.run()
        url = serverBaseURL()+"/lifecheck"
        life = requests.get(url).json()
        assert life["alive"] == True
        server.stop()

def test_modes_and_scoring_items_api(tmpdir):
    gen_test_environment(tmpdir)
    start_uvicorn_server


def setupTempDB(temp_path):
    # Ensures the target page is entered into the DB
    RCSA_Config.getConfig(test_TOML=gen_test_config(temp_path))
    RCSA_DB.getSQLSession(reset=True)
    # Process working file
    file = RCSA_Config.getConfig()["Server_Config"]["scoring_page"]
    uhp = UserHTMLProcessing(file)
    validated = uhp.validate()
    assert validated == True

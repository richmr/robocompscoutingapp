import pytest
from pathlib import Path
from tomlkit import TOMLDocument, table
from contextlib import contextmanager

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

# https://stackoverflow.com/questions/49753085/python-configure-logger-with-yaml-to-open-logfile-in-write-mode
# https://docs.python.org/3/howto/logging.html#configuring-logging

class RCSAUvicornServer:

    _server_instance = None
    _checkouts = 0

    @classmethod
    def start(cls):
        if cls._server_instance is None:
            app_config = RCSA_Config.getConfig()
            uv_config = Config("robocompscoutingapp.web:rcsa_api_app", 
                               host=app_config["Server_Config"]["IP_Address"], 
                               port=app_config["Server_Config"]["port"], 
                               reload=False,
                               log_config= 
                               log_level=logging_level.value)
    server = ThreadedUvicorn(config)
    server.start()

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

def test_modes_and_scoring_items_api(tmpdir):
    gen_test_environment(tmpdir)
    start_uvicorn_server



    # new_doc = TOMLDocument()
    # server_config = table()
    # server_config.add("IP_address", "127.0.0.1")
    # server_config.add("port", 8080)
    # server_config.add("user_static_folder", f"{temp_dir_path}/static")
    # server_config.add("log_folder", f"{temp_dir_path}/logs")
    # server_config.add("FQDN", "localhost")
    # server_config.add("scoring_database", f"{temp_dir_path}/rcsa_scoring.db")
    # server_config.add("scoring_page", "tests/data/scoring_sample.html")
    # new_doc["Server_Config"] = server_config

    # # ensure 
    # return new_doc

def setupTempDB(temp_path):
    # Ensures the target page is entered into the DB
    RCSA_Config.getConfig(test_TOML=gen_test_config(temp_path))
    RCSA_DB.getSQLSession(reset=True)
    # Process working file
    file = RCSA_Config.getConfig()["Server_Config"]["scoring_page"]
    uhp = UserHTMLProcessing(file)
    validated = uhp.validate()
    assert validated == True

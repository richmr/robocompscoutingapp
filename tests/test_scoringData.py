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
from robocompscoutingapp.ScoringData import (
    getGameModeAndScoringElements,
    getCurrentScoringPageID
)
from robocompscoutingapp.ORMDefinitionsAndDBAccess import (
    ScoringPageStatus,
    ModesForScoringPage,
    ScoringItemsForScoringPage,
    RCSA_DB
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
    finally:
        os.chdir(cwd)

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

def test_getGameModeAndScoringElements(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        # only one page is loaded in temporary db, it should be ID 1
        mai = getGameModeAndScoringElements(1)
        assert len(mai.modes) == 2
        assert len(mai.scoring_items) == 6

def test_scoring_page_id(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        assert getCurrentScoringPageID() == 1
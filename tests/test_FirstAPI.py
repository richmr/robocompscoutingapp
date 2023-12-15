import tempfile
import pytest
from pathlib import Path
# from tomlkit import TOMLDocument, table
from contextlib import contextmanager
import os
import yaml
import requests

from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.Initialize import Initialize
from robocompscoutingapp.Integrate import Integrate
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing
from robocompscoutingapp.FirstEventsAPI import FirstEventsAPI

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
        os.chdir(cwd)
        raise(badnews)
    finally:
        os.chdir(cwd)

def test_getDistricts(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        config = RCSA_Config.getFirstConfig()
        fapi = FirstEventsAPI(config=config)
        districts = fapi.getDistricts()
        print(districts)
        assert len(districts) > 0

import os
import tempfile
import pytest
from tomlkit import TOMLDocument
from pathlib import Path
import contextlib

from robocompscoutingapp.GlobalItems import RCSA_Config

# @pytest.fixture
def getTestConfig() -> TOMLDocument:
    # Tests normally run from repository root dir, need to change to "tests"
    # Where are we?
    # cwd = Path(os.getcwd())
    # if cwd.name == "tests":
    #     #  We are in the right place, go
    #     pass
    # elif cwd.name == "robocompscoutingapp":
    #     os.chdir("tests")
    # else:
    #     # Could be any number of places, try the chdir to throw error
    #     print(cwd)
    #     os.chdir("tests")
    with contextlib.chdir("tests"):
        return RCSA_Config.getConfig(reset=True)

def test_missing_config():
    with pytest.raises(FileNotFoundError):
        with tempfile.TemporaryDirectory() as tmpdir:
            with contextlib.chdir(tmpdir):
                config = RCSA_Config.getConfig(reset=True)

def test_found_config():
    config = getTestConfig()

def test_singleton_config():
    # First load it once
    config = getTestConfig()
    # Now change dir and try again
    with contextlib.chdir(tempfile.gettempdir()):
        config = RCSA_Config.getConfig()
      

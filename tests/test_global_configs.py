import os
import tempfile
import pytest
from tomlkit import TOMLDocument
from pathlib import Path

from robocompscoutingapp.GlobalItems import RCSA_Config

@pytest.fixture
def getTestConfig() -> TOMLDocument:
    # Tests normally run from repository root dir, need to change to "tests"
    # Where are we?
    cwd = Path(os.getcwd())
    if cwd.name == "tests":
        #  We are in the right place, go
        pass
    elif cwd.name == "robocompscoutingapp":
        os.chdir("tests")
    else:
        # Could be any number of places, try the chdir to throw error
        print(cwd)
        os.chdir("tests")
    return RCSA_Config().getConfig()

def test_missing_config():
    with pytest.raises(FileNotFoundError):
        os.chdir(tempfile.gettempdir())
        config = RCSA_Config().getConfig()

def test_found_config(getTestConfig):
    config = getTestConfig

def test_singleton_config(getTestConfig):
    # First load it once
    config = getTestConfig
    # Now change dir and try again
    os.chdir(tempfile.gettempdir())
    config = RCSA_Config.getConfig()

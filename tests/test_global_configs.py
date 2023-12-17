import os
import tempfile
import pytest
from tomlkit import TOMLDocument
from pathlib import Path
import contextlib

from robocompscoutingapp.GlobalItems import RCSA_Config, RCSAConfig

# @pytest.fixture
def getTestConfig() -> RCSAConfig:
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
    with contextlib.chdir("src/robocompscoutingapp/initialize"):
        return RCSA_Config.getConfig(reset=True)

def test_missing_config():
    with pytest.raises(FileNotFoundError):
        with tempfile.TemporaryDirectory() as tmpdir:
            with contextlib.chdir(tmpdir):
                config = RCSA_Config.getConfig(reset=True)

def test_found_config():
    with contextlib.chdir("src/robocompscoutingapp/initialize"):
        config = RCSA_Config.getConfig()
        assert isinstance(config,RCSAConfig)


def test_singleton_config():
    # First load it once
    with contextlib.chdir("src/robocompscoutingapp/initialize"):
        config = RCSA_Config.getConfig()
    # Now change dir and try again
    with contextlib.chdir(tempfile.gettempdir()):
        config = RCSA_Config.getConfig()
      

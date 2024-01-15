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

# This is running tests as the other API endpoints, but testing with auth

fake_secrets_toml = """
[Secrets]
basic_auth_username = "test"
basic_auth_password = "test"
FRC_Events_API_Username = "sample"
FRC_Events_API_Auth_Token = "notakey"
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
            init.updateTOML(["ServerConfig", "scoring_page"], f"{cls._temp_dir_obj.name}/static/scoring_sample.html", tgt_dir = cls._temp_dir_obj.name)
            os.chdir(cls._temp_dir_obj.name)
            # Set up some fake credentials
            with open("fake_secrets.toml", "w") as f:
                f.write(fake_secrets_toml)
            init.updateTOML(["Secrets", "secrets_file"], f"{cls._temp_dir_obj.name}/fake_secrets.toml", tgt_dir = cls._temp_dir_obj.name)
            uhp = UserHTMLProcessing(f"{cls._temp_dir_obj.name}/static/scoring_sample.html")
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
    init.updateTOML(["ServerConfig", "scoring_page"], f"{temp_dir_path}/static/scoring_sample.html", tgt_dir = temp_dir_path)
    # Now enter the directory
    cwd = os.getcwd() 
    # Validate the page
    try:
        os.chdir(temp_dir_path)
        RCSA_Config.getConfig(reset=True)
        uhp = UserHTMLProcessing(f"{temp_dir_path}/static/scoring_sample.html")
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

def gen_test_environment(temp_dir_path:Path):
    init = Initialize(temp_dir_path)
    init.initialize(overwrite=True)
    # Update the location of the scoring page
    init.updateTOML(["ServerConfig", "scoring_page"], f"{temp_dir_path}/static/scoring_sample.html", tgt_dir = temp_dir_path)
    # Validate the page
    with temp_chdir(temp_dir_path):
        uhp = UserHTMLProcessing(f"{temp_dir_path}/static/scoring_sample.html")
        uhp.validate()
        # Integrate it to set the data
        int = Integrate()
        int.integrate()



def test_server_alive_unauth():
    with SingletonTestEnv.activateTestEnv() as (baseurl, temp_dir):
        url = baseurl+"/lifecheck"
        life = requests.get(url)
        assert life.status_code == 401 

def test_server_alive_wrongauth():
    with SingletonTestEnv.activateTestEnv() as (baseurl, temp_dir):
        url = baseurl+"/lifecheck"
        life = requests.get(url, auth=("wrong","wrong"))
        assert life.status_code == 401         

def test_server_alive_authed():
    with SingletonTestEnv.activateTestEnv() as (baseurl, temp_dir):
        url = baseurl+"/lifecheck"
        life = requests.get(url, auth=("test","test"))
        life = life.json()
        assert life["alive"] == True


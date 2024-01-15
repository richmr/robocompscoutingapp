from contextlib import contextmanager
import os
from pathlib import Path

from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.Initialize import Initialize
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing
from robocompscoutingapp.ORMDefinitionsAndDBAccess import RCSA_DB




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
        # Go do what the test needs
        yield
    except Exception as badnews:
        print("Failed test detected")
        print(f"Temp dir: {temp_dir_path}")
        print("API Config", RCSA_Config.getConfig())
        raise(badnews)
    finally:
        os.chdir(cwd)
        # API rate?
        # sleep(1.0)

def test_with_database(tmpdir):
    broken_file = Path("tests/data/full_template_with_errors.html").absolute()
    with gen_test_env_and_enter(tmpdir):
        # First call getTestConfig to set the global config singleton
        config = RCSA_Config.getConfig()
        
        RCSA_DB.getSQLSession(reset=True)        

        # creation and check
        uhp = UserHTMLProcessing(broken_file)
        existing = uhp.checkForValidatedPageEntry()
        # Test for proper None return
        assert existing is None
    
        # Start again with working template
        uhp = UserHTMLProcessing(config.ServerConfig.scoring_page)
        good = uhp.validate()
        assert good == True

        # Check to make sure its there
        existing = uhp.checkForValidatedPageEntry()
        assert existing is not None

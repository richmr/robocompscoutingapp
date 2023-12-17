import pytest
from pathlib import Path
import tempfile

from robocompscoutingapp.GlobalItems import getFullTemplateFile
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing
from robocompscoutingapp.ORMDefinitionsAndDBAccess import RCSA_DB

from test_global_configs import getTestConfig

@pytest.fixture
def broken_template_file() -> Path:
    current_file_path = Path(__file__)
    html_file_path = current_file_path.parent/"data/full_template_with_errors.html"
    return html_file_path

def test_full_success(getFullTemplateFile):
    # Use getTestConfig to set things up
    getTestConfig()

    uhp = UserHTMLProcessing(getFullTemplateFile)
    good = uhp.validateHTML()
    assert good == True

def test_with_errors(broken_template_file):
    # Use getTestConfig to set things up
    getTestConfig()
    uhp = UserHTMLProcessing(broken_template_file)
    good = uhp.validateHTML()
    assert good == False
    assert uhp.scoring_parse_result.hasErrors() == True
    assert uhp.match_team_element_parse_result.hasErrors() == True
    assert uhp.js_parse_result.hasErrors() == True

def test_hash(broken_template_file):
    # First call getTestConfig to set the global config singleton
    config = getTestConfig()

    # Now establish tempdir and modify the config
    with tempfile.TemporaryDirectory() as tempdir:
        print(tempdir)
        config["ServerConfig"]["user_static_folder"] = tempdir
        uhp = UserHTMLProcessing(broken_template_file)
        h = uhp.getFileHash()
        assert h == "c539b61e9838f032c89e2c22306346d35350a9e359c1be39a5560e0b660d84d4"

def test_with_database(getFullTemplateFile, broken_template_file):
    # First call getTestConfig to set the global config singleton
    config = getTestConfig()

    # Now establish tempdir and modify the config
    with tempfile.TemporaryDirectory() as tempdir:
        config["ServerConfig"]["scoring_database"] = f"{tempdir}/rcsa_scoring.db"
        assert Path(config["ServerConfig"]["scoring_database"]).exists() == False
        # Reset DB singleton
        RCSA_DB.getSQLSession(reset=True)        

        # creation and check
        uhp = UserHTMLProcessing(broken_template_file)
        existing = uhp.checkForValidatedPageEntry()
        # Test for proper None return
        assert existing is None
       
        # Start again with working template
        uhp = UserHTMLProcessing(getFullTemplateFile)
        good = uhp.validate()
        assert good == True

        # Check to make sure its there
        existing = uhp.checkForValidatedPageEntry()
        assert existing is not None

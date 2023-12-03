import pytest
from pathlib import Path
import tempfile

from robocompscoutingapp.GlobalItems import getFullTemplateFile
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing

from test_global_configs import getTestConfig

@pytest.fixture
def broken_template_file() -> Path:
    current_file_path = Path(__file__)
    html_file_path = current_file_path.parent/"data/full_template_with_errors.html"
    return html_file_path

def test_full_success(getFullTemplateFile, getTestConfig):
    # Use getTestConfig to set things up
    getTestConfig

    uhp = UserHTMLProcessing(getFullTemplateFile)
    good = uhp.validateHTML()
    assert good == True

def test_with_errors(broken_template_file, getTestConfig):
    # Use getTestConfig to set things up
    getTestConfig
    uhp = UserHTMLProcessing(broken_template_file)
    good = uhp.validateHTML()
    assert good == False
    assert uhp.scoring_parse_result.hasErrors() == True
    assert uhp.match_team_element_parse_result.hasErrors() == True
    assert uhp.js_parse_result.hasErrors() == True

def test_hash(getTestConfig, broken_template_file):
    # First call getTestConfig to set the global config singleton
    config = getTestConfig

    # Now establish tempdir and modify the config
    with tempfile.TemporaryDirectory() as tempdir:
        config["Server_Config"]["user_static_folder"] = tempdir
        uhp = UserHTMLProcessing(broken_template_file)
        h = uhp.getFileHash()
        assert h == "c539b61e9838f032c89e2c22306346d35350a9e359c1be39a5560e0b660d84d4"

def test_with_database(getTestConfig, getFullTemplateFile, broken_template_file):
    # First call getTestConfig to set the global config singleton
    config = getTestConfig

    # Now establish tempdir and modify the config
    with tempfile.TemporaryDirectory() as tempdir:
        config["Server_Config"]["user_static_folder"] = tempdir

        # Test for proper None return
        uhp = UserHTMLProcessing(broken_template_file)
        existing = uhp.checkForValidatedPageEntry()
        assert existing == None

        # creation and check
        uhp.createValidatedPageEntry()
        existing = uhp.checkForValidatedPageEntry()
        assert existing.scoring_page_hash == "c539b61e9838f032c89e2c22306346d35350a9e359c1be39a5560e0b660d84d4"

        # Start again with working template
        uhp = UserHTMLProcessing(getFullTemplateFile)
        good = uhp.validate()
        assert good == True

        # Check to make sure its there
        existing = uhp.checkForValidatedPageEntry()
        assert existing is not None

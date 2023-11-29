import pytest
from pathlib import Path

from robocompscoutingapp.GlobalItems import getFullTemplateFile
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing

@pytest.fixture
def broken_template_file() -> Path:
    current_file_path = Path(__file__)
    html_file_path = current_file_path.parent/"data/full_template_with_errors.html"
    return html_file_path

def test_full_success(getFullTemplateFile):
    with getFullTemplateFile.open() as f:
        uhp = UserHTMLProcessing(f)
        good = uhp.validate()
        assert good == True

def test_with_errors(broken_template_file):
    with broken_template_file.open() as f:
        uhp = UserHTMLProcessing(f)
        good = uhp.validate()
        assert good == False
        assert uhp.scoring_parse_result.hasErrors() == True
        assert uhp.match_team_element_parse_result.hasErrors() == True

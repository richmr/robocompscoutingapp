from pathlib import Path
import pytest
from bs4 import BeautifulSoup

@pytest.fixture
def check_data_page():
    current_file_path = Path(__file__)
    html_file_path = current_file_path.parent/"data/check_data.html"
    with html_file_path.open() as f:
        html = f.read()
        html = html.strip()
        return html

@pytest.fixture
def scoring_html_page():
    current_file_path = Path(__file__)
    html_file_path = current_file_path.parent/"data/scoring_sample.html"
    with html_file_path.open() as f:
        html = f.read()
        html = html.strip()
        return html
     
def test_data_discover(check_data_page: str):
    # Just making sure we can find our data files
    assert check_data_page == "test data is discoverable"

def test_class_match_selection(scoring_html_page: str):
    soup = BeautifulSoup(scoring_html_page, features="html.parser")
    match_selection = soup.select(".match_selection")
    assert len(match_selection) == 1
    inner = match_selection[0].text
    assert inner == "Match Selection"

def test_find_scoring_section(scoring_html_page: str):
    soup = BeautifulSoup(scoring_html_page, features="html.parser")
    match_selection = soup.select(".scoring")
    assert len(match_selection) == 1

def test_game_mode_parsing(scoring_html_page: str):
    soup = BeautifulSoup(scoring_html_page, features="html.parser")
    match_selection = soup.select(".game_mode_group")
    assert len(match_selection) == 1

    # Now make sure we see both game modes
    game_modes = soup.select(".game_mode")
    assert len(game_modes) == 2
    
    # Check first find
    assert game_modes[0]["id"] == "set-auton"
    first = game_modes[0].find_all(True)
    assert len(first) == 1
    # Can't do exact HTML comparison because bs4 can switch attributes around on parse.
    assert first[0]["id"] == "auton_icon"

    # Check second find
    assert game_modes[1]["id"] == "set-teleop"
    first = game_modes[1].find_all(True)
    assert len(first) == 1
    assert first[0]["id"] == "tele_icon"

# def test_find_tally_fields():
#     # Send HTML to the processor
#     pass
#     # Call API to get list of tally fields
#     pass
#     # Check matches intent
#     pass


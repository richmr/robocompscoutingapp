from pathlib import Path
import pytest

from robocompscoutingapp.MatchAndTeamSelectionParser import MatchAndTeamSelectionParser
from robocompscoutingapp.AppExceptions import MatchAndTeamSelectionParseError, MatchAndTeamSelectionParseWarning
from robocompscoutingapp.GlobalItems import getFullTemplateFile

def test_scoring_class_parse():
    parser = MatchAndTeamSelectionParser("<div class='match_and_team_selection'></div>")
    assert parser.matchDivPresent() == True

    with pytest.raises(MatchAndTeamSelectionParseError):
        parser = MatchAndTeamSelectionParser("<div class='not_match_and_team_selection'></div>")
        parser.matchDivPresent()

    with pytest.raises(MatchAndTeamSelectionParseError):
        parser = MatchAndTeamSelectionParser("<div class='match_and_team_selection'></div><div class='match_and_team_selection'></div>")
        parser.matchDivPresent()

def test_match_selector():
    #  Clean test
    parser = MatchAndTeamSelectionParser("<select class='match_selector'></select>")
    assert parser.matchSelectorParse() == True

    # class applied to div, not select element
    with pytest.raises(MatchAndTeamSelectionParseError):
        parser = MatchAndTeamSelectionParser("<div class='match_selector'></div>")
        assert parser.matchSelectorParse() == True

    # None found
    with pytest.raises(MatchAndTeamSelectionParseError):
        parser = MatchAndTeamSelectionParser("<select class='not_match_selector'></select>")
        assert parser.matchSelectorParse() == True

    # Too many found
    with pytest.raises(MatchAndTeamSelectionParseError):
        parser = MatchAndTeamSelectionParser("<select class='match_selector'></select><select class='match_selector'></select>")
        assert parser.matchSelectorParse() == True
   
def test_team_selector():
    #  Clean test
    parser = MatchAndTeamSelectionParser("<select class='team_selector'></select>")
    assert parser.teamSelectorParse() == True

    # class applied to div, not select element
    with pytest.raises(MatchAndTeamSelectionParseError):
        parser = MatchAndTeamSelectionParser("<div class='team_selector'></div>")
        assert parser.teamSelectorParse() == True

    # None found
    with pytest.raises(MatchAndTeamSelectionParseError):
        parser = MatchAndTeamSelectionParser("<select class='not_match_selector'></select>")
        assert parser.teamSelectorParse() == True

    # Too many found
    with pytest.raises(MatchAndTeamSelectionParseError):
        parser = MatchAndTeamSelectionParser("<select class='team_selector'></select><select class='team_selector'></select>")
        assert parser.teamSelectorParse() == True




def test_full_element_parse():
    # Full success
    test_html = """
        <div class="match_and_team_selection">
            <select class="match_selector"></select>
            <select class="team_selector"></select>
            <button class="button btn-big begin_scoring">Begin Scoring</button>
        </div>
    """
    parser = MatchAndTeamSelectionParser(test_html)
    pr = parser.parseElement()
    assert pr.hasErrors() == False
    assert pr.hasWarnings() == False
    
    # Make sure errors and warnings are collected correctly
    test_html = """
        <div class="match_and_team_selection">
            <select class="_match_selector"></select>
            <p class="team_selector"></p>
        </div>
    """
    parser = MatchAndTeamSelectionParser(test_html)
    pr = parser.parseElement()
    assert pr.hasErrors() == True
    assert len(pr.errors) == 3
    assert pr.hasWarnings() == False

def test_validation_output(capfd, getFullTemplateFile):
    with getFullTemplateFile.open() as f:
        parser = MatchAndTeamSelectionParser(f)
        result = parser.validate()
        assert result.hasErrors() == False
        assert result.hasWarnings() == False
        out, err = capfd.readouterr()
        assert out == "[+] Match selection element passed validation!\n"

    
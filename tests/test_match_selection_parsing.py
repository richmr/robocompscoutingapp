from pathlib import Path
import pytest

from robocompscoutingapp.MatchAndTeamSelectionParser import MatchAndTeamSelectionParser
from robocompscoutingapp.AppExceptions import MatchAndTeamSelectionParseError, MatchAndTeamSelectionParseWarning


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


# def test_scoring_items():
#     # with pytest.warns(ScoringPageParseWarning):
#         # Suppress the warning about game modes.  Already tested.
#         # Get dict with two items each for _tally and _flag
#         input = """
#             <div class="scoring">
#             <div class="score_tally" data-scorename="Test Tally 1"></div>
#             <div class="score_tally" data-scorename="Test Tally 2"></div>
#             <div class="score_flag" data-scorename="Test Flag 1"></div>
#             <div class="score_flag" data-scorename="Test Flag 2"></div>
#             </div>
#         """
#         parser = MatchAndTeamSelectionParser(input)
#         scoring_dict = parser.collectScoringItems()
#         assert "score_tally" in scoring_dict.keys()
#         assert ["Test Tally 1", "Test Tally 2"].sort() == scoring_dict["score_tally"].sort()
#         assert "score_flag" in scoring_dict.keys()
#         assert ["Test Flag 1", "Test Flag 2"].sort() == scoring_dict["score_flag"].sort()    

#         # Fail because no scoring items found
#         with pytest.raises(MatchAndTeamSelectionParseError):
#             input = """
#                 <div  data-scorename="Test Tally 1"></div>
#                 <div  data-scorename="Test Tally 2"></div>
#                 <div  data-scorename="Test Flag 1"></div>
#                 <div  data-scorename="Test Flag 2"></div>
#             """
#             parser = MatchAndTeamSelectionParser(input)
#             scoring_dict = parser.collectScoringItems()

#         # Fail because two scoring items with same name in same mode found
#         with pytest.raises(MatchAndTeamSelectionParseError):
#             input = """
#                 <div class="score_tally" data-scorename="Same Name"></div>
#                 <div class="score_tally" data-scorename="Same Name"></div>
#                 <div class="score_flag" data-scorename="Test Flag 1"></div>
#                 <div class="score_flag" data-scorename="Test Flag 2"></div>
#             """
#             parser = MatchAndTeamSelectionParser(input)
#             scoring_dict = parser.collectScoringItems()

#         # Fail because two scoring items with same name in different modes found
#         with pytest.raises(MatchAndTeamSelectionParseError):
#             input = """
#                 <div class="score_tally" data-scorename="Same Name"></div>
#                 <div class="score_tally" data-scorename="Test Tally 2"></div>
#                 <div class="score_flag" data-scorename="Test Flag 1"></div>
#                 <div class="score_flag" data-scorename="Same Name"></div>
#             """
#             parser = MatchAndTeamSelectionParser(input)
#             scoring_dict = parser.collectScoringItems()

#         # Fail because scoring item with onlyformode has mode that does not exist
#         with pytest.raises(MatchAndTeamSelectionParseError):
#             input = """
#                 <div class="score_tally" data-onlyformode="not exist" data-scorename="Same Name"></div>
#                 <div class="score_tally" data-scorename="Test Tally 2"></div>
#                 <div class="score_flag" data-scorename="Test Flag 1"></div>
#                 <div class="score_flag" data-scorename="Same Name"></div>
#             """
#             parser = MatchAndTeamSelectionParser(input)
#             scoring_dict = parser.collectScoringItems()

#         # Fail because no activity name defined
#         with pytest.raises(MatchAndTeamSelectionParseError):
#             input = """
#                 <div class="score_tally"></div>
#             """
#             parser = MatchAndTeamSelectionParser(input)
#             scoring_dict = parser.collectScoringItems()

# @pytest.fixture
# def get_test_data_path() -> Path:
#     current_file_path = Path(__file__)
#     data_path = current_file_path.parent/"data"
#     return data_path

def test_full_element_parse():
    # Full success
    test_html = """
        <div class="match_and_team_selection">
            <select class="match_selector"></select>
            <select class="team_selector"></select>
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
    assert len(pr.errors) == 2
    assert pr.hasWarnings() == False
    

    
import pytest

from robocompscoutingapp.ScoringPageParser import ScoringPageParser
from robocompscoutingapp.AppExceptions import ScoringPageParseError, ScoringPageParseWarning

"""
Needed tests:
- detect match_selection div (pos/neg) - Not needed..  I'm just going to add it anyway
- detect review_and_submit div (pos/neg) - Not needed..  I'm just going to add it anyway
- detect error_modal div (pos/neg) - Not needed..  I'm just going to add it anyway
- detect sending_data_modal div (pos/neg) - Not needed..  I'm just going to add it anyway

- detect game_mode_group (pos/neg)
- collect game_mode (return findings)
    - Check for duplicates, error
- collect score_tally (return findings)
- collect score_flag (return findings)
- detect click_feedback (return findings) - not sure this is needed.  Its window dressing
- collect data-modename (return findings)
    - Check for duplicates, error
- collect data-scorename (return findings)
    - Check for duplicates, error
- collect data-onlyForMode (return findings)
    - Check for modes that do not exist
"""

def test_scoring_class_parse():
    spp = ScoringPageParser("<div class='scoring'></div>")
    assert spp.scoringDivPresent() == True

    with pytest.raises(ScoringPageParseError):
        spp = ScoringPageParser("<div class='not_scoring'></div>")
        spp.scoringDivPresent()

def test_game_mode_group_class():
    spp = ScoringPageParser("<div class='game_mode_group'></div>")
    assert spp.gameModeGroupPresent() == True

    with pytest.raises(ScoringPageParseWarning):
        spp = ScoringPageParser("<div></div>")
        spp.gameModeGroupPresent()

    with pytest.raises(ScoringPageParseError):
        spp = ScoringPageParser("<div class='game_mode_group'></div><div class='game_mode_group'></div>")
        spp.gameModeGroupPresent()

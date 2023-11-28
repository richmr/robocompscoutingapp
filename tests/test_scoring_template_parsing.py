from pathlib import Path
import pytest

from robocompscoutingapp.ScoringPageParser import ScoringPageParser
from robocompscoutingapp.AppExceptions import ScoringPageParseError, ScoringPageParseWarning
from robocompscoutingapp.GlobalItems import ScoringClassTypes, getFullTemplateFile


def test_scoring_class_parse():
    spp = ScoringPageParser("<div class='scoring'></div>")
    assert spp.scoringDivPresent() == True

    with pytest.raises(ScoringPageParseError):
        spp = ScoringPageParser("<div class='not_scoring'></div>")
        spp.scoringDivPresent()

def test_game_mode_group_class():
    spp = ScoringPageParser("<div class='game_mode_group'></div>")
    assert spp.gameModeGroupPresent() == True

    with pytest.warns(ScoringPageParseWarning):
        spp = ScoringPageParser("<div></div>")
        spp.gameModeGroupPresent()

    with pytest.raises(ScoringPageParseError):
        spp = ScoringPageParser("<div class='game_mode_group'></div><div class='game_mode_group'></div>")
        spp.gameModeGroupPresent()

def test_game_mode():
    spp = ScoringPageParser("<div data-modename='mode1' class='game_mode'></div><div data-modename='mode2' class='game_mode'></div>")
    gmodes = spp.collectGameModes()
    expected_gmodes = ["mode1", "mode2"]
    assert gmodes.sort() == expected_gmodes.sort()

    with pytest.warns(ScoringPageParseWarning):
        spp = ScoringPageParser("<div ></div>")
        gmodes = spp.collectGameModes()
        assert gmodes == []

    with pytest.raises(ScoringPageParseError):
        spp = ScoringPageParser("<div class='game_mode'></div><div data-modename='mode2' class='game_mode'></div>")
        gmodes = spp.collectGameModes()

    # Test same game_mode
    with pytest.raises(ScoringPageParseError):
        spp = ScoringPageParser("<div data-modename='mode1' class='game_mode'></div><div data-modename='mode1' class='game_mode'></div>")
        gmodes = spp.collectGameModes()

def test_scoring_items():
    # with pytest.warns(ScoringPageParseWarning):
        # Suppress the warning about game modes.  Already tested.
        # Get dict with two items each for _tally and _flag
        input = """
            <div class="scoring">
            <div class="score_tally" data-scorename="Test Tally 1"></div>
            <div class="score_tally" data-scorename="Test Tally 2"></div>
            <div class="score_flag" data-scorename="Test Flag 1"></div>
            <div class="score_flag" data-scorename="Test Flag 2"></div>
            </div>
        """
        spp = ScoringPageParser(input)
        scoring_dict = spp.collectScoringItems()
        assert "score_tally" in scoring_dict.keys()
        assert ["Test Tally 1", "Test Tally 2"].sort() == scoring_dict["score_tally"].sort()
        assert "score_flag" in scoring_dict.keys()
        assert ["Test Flag 1", "Test Flag 2"].sort() == scoring_dict["score_flag"].sort()    

        # Fail because no scoring items found
        with pytest.raises(ScoringPageParseError):
            input = """
                <div  data-scorename="Test Tally 1"></div>
                <div  data-scorename="Test Tally 2"></div>
                <div  data-scorename="Test Flag 1"></div>
                <div  data-scorename="Test Flag 2"></div>
            """
            spp = ScoringPageParser(input)
            scoring_dict = spp.collectScoringItems()

        # Fail because two scoring items with same name in same mode found
        with pytest.raises(ScoringPageParseError):
            input = """
                <div class="score_tally" data-scorename="Same Name"></div>
                <div class="score_tally" data-scorename="Same Name"></div>
                <div class="score_flag" data-scorename="Test Flag 1"></div>
                <div class="score_flag" data-scorename="Test Flag 2"></div>
            """
            spp = ScoringPageParser(input)
            scoring_dict = spp.collectScoringItems()

        # Fail because two scoring items with same name in different modes found
        with pytest.raises(ScoringPageParseError):
            input = """
                <div class="score_tally" data-scorename="Same Name"></div>
                <div class="score_tally" data-scorename="Test Tally 2"></div>
                <div class="score_flag" data-scorename="Test Flag 1"></div>
                <div class="score_flag" data-scorename="Same Name"></div>
            """
            spp = ScoringPageParser(input)
            scoring_dict = spp.collectScoringItems()

        # Fail because scoring item with onlyformode has mode that does not exist
        with pytest.raises(ScoringPageParseError):
            input = """
                <div class="score_tally" data-onlyformode="not exist" data-scorename="Same Name"></div>
                <div class="score_tally" data-scorename="Test Tally 2"></div>
                <div class="score_flag" data-scorename="Test Flag 1"></div>
                <div class="score_flag" data-scorename="Same Name"></div>
            """
            spp = ScoringPageParser(input)
            scoring_dict = spp.collectScoringItems()

        # Fail because no activity name defined
        with pytest.raises(ScoringPageParseError):
            input = """
                <div class="score_tally"></div>
            """
            spp = ScoringPageParser(input)
            scoring_dict = spp.collectScoringItems()

@pytest.fixture
def get_test_data_path() -> Path:
    current_file_path = Path(__file__)
    data_path = current_file_path.parent/"data"
    return data_path

def test_full_page_parse(get_test_data_path: Path):
    # Full success
    test_file = get_test_data_path/"scoring_parse_success.html"
    with test_file.open() as f:
        spp = ScoringPageParser(f)
        spr = spp.parseScoringElement()
        assert spr.hasErrors() == False
        assert spr.hasWarnings() == False
        assert len(spr.game_modes) == 2
        for st in ScoringClassTypes.list():
            assert st in spr.scoring_elements.keys()

    # Make sure errors and warnings are collected correctly
    test_file = get_test_data_path/"scoring_parse_err_warn.html"
    with test_file.open() as f:
        spp = ScoringPageParser(f)
        spr = spp.parseScoringElement()
        assert spr.hasErrors() == True
        assert len(spr.errors) == 1
        assert spr.hasWarnings() == True
        assert len(spr.warnings) == 1
        
def test_validation_output(capfd, get_test_data_path):
    # Full success
    test_file = get_test_data_path/"scoring_parse_success.html"
    with test_file.open() as f:
        spp = ScoringPageParser(f)
        spr = spp.validateScoringElement()
        assert spr.hasErrors() == False
        assert spr.hasWarnings() == False
        out, err = capfd.readouterr()
        assert out == "[+] Scoring element passed validation!\n"

    # Make sure errors propogate
    test_file = get_test_data_path/"scoring_parse_err_warn.html"
    with pytest.raises(ScoringPageParseError):
        with test_file.open() as f:
            spp = ScoringPageParser(f)
            spr = spp.validateScoringElement()
            
    # Make sure warnings print
    # Clear capfd?
    out, err = capfd.readouterr()
    test_file = get_test_data_path/"scoring_parse_warn.html"
    with test_file.open() as f:
        spp = ScoringPageParser(f)
        spr = spp.validateScoringElement()
        out, err = capfd.readouterr()
        # Remove the \n from the capture output because capfd puts extra new lines in place every 80 char
        # Removing the newlines will make this test easier to run.
        assert out.replace("\n", "") == "[w] No element with 'game_mode_group' class present.  It's not mandatory but it's a good idea to keep your game_mode selectors in one area of UI" + \
                        "[+] Scoring element passed validaton, but please read through warnings to make sure you didn't miss anything important to you!"
        
def test_template_validation(capfd, getFullTemplateFile):
    with getFullTemplateFile.open() as f:
        parser = ScoringPageParser(f)
        result = parser.validateScoringElement()
        assert result.hasErrors() == False
        assert result.hasWarnings() == False
        out, err = capfd.readouterr()
        assert out == "[+] Scoring element passed validation!\n"
    
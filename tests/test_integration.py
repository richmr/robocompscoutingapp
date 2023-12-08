import pytest
from pathlib import Path
from tomlkit import TOMLDocument, table
from functools import reduce

from sqlalchemy import select, delete

from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing
from robocompscoutingapp.AppExceptions import IntegrationPageNotValidated
from robocompscoutingapp.Integrate import Integrate
from robocompscoutingapp.ORMDefinitionsAndDBAccess import (
    ScoringPageStatus,
    ModesForScoringPage,
    ScoringItemsForScoringPage,
    RCSA_DB
)

def gen_test_config(temp_dir_path:Path):
    new_doc = TOMLDocument()
    server_config = table()
    server_config.add("scoring_database", f"{temp_dir_path}/rcsa_scoring.db")
    server_config.add("scoring_page", "tests/data/integration_test_data/integration_test.html")
    new_doc["Server_Config"] = server_config
    return new_doc

def test_not_validated_error(tmp_path):
    RCSA_Config.getConfig(test_TOML=gen_test_config(tmp_path))
    # Check for validated file (giggle check)
    file = RCSA_Config.getConfig()["Server_Config"]["scoring_page"]
    uhp = UserHTMLProcessing(file)
    valid_found = uhp.checkForValidatedPageEntry()
    assert valid_found is None

    # Now check to make sure Integrate throws the error
    with pytest.raises(IntegrationPageNotValidated):
        integration = Integrate()
        integration.verifyScoringPageValidated()


def setupTempDB(temp_path):
    # Ensures the target page is entered into the DB
    RCSA_Config.getConfig(test_TOML=gen_test_config(temp_path))
    # Process working file
    file = RCSA_Config.getConfig()["Server_Config"]["scoring_page"]
    uhp = UserHTMLProcessing(file)
    validated = uhp.validate()
    assert validated == True

def getScoringPageID():
    with RCSA_DB.getSQLSession() as db:
        # Should hopefully only be one loaded for these tests
        sps = db.scalars(select(ScoringPageStatus)).one()
        assert isinstance(sps, ScoringPageStatus)
        return sps.scoring_page_id

def deleteIntegrationEntries():
    todelete = [
        ModesForScoringPage
    ]
    with RCSA_DB.getSQLSession() as dbsession:
        for table in todelete:
            dbsession.execute(delete(ModesForScoringPage))
        dbsession.commit()

def test_scoring_modes(tmp_path):
    # Just make sure fake game modes are working
    setupTempDB(tmp_path)    
    # Integrate it
    integrate = Integrate()
    scoring_page_id = getScoringPageID()
    game_modes = ["auton","teleop"]
    result = integrate.addGameModesToDatabase(scoring_page_id, game_modes)
    assert "auton" in result
    assert "teleop" in result

    # Verify in the database
    with RCSA_DB.getSQLSession() as db:
        rows = db.execute(select(ModesForScoringPage))
        for row in rows.scalars():
            print(row)
            assert result[row.mode_name] == row.mode_id

    # teardown the db
    deleteIntegrationEntries()

def test_scoring_items(tmp_path):
    setupTempDB(tmp_path)
    integrate = Integrate()
    scoring_page_id = getScoringPageID()
    scoring_items = {
        "score_tally":[
            "bottles",
            "cans"
        ],
        "score_flag": [
            "dieded"
        ]
    }
    result = integrate.addScoringItemsToDatabase(scoring_page_id, scoring_items)
    assert "bottles" in result
    assert "dieded" in result

    # Verify in the database
    with RCSA_DB.getSQLSession() as db:
        for index, (key, value) in enumerate(scoring_items.items()):
            for an_item in value:
                item = db.scalars(select(ScoringItemsForScoringPage).filter_by(name=an_item)).one()
                assert item.type == key
                assert item.scoring_item_id == result[an_item]
    
    # teardown the db
    deleteIntegrationEntries()
    

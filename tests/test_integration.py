from contextlib import contextmanager
import os
import pytest
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.Initialize import Initialize
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing
from robocompscoutingapp.AppExceptions import IntegrationPageNotValidated
from robocompscoutingapp.Integrate import Integrate
from robocompscoutingapp.ORMDefinitionsAndDBAccess import (
    ScoringPageStatus,
    ModesForScoringPage,
    ScoringItemsForScoringPage,
    RCSA_DB
)


def getScoringPageID():
    with RCSA_DB.getSQLSession() as db:
        # Should hopefully only be one loaded for these tests
        sps = db.scalars(select(ScoringPageStatus)).one()
        assert isinstance(sps, ScoringPageStatus)
        return sps.scoring_page_id



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

def test_not_validated_error(tmp_path):
    # get location of test page
    not_validated = Path("tests/data/integration_test_data/not_validated.html").absolute()
    with gen_test_env_and_enter(tmp_path):
        # Check for validated file (giggle check)
        # Need a different file because the one in the config will now have been added to the database
        config = RCSA_Config.getConfig()
        config.ServerConfig.scoring_page = not_validated
        uhp = UserHTMLProcessing(config.ServerConfig.scoring_page)
        valid_found = uhp.checkForValidatedPageEntry()
        assert valid_found is None

        # Now check to make sure Integrate throws the error
        with pytest.raises(IntegrationPageNotValidated):
            integration = Integrate()
            integration.verifyScoringPageValidated()

def test_full_integration(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        scoring_page_id = getScoringPageID()
        
        # Values from the integration_test.html
        expected_modes = ['Auton', 'Teleop']
        expected_items = {'score_tally': ['cone', 'cube'], 'score_flag': ['Attempted charge', 'Succeeded charge', 'Auton Mobility', 'Broke']}

        integrate = Integrate()
        (mode_id_dict,  scoring_item_id_dict) = integrate.integrate()
        assert mode_id_dict is not None
        assert scoring_item_id_dict is not None

        # Verify in DB
        with RCSA_DB.getSQLSession() as db:
            for index, (key, value) in enumerate(expected_items.items()):
                for an_item in value:
                    item = db.scalars(select(ScoringItemsForScoringPage).filter_by(name=an_item)).one()
                    assert item.type == key
                    
            for mode in expected_modes:
                item = db.scalars(select(ModesForScoringPage).filter_by(mode_name=mode)).one()
                assert item.scoring_page_id == scoring_page_id

            this_page = db.scalars(select(ScoringPageStatus).filter_by(scoring_page_id=scoring_page_id)).one()
            assert this_page.integrated == True
        
        # verify re-run doesn't add more database entries
        (mode_id_dict2,  scoring_item_id_dict2) = integrate.integrate()
        # this might work?
        assert mode_id_dict2 == mode_id_dict
        assert scoring_item_id_dict2 == scoring_item_id_dict

        # Double check the unique constraint holds
        with pytest.raises(IntegrityError):
            integrate.addScoringItemsToDatabase(scoring_page_id, expected_items)

       
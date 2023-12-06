import pytest
from pathlib import Path
from tomlkit import TOMLDocument, table

from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing

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


def test_scoring_modes():
    pass

from pathlib import Path
import tempfile

from test_global_configs import getTestConfig

from robocompscoutingapp.ORMDefinitionsAndDBAccess import RCSA_DB, rcsa_scoring_tables
from robocompscoutingapp.GlobalItems import rcsa_database_name

def test_create_database():
    # First call getTestConfig to set the global config singleton
    config = getTestConfig()

    # Now establish tempdir and modify the config
    with tempfile.TemporaryDirectory() as tempdir:
        config["Server_Config"]["user_static_folder"] = tempdir
        # Call RCSA_DB() to get it set up
        # RCSA_DB()
        #  Now open the session
        with RCSA_DB.getSQLSession(reset=True) as session:
            db_file = Path(config["Server_Config"]["scoring_database"])
            assert db_file.exists()

            # check declared tables are made
            made_tables = set(rcsa_scoring_tables.metadata.tables.keys())
            expected_tables = {
                "ScoringPageStatus"
            }

            leftovers = expected_tables - made_tables
            assert len(leftovers) == 0


# Tools for test mode.
from contextlib import contextmanager
from pathlib import Path
import time
import shutil
from sqlalchemy import select, distinct, func, delete, desc


from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.ScoringData import getCurrentScoringPageData
from robocompscoutingapp.ORMDefinitionsAndDBAccess import RCSA_DB, ScoringPageStatus
from robocompscoutingapp.GlobalItems import FancyText as ft

@contextmanager
def configure_for_testing(cleanup:bool = True):
    """
    Protects the existing configurations and database
    """
    ft.print("Setting up testing environment")
    # get an existing DB session now before changing
    with RCSA_DB.getSQLSession() as orig_db:
        try:
            RCSA_Config.getConfig().FRCEvents.first_event_id = "CALA"
            src_db = RCSA_Config.getConfig().ServerConfig.scoring_database
            dst_db = Path(f"testing_database_{int(time.time())}.db").absolute()
            if src_db.exists():
                shutil.copy(str(src_db), str(dst_db))
            RCSA_Config.getConfig().ServerConfig.scoring_database = dst_db
            RCSA_Config.getConfig().ServerConfig.log_level = "INFO"
            yield
        except Exception as badnews:
            ft.error(f"Test server failed because {badnews}")
        finally:
            # Need to copy over the testing status for the scoring page to the original db
            from_temp_db_sps = getCurrentScoringPageData()
            if from_temp_db_sps is not None:
                orig_sps = orig_db.scalars(select(ScoringPageStatus).where(ScoringPageStatus.scoring_page_id==from_temp_db_sps.scoring_page_id)).one()
                orig_sps.tested = from_temp_db_sps.tested
                orig_db.commit()
            if cleanup:
                if RCSA_Config.getConfig().ServerConfig.scoring_database.exists():
                    RCSA_Config.getConfig().ServerConfig.scoring_database.unlink()
                    ft.print("Temporary database deleted")
            else:
                ft.print(f"Data from this test can be found in {RCSA_Config.getConfig().ServerConfig.scoring_database}")
            # ft.success("Test complete!")



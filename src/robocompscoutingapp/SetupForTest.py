# Tools for test mode.
from contextlib import contextmanager
from pathlib import Path
import time
import shutil

from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.GlobalItems import FancyText as ft

@contextmanager
def configure_for_testing(cleanup:bool = True):
    """
    Protects the existing configurations and database
    """
    ft.print("Setting up testing environment")
    try:
        RCSA_Config.getConfig().FRCEvents.first_event_id = "CALA"
        src_db = RCSA_Config.getConfig().ServerConfig.scoring_database
        dst_db = Path(f"testing_database_{int(time.time())}.db").absolute()
        shutil.copy(str(src_db), str(dst_db))
        RCSA_Config.getConfig().ServerConfig.scoring_database = dst_db
        RCSA_Config.getConfig().ServerConfig.log_level = "INFO"
        yield
    except Exception as badnews:
        ft.error(f"Test server failed because {badnews}")
    finally:
        if cleanup:
            RCSA_Config.getConfig().ServerConfig.scoring_database.unlink()
            ft.print("Temporary database deleted")
        else:
            ft.print(f"Data from this test can be found in {RCSA_Config.getConfig().ServerConfig.scoring_database}")
        ft.success("Test complete!")



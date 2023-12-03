import pytest
from pathlib import Path
import tempfile
from tomlkit import TOMLDocument, table, comment
from tomlkit.toml_file import TOMLFile

from robocompscoutingapp.Initialize import Initialize

def test_overall_initialize():
    with tempfile.TemporaryDirectory() as tempdir:
        td = Path(tempdir)
        init = Initialize(td)
        init.initialize(overwrite=True)
        # Test the TOML config.  There's really no reason the copying should fail
        config = TOMLFile(f"{tempdir}/rcsa_config.toml").read()
        assert config["Server_Config"]["user_static_folder"] == f"{tempdir}/static"
        assert config["Server_Config"]["scoring_database"] == f"{tempdir}/rcsa_scoring.db"
        assert config["Server_Config"]["log_folder"] == f"{tempdir}/logs"

        # Test overwrite warning
        with pytest.raises(FileExistsError):
            init.initialize()

        



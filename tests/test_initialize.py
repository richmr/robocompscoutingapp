import pytest
from pathlib import Path
import tempfile
from tomlkit import TOMLDocument, table, comment
from tomlkit.toml_file import TOMLFile
import shutil
import os
from contextlib import contextmanager

from robocompscoutingapp.Initialize import Initialize

@contextmanager
def gen_test_env_and_enter(temp_dir):
    try:
        #protect existing secrets file
        existing_secrets_file = Path("~/.RCSA_SECRETS.toml").expanduser().absolute()
        protected_secrets_file = Path("~/.PROTECTED_RCSA_SECRETS.toml").expanduser().absolute()
        moved_secrets_file = False
        if existing_secrets_file.exists():
            shutil.move(str(existing_secrets_file),str(protected_secrets_file))
            moved_secrets_file = True
        cwd = os.getcwd()
        os.chdir(temp_dir)
        yield
    except Exception as badnews:
        print("Failed test detected")
        print(f"Temp dir: {temp_dir}")
        raise(badnews)
    finally:
        os.chdir(cwd)
        if moved_secrets_file:
            shutil.move(str(protected_secrets_file), str(existing_secrets_file))


def test_overall_initialize(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        init = Initialize(Path("."))
        init.initialize(overwrite=True)
        # Test the TOML config.  There's really no reason the copying should fail
        config = TOMLFile(f"{tmpdir}/rcsa_config.toml").read()
        assert config["ServerConfig"]["user_static_folder"] == f"{tmpdir}/static"
        assert config["ServerConfig"]["scoring_database"] == f"{tmpdir}/rcsa_scoring.db"
        assert config["ServerConfig"]["log_filename"] == f"{tmpdir}/logs/rcsa_logs.log"
        # Ensure the secrets file copied over
        assert Path("~/.RCSA_SECRETS.toml").expanduser().absolute().exists()

        # Test overwrite warning
        with pytest.raises(FileExistsError):
            init.initialize()

def test_TOML_updating(tmpdir):
    with gen_test_env_and_enter(tmpdir):
        # Test
        init = Initialize()
        init.initialize(overwrite=True)
        assert init.isTOMLInDir() == True

        # Update test
        init.updateTOML(["ServerConfig", "scoring_page"], "updated.file")

        # Check
        config = TOMLFile("rcsa_config.toml").read()
        assert config["ServerConfig"]["scoring_page"] == "updated.file"
        




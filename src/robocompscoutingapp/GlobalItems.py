"""
Collection of configuration items that are used across many parts of application
"""
#from rich import print
from enum import Enum
import rich
import pytest
from pathlib import Path
from tomlkit import TOMLDocument, table, comment
from tomlkit.toml_file import TOMLFile

from robocompscoutingapp.FirstEventsAPI import FirstEventsConfig

class ExtendedEnum(Enum):
    """
    Taken from: https://stackoverflow.com/questions/29503339/how-to-get-all-values-from-python-enum-class
    Generates a list of value names for this enum
    """
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

class ScoringClassTypes(ExtendedEnum):
    """
    Add possible scoring types here
    The value is the class name the parser will look for and also use to set up scoring logic
    You'll also need to add logic to the API end to understand and handle these scoring types
    """
    score_tally = "score_tally"     # Scoring events that additively increase per event (i.e. balls in a goal)
    score_flag = "score_flag"       # Scoring events that are True/False (i.e. it happened or didn't)

# 'Rich' text 
class FancyText:
    err = "[red bold]\[!][/][red]"
    wrn = "[yellow]\[w]"

    @classmethod
    def error(cls, message):
        rich.print(f"{cls.err} {message}")

    @classmethod
    def warning(cls, message):
        rich.print(f"{cls.wrn} {message}")

    @classmethod
    def success(cls, message):
        rich.print(f"[green]\[+] {message}[/green]")

    @classmethod
    def print(cls, message):
        # Pass through to rich.print to prevent needing to import if a specific message has specfic needs.
        rich.print(message) 

# The location of the fully working template, to be used in test
@pytest.fixture
def getFullTemplateFile() -> Path:
    current_file_path = Path(__file__)
    working_template = current_file_path.parent/"web/pages/full_template.html"
    return working_template

# Name of critical scripts that power scoring engine
rcsa_fixed_script_prefix = "/rcsa"
rcsa_js_loader = f"{rcsa_fixed_script_prefix}/rcsa_loader.js"

# name for rcsa database
rcsa_database_name = "rcsa_scoring.db"

# name for the primary config file
rcsa_config_filename = "rcsa_config.toml"

class RCSA_Config:
    """
    Class that connects to the toml file and returns TOML object to use
    """

    _TOMLDocument = None
    _FirstConfig = None

    @classmethod
    def getConfig(cls, reset:bool = False, test_TOML:TOMLDocument = None) -> TOMLDocument:
        """
        Class method to access the singleton Configuration page.

        Parameters
        ----------
        reset:bool
            Forces the stored _TOMLDocument to reset to None.  This is mainly used in testing to ensure changes to configs don't leak into subsequent tests        
        
        test_TOML:TOMLDocument
            Sets the Config document to the provided TOML.  Used for test configurations mainly

        Returns
        -------
        TOMLDocument
            A TOMLDocument representing the configuration settings
        """
        if reset:
            cls._TOMLDocument = None

        if test_TOML is not None:
            cls._TOMLDocument = test_TOML

        if cls._TOMLDocument is None:
            toml_path = Path(rcsa_config_filename)
            if not toml_path.exists():
                raise FileNotFoundError(f"{rcsa_config_filename} expected in current working directory.  Run this app from the directory you created with 'initialize'")
            # type(self) here to set the class, not instance variable
            cls._TOMLDocument = TOMLFile(toml_path).read()
        return cls._TOMLDocument
    
    @classmethod
    def getFirstConfig(cls) -> FirstEventsConfig:
        if cls._FirstConfig is None:
            config = cls.getConfig()["FRC_events"]
            cls._FirstConfig = FirstEventsConfig.model_validate(config)
        return cls._FirstConfig
    
from contextlib import contextmanager
import os

@contextmanager
def temp_chdir(tgt_dir):
    """
    Context manager to temporarily change directory and then return to original on completion.
    This is mainly used for testing in this app
    
    Parameters
    ----------
    tgt_dir:str
        The string path of where you want to change the working directory to
    """
    cwd = os.getcwd()
    try:
        os.chdir(tgt_dir)
        yield
    finally:
        os.chdir(cwd)
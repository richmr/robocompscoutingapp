"""
Tools to support initialize command
"""
from pathlib import Path
from importlib import resources
import shutil

from tomlkit import TOMLDocument, table, comment
from tomlkit.toml_file import TOMLFile

from robocompscoutingapp.GlobalItems import rcsa_config_filename

class Initialize:

    def __init__(self, target_directory:Path) -> None:
        self.dst_path = target_directory

        # set the src directory
        with resources.path("robocompscoutingapp", "Initialize") as src_path:
            self.src_path = src_path.parent/"initialize"

    def initialize(self, overwrite:bool=False):
        """
        Calls all the initialize steps as needed

        Parameter
        ---------
        overwrite : bool
            Passed along to copy() to allow overwriting of files

        Returns
        -------
        None
        """
        self.copy(overwrite=overwrite)
        self.setupTOML()
    
    def copy(self, overwrite=False):
        """
        Copies all the files in the package 'initialize' directory to the target directory
        Set overwrite to "True" to re-initialize a directory
        """
        shutil.copytree(str(self.src_path), str(self.dst_path), dirs_exist_ok=overwrite)

    def setupTOML(self):
        """
        Sets the user_static_folder to the static folder in the initialized folder structure
        """
        rcsa_config_file = TOMLFile(self.dst_path/rcsa_config_filename)
        rcsa_config = rcsa_config_file.read()
        rcsa_config["Server_Config"]["user_static_folder"] = str(self.dst_path.absolute()/"static")
        rcsa_config["Server_Config"]["scoring_database"] = str(self.dst_path.absolute()/"rcsa_scoring.db")
        rcsa_config["Server_Config"]["log_folder"] = str(self.dst_path.absolute()/"logs")
        
        rcsa_config_file.write(rcsa_config)

        




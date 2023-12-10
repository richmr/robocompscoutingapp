"""
Tools to support initialize command
"""
from pathlib import Path
from importlib_resources import files
import shutil

from tomlkit import TOMLDocument, table, comment
from tomlkit.toml_file import TOMLFile

from robocompscoutingapp.GlobalItems import rcsa_config_filename

class Initialize:

    def __init__(self, target_directory:Path) -> None:
        self.dst_path = Path(target_directory)

        # set the src directory
        self.src_path = files('robocompscoutingapp.Initialize').joinpath("initialize")
        

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

    def isTOMLInDir(self, tgt_dir:Path = Path('.')) -> bool:
        """
        This examines the current working directory for the TOML file

        Parameters
        ----------
        tgt_dir
            Location to look for the TOML (default is current working directory)
                
        Returns
        -------
        bool
            Is TOML file in the provided directory
        """
        file = tgt_dir/rcsa_config_filename
        return file.exists()
    
    def updateTOML(self, key_list:list, value, tgt_dir:Path = Path('.')):
        """
        Updates a single TOML value to the value provided.
        
        Parameters
        ----------
        key_list:list
            A list of nested keys like ["Server_Config", "user_static_folder"] to get to the key you are looking for.
            The above is the same as TOMLDocument["Server_Config"]["user_static_folder"].  No key checking provided

        value
            The value to set the key to.  No type checking, user must get it right for the TOML

        tgt_dir
            Location to look for the TOML (default is current working directory)    

        Returns
        -------
            None
        """
        file = tgt_dir/rcsa_config_filename
        rcsa_config_file = TOMLFile(file)
        rcsa_config = rcsa_config_file.read()
        target_key = rcsa_config[key_list[0]]
        for key in key_list[1:-1]:
            target_key = target_key[key]
        target_key[key_list[-1]] = value
        rcsa_config_file.write(rcsa_config)


        
        




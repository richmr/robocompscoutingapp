from pathlib import Path
from string import Template
from uvicorn import Config
import uvicorn

from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.web.ThreadedUvicorn import ThreadedUvicorn
class RunAPIServer:

    def __init__(self, yaml_file_template:Path = Path("logs/.template.rcsa_log_config.yaml"),
                 destination_yaml_file:Path = Path("logs/rcsa_log_config.yaml"),
                 daemon:bool = False
                 ) -> None:
        """
        Make a RunAPIServer instance
        
        Parameters
        ----------
        yamlFile:Path
            The Path-object to the location of the target YAML.  If none provided, defaults to expected location from 
            Initialize
        daemon:bool
            Will this server run as daemon?
        """
        self.yaml_file_template = Path(yaml_file_template)
        self.destination_yaml_file = Path(destination_yaml_file)
        self.server_config = RCSA_Config.getConfig().ServerConfig
        self.daemon = daemon

    def setupLoggingYAML(self):
        """
        Access the config file and modify the Logging YAML file to meet settings.
        """
        # We log to console and file by default
        handlers = "[console, file]"
        # But not to console if daemon
        if self.daemon:
            handlers = "[file]"
        file_edits = {
            "log_filename":self.server_config.log_filename,
            "log_level":self.server_config.log_level,
            "handlers":handlers
        }
        try:
            with open(self.yaml_file_template) as f:
                original = Template(f.read())
                fixed = original.substitute(file_edits)

            with open(self.destination_yaml_file, "w") as fix:
                fix.write(fixed)
        except Exception as badnews:
            raise(Exception(f"Unable to edit logging YAML file {self.destination_yaml_file} because {badnews}"))
        
    def run(self):
        """
        Runs the server
        """
        self.setupLoggingYAML()
        host = self.server_config.IP_Address
        port = self.server_config.port
        config = Config("robocompscoutingapp.web:rcsa_api_app", host=host, port=port, reload=False, log_config=str(self.destination_yaml_file))
        self.server = ThreadedUvicorn(config)
        self.server.start()

    def stop(self):
        """
        Stops the server
        """
        self.server.stop()



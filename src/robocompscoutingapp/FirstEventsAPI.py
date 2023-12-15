from pathlib import Path
from pydantic import BaseModel
import requests

from robocompscoutingapp.GlobalItems import RCSA_Config

class FirstEventsAPI:
    """
    Interface to the First Events API
    """

    def __init__(self, APIKey:str, first_event_id:str, api_url_root:str = "https://frc-api.firstinspires.org/v3.0/") -> None:
        """
        Set up session and common headers        
        """
        self.api_session = requests.Session()
        self.api_session.headers.update({
            # API key added this way and not native auth() because I had users store the key as B64 encoded already
            "Authorization: Basic":APIKey,
            "Accept":"application/json"
        })
        self.first_event_id = first_event_id
        self.api_url_root = api_url_root

    
    
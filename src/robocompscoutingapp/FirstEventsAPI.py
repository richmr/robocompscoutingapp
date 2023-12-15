from pathlib import Path
from pydantic import BaseModel
from typing import Union, List
import requests
import datetime

# from robocompscoutingapp.GlobalItems import RCSA_Config

# Defining all these Pydantic models so I don't have to guess at key values later
class FirstEventsConfig(BaseModel):
    APIKey_File:Path
    first_event_id: Union[bool, str]
    district_id: Union[bool, str]
    URL_Root:str

class FirstDistrict(BaseModel):
    code:str
    name:str

class FirstEventsAPI:
    """
    Interface to the First Events API
    """

    def __init__(self, config:FirstEventsConfig, season:int = None) -> None:
        """
        Set up session and common headers        
        """
        self.config = config
        self.api_session = requests.Session()
        # Expand user used here because I encourage "~" as a location to store the key
        with config.APIKey_File.expanduser().absolute().open() as f:
            self.api_session.headers.update({
                # API key added this way and not native auth() because I had users store the key as B64 encoded already
                "Authorization":"Basic " + f.readline().strip(),
                "Accept":"application/json"
            })
        if season is None:
            season = datetime.date.today().year
        self.config.URL_Root += f"{season}/"

    def getDistricts(self) -> List[FirstDistrict]:
        url = self.config.URL_Root + "districts"
        r = self.api_session.get(url).json()
        toreturn = [FirstDistrict.model_validate(d) for d in r["districts"]]
        return toreturn


    
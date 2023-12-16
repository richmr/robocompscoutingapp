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

class FirstEvent(BaseModel):
    code:str
    name:str
    dateStart:datetime.datetime
    dateEnd:datetime.datetime

class FirstTeam(BaseModel):
    eventCode:str
    nameShort:str
    teamNumber:int

class FirstMatch(BaseModel):
    eventCode:str
    description:str
    matchNumber:int
    Red1:int
    Red2:int
    Red3:int
    Blue1:int
    Blue2:int
    Blue3:int

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

    def getEvents(self, districtCode:str = None) -> List[FirstEvent]:
        """
        Get first events
        
        Parameters
        ----------
        districtCode:str
            Optional district code to narrow results

        Returns
        -------
        List[FirstEvent]
            List of all the events found
        """
        params = districtCode 
        if params is not None:
            params = {
                "districtCode":districtCode
            }
        url = self.config.URL_Root + "events"
        r = self.api_session.get(url, params=params).json()
        toreturn = [FirstEvent.model_validate(e) for e in r["Events"]]
        return toreturn
        
    def getTeamsAtEvent(self, eventCode:str) -> List[FirstTeam]:
        """
        Get the teams at an event

        Parameters
        ----------
        eventCode:str
            Valid event code we are scoring

        Returns
        -------
        List[FirstTeam]
            List of Team objects with shortName and teamNumber
        """
        params = {
            "eventCode":eventCode
        }
        url = self.config.URL_Root + "teams"
        r = self.api_session.get(url, params=params).json()
        # t | {"eventCode":eventCode} adds the eventCode to the t dict and returns a dict
        toreturn = [FirstTeam.model_validate(t | {"eventCode":eventCode}) for t in r["teams"]]
        return toreturn

    def getMatchesAtEvent(self, eventCode:str) -> List[FirstMatch]:
        """
        Get all matches for an event code

        Parameters
        ----------
        eventCode:str
            Valid event code we are scoring

        Returns
        -------
        List[FirstMatch]
            List of match objects detailing 
        """
        # Scouting really only happens during qualification
        params = {
            "tournamentLevel":"qual"
        }
        url = self.config.URL_Root + f"schedule/{eventCode}"
        r = self.api_session.get(url, params=params).json()
        toreturn = []
        for event in r["Schedule"]:
            event_dict = {
                "eventCode":eventCode,
                "description":event["description"],
                "matchNumber":event["matchNumber"]
            }
            for team in event["teams"]:
                event_dict[team["station"]] = team["teamNumber"]
            toreturn.append(FirstMatch.model_validate(event_dict))
        return toreturn
    


    
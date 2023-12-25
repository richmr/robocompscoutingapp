from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from typing import Union, List
import requests
from requests.auth import HTTPBasicAuth
import datetime

from robocompscoutingapp.GlobalItems import RCSAConfig

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
    model_config = ConfigDict(from_attributes=True)

    eventCode:str
    nameShort:str
    teamNumber:int

class FirstMatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    eventCode:str
    description:str
    matchNumber:int
    Red1:int
    Red2:int
    Red3:int
    Blue1:int
    Blue2:int
    Blue3:int
    scored:bool = Field(default=False)

class NoAPIKeyProvided(Exception):
    pass

class FirstEventsAPI:
    """
    Interface to the First Events API
    """

    def __init__(self, config:RCSAConfig, season:int = None) -> None:
        """
        Set up session and common headers        
        """
        self.config = config.FRCEvents
        self.api_session = requests.Session()
        # basic = HTTPBasicAuth(config.Secrets.FRC_Events_API_Username, config.Secrets.FRC_Events_API_Auth_Token)
        # Check the API key values
        if config.Secrets.FRC_Events_API_Username == "sampleuser":
            raise(NoAPIKeyProvided("You did not update the the default API key username in "))
        self.api_session.auth = (config.Secrets.FRC_Events_API_Username, config.Secrets.FRC_Events_API_Auth_Token)
        self.api_session.headers.update({"Accept":"application/json"})
        if season is None:
            season = datetime.date.today().year
        self.URL_Root = self.config.URL_Root + f"{season}/"

    def getDistricts(self) -> List[FirstDistrict]:
        url = self.URL_Root + "districts"
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
        url = self.URL_Root + "events"
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
        url = self.URL_Root + "teams"
        r = self.api_session.get(url, params=params)
        if "Invalid Event Requested" in r.text:
            raise ValueError(f"{eventCode} is not valid")
        r = r.json()
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
        url = self.URL_Root + f"schedule/{eventCode}"
        r = self.api_session.get(url, params=params)
        if "Invalid Event Requested" in r.text:
            raise ValueError(f"{eventCode} is not valid")
        r = r.json()
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
    


    
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, ConfigDict
from typing import Dict, List, Union

from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing
from robocompscoutingapp.ORMDefinitionsAndDBAccess import (
    ScoringPageStatus,
    ModesForScoringPage,
    ScoringItemsForScoringPage,
    TeamsForEvent,
    MatchesForEvent,
    ScoresForEvent,
    RCSA_DB
)

_scoring_page_id = None

def getCurrentScoringPageID():
    """
    Uses current scoring page hash to get the scoring page ID
    """
    global _scoring_page_id
    if _scoring_page_id is None:
        sp = RCSA_Config.getConfig()["Server_Config"]["scoring_page"]
        uhp = UserHTMLProcessing(sp)
        _scoring_page_id = uhp.checkForValidatedPageEntry().scoring_page_id
    return _scoring_page_id

class GameMode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mode_name:str
    mode_id:int

class ScoringItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name:str
    scoring_item_id:int
    type:str

class ModesAndItems(BaseModel):
    modes:Dict[str, GameMode]
    scoring_items:Dict[str, ScoringItem]

def getGameModeAndScoringElements(scoring_page_id:int) -> ModesAndItems:
    """
    Returns all of the named modes an scoring items with their keys

    Parameters
    ----------
    scoring_page_id:int
        Primary key for the scoring page

    Returns
    -------
    ModesAndItems
        Model with all modes and items
    """
    with RCSA_DB.getSQLSession() as db:
        modes = db.scalars(select(ModesForScoringPage).filter_by(scoring_page_id=scoring_page_id)).all()
        mode_dict = {m.mode_name:GameMode.model_validate(m) for m in modes}
        items = db.scalars(select(ScoringItemsForScoringPage).filter_by(scoring_page_id=scoring_page_id)).all()
        item_dict = {i.name:ScoringItem.model_validate(i) for i in items}
        return ModesAndItems(modes=mode_dict, scoring_items=item_dict)

from robocompscoutingapp.FirstEventsAPI import FirstMatch, FirstTeam


def storeTeams(team_list:List[FirstTeam]):
    """
    Saves the list of teams to the database

    Parameters
    ----------
    team_list:List[FirstTeam]
        List of FirstTeam objects (Directly from FirstAPI.getTeamsAtEvent)
    """
    with RCSA_DB.getSQLSession() as db:
        for team in team_list:
            try:
                new_db_team = TeamsForEvent(**team.model_dump())
                db.add(new_db_team)
                db.commit()
            except IntegrityError:
                # Already added for this event
                db.rollback()
            except Exception as badnews:
                raise(f"Unable to add team {team.teamNumber} for event {team.eventCode} because {badnews}")
        
def storeMatches(match_list:List[FirstMatch]):
    """
    Saves the list of teams to the database

    Parameters
    ----------
    match_list:List[FirstMatch]
        List of FirstMatch objects (Directly from FirstAPI.getMatchesAtEvent)
    """
    with RCSA_DB.getSQLSession() as db:
        for match in match_list:
            try:
                new_db_team = MatchesForEvent(**match.model_dump())
                db.add(new_db_team)
                db.commit()
            except IntegrityError:
                # Already added for this event
                db.rollback()
            except Exception as badnews:
                raise(f"Unable to add team {match.matchNumber} for event {match.eventCode} because {badnews}")

class MatchesAndTeams(BaseModel):
    # using dicts here to help with finding info from the scoring page later
    matches:Dict[int, FirstMatch]   # int is the matchNumber
    teams:Dict[int, FirstTeam]      # int is the teamNumber

def getMatchesAndTeams() -> MatchesAndTeams:
    """
    Returns matches and teams for the event (event code is part of configuration)
    """
    with RCSA_DB.getSQLSession() as db:
        # Get the event code
        eventCode = RCSA_Config.getFirstConfig().first_event_id
        # get all the matches
        matches_db = db.scalars(select(MatchesForEvent).filter_by(eventCode=eventCode)).all()
        matches = { m.matchNumber:FirstMatch.model_validate(m) for m in matches_db }
        # get all the teams
        teams_db = db.scalars(select(TeamsForEvent)).all()
        teams = { t.teamNumber: FirstTeam.model_validate(t) for t in teams_db }
        return MatchesAndTeams(
            matches=matches,
            teams=teams
        )



def teamAlreadyScoredForThisMatch(teamNumber:int, matchNumber:int, eventCode:str) -> bool:
    """
    Returns true if this team has already had its scores for this event filed

    Parameters
    ----------
    teamNumber:int
        Official team number
    matchNumber:int
        Match number for this score
    eventCode:str
        Official eventCode for this event

    Returns
    -------
    bool
        True if there are alredy scores for this team, match, and event; False otherwise
    """
    with RCSA_DB.getSQLSession() as db:
        check = db.scalars(select(ScoresForEvent).filter_by(eventCode=eventCode, teamNumber=teamNumber, matchNumber=matchNumber)).all()
        if len(check) > 0:
            return True
        else:
            return False

class Score(BaseModel):
    scoring_item_id:int
    value:Union[str, int, bool, float]

class ScoredMatchForTeam(BaseModel):
    matchNumber:int
    teamNumber:int
    scores:List[Score]

def addScoresToDB(eventCode:str, match_score:ScoredMatchForTeam):
    """
    Saves the recorded scores to the DB

    Parameters
    ----------
    eventCode:str
        Event code for the scored event
    match_score:ScoredMatchForTeam
        ScoredMatchForTeam object
    """
    with RCSA_DB.getSQLSession() as db:
        try:
            to_add = [ScoresForEvent(**a_score.model_dump() | {
                "eventCode":eventCode,
                "matchNumber":match_score.matchNumber,
                "teamNumber":match_score.teamNumber
            }) for a_score in match_score.scores]
            db.add_all(to_add)
            db.commit()
        except IntegrityError:
            raise Exception(f"Your submitted scoring had multiple score entries for the same scoring item, please check.  No scoring data saved.")
        except Exception as badnews:
            raise Exception(f"Unable to add scores to DB because {badnews}")
        



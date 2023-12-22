from sqlalchemy import select, distinct, func
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, ConfigDict, Field
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
        sp = RCSA_Config.getConfig().ServerConfig.scoring_page
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

def getMatchesAndTeams(eventCode:str, unscored_only:bool = True) -> MatchesAndTeams:
    """
    Returns matches (ordered by ascending match number) and teams for the event

    Parameters
    ----------
    eventCode:str
        Official eventCode for this event
    unscored_only:bool
        Only report matches that have yet to be scored.

    Returns
    -------
    MatchesAndTeams
        MatchesAndTeams object
    """
    with RCSA_DB.getSQLSession() as db:
        # get all the matches
        if unscored_only:
            matches_db = db.scalars(select(MatchesForEvent).filter_by(eventCode=eventCode, scored=False).order_by(MatchesForEvent.matchNumber)).all()
        else:
            matches_db = db.scalars(select(MatchesForEvent).filter_by(eventCode=eventCode).order_by(MatchesForEvent.matchNumber)).all()
        # matches_db = db.scalars(select(MatchesForEvent).filter_by(eventCode=eventCode)).all()
        matches = { int(m.matchNumber):FirstMatch.model_validate(m) for m in matches_db }
        # get all the teams
        teams_db = db.scalars(select(TeamsForEvent).filter_by(eventCode=eventCode)).all()
        teams = { int(t.teamNumber): FirstTeam.model_validate(t) for t in teams_db }
        return MatchesAndTeams(
            matches=matches,
            teams=teams
        )

def getMatches(eventCode:str, unscored_only:bool = True) -> MatchesAndTeams:
    """
    Returns matches (ordered by ascending match number) only

    Parameters
    ----------
    eventCode:str
        Official eventCode for this event
    unscored_only:bool
        Only report matches that have yet to be scored.

    Returns
    -------
    MatchesAndTeams
        MatchesAndTeams object (but teams will be empty {})
    """
    with RCSA_DB.getSQLSession() as db:
        # get all the matches
        if unscored_only:
            matches_db = db.scalars(select(MatchesForEvent).filter_by(eventCode=eventCode, scored=False).order_by(MatchesForEvent.matchNumber)).all()
        else:
            matches_db = db.scalars(select(MatchesForEvent).filter_by(eventCode=eventCode).order_by(MatchesForEvent.matchNumber)).all()
        # matches_db = db.scalars(select(MatchesForEvent).filter_by(eventCode=eventCode)).all()
        matches = { m.matchNumber:FirstMatch.model_validate(m) for m in matches_db }
        # get all the teams
        teams = {}
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
    mode_id:int
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
            raise IntegrityError(f"Your submitted scoring had multiple score entries for the same scoring item, please check.  No scoring data saved.")
        # except Exception as badnews:
        #     raise Exception(f"Unable to add scores to DB because {badnews}")

    setMatchToScored(eventCode=eventCode, matchNumber=match_score.matchNumber) 

def setMatchToScored(eventCode:str, matchNumber:int):
    """
    Sets a given match to scored after a logic check is satisfied.  Right now set to after a single team is scored, but here to allow more complicated logic

    Parameters
    ----------
    eventCode:str
        Event code for the scored event
    matchNumber:int
        Match number for the event
    """    
    with RCSA_DB.getSQLSession() as db:
        m = db.scalars(select(MatchesForEvent).filter_by(eventCode=eventCode, matchNumber=matchNumber)).one()
        m.scored = True
        db.commit()
    
class ScoredItemAggregateResult(BaseModel):
    mode_name:str
    name:str
    count_of_scored_events:int = Field(default=0)
    total:Union[int, float] = Field(default=0)
    average:float = Field(default=0)
    # These are here for future expansion, and are meant to to be interepreted by mode_name
    agg_result1:Union[int, str, float] = Field(default=None)
    agg_result2:Union[int, str, float] = Field(default=None)

class ScoresForMode(BaseModel):
    mode_name:str
    # str is the name of the scored item
    scores:Dict[str, ScoredItemAggregateResult]

class ResultsForTeam(BaseModel):
    teamNumber:int
    # str is the mode
    by_mode_results:Dict[str, ScoresForMode]
    # str is the scored item name
    totals:Dict[str, ScoredItemAggregateResult]

class AllTeamResults(BaseModel):
    # int is teamNumber
    data:Dict[int, ResultsForTeam]

class GenerateResultsForTeam:

    def __init__(self, eventCode:str, teamNumber:int, scoring_page_id:int) -> None:
        self.eventCode = eventCode
        self.teamNumber = teamNumber
        self.scoring_page_id = scoring_page_id
        self.modes_by_mode_id = {}
        self.scoring_items_by_id = {}
        self.by_mode_results = {}
        self.totals = {}
        self.list_of_totalled_match_numbers = []
        pass

    def initializeDataStructures(self):
        """
        Sets up empty ScoredItemAggregateResult objects for all score types
        """
        modes_and_items = getGameModeAndScoringElements(self.scoring_page_id)
        for a_mode in modes_and_items.modes.values():
            this_mode_scores = {i.name:ScoredItemAggregateResult(
                mode_name=a_mode.mode_name,
                name=i.name, 
                count_of_scored_events=self.count_of_scored_events
            ) for i in modes_and_items.scoring_items.values()}
            self.by_mode_results[a_mode.mode_name] = ScoresForMode(
                mode_name=a_mode.mode_name,
                scores = this_mode_scores
            )
        self.totals = {i.name:ScoredItemAggregateResult(
            mode_name="Total",
            name=i.name,
            count_of_scored_events=self.count_of_scored_events
        ) for i in modes_and_items.scoring_items.values()}

        # Also repackage modes and items into id indexed dictionaries for easier reference later
        self.modes_by_mode_id = {m.mode_id:m for m in modes_and_items.modes.values()}
        self.scoring_items_by_id = {i.scoring_item_id:i for i in modes_and_items.scoring_items.values()}

    def processTallyScore(self, score:ScoresForEvent):
        """
        Process a tally score type.
        
        Parameters
        ----------
        score:ScoresForEvent
            The specific score to add to the team's data
        """
        # Score this mode and score item name
        mode_name = self.modes_by_mode_id[score.mode_id].mode_name
        score_item_name = self.scoring_items_by_id[score.scoring_item_id].name
        # Get the "reference" to the current object.  Changes to this will propagate to the actual object
        current = self.by_mode_results[mode_name].scores[score_item_name]
        # Values are stored as strings in db for flexibility.  Convert here
        current.total += int(score.value)
        if current.count_of_scored_events > 0:
            current.average = current.total/current.count_of_scored_events

        # Score the totals
        total_current = self.totals[score_item_name]
        # Since there are different entries for different modes for the same match number, we need to see if we already counted this match
        # if score.matchNumber not in self.list_of_totalled_match_numbers:
        #     total_current.count_of_scored_events += 1
        #     self.list_of_totalled_match_numbers.append(score.matchNumber)

        total_current.total += int(score.value)
        if total_current.count_of_scored_events > 0:
            total_current.average = total_current.total/total_current.count_of_scored_events

    def processFlagScore(self, score:ScoresForEvent):
        """
        Process a flag score.  Flag scores are either 0 or 1 so we make those changes to the provided score.
        The actual mechanics behind the scoring are the same as Tally so we forward it on.

        Parameters
        ----------
        score:ScoresForEvent
            The specific score to add to the team's data
        """
        # SqlAlchemy (maybe?) converts "True" to 1 in the database, which means no extra translation needs
        # to be done. I suspect this may be brittle.
        # Safest solution is to ensure the scoring code sends a "1" for a true, and a "0" for a false
        # Either way, we can just pass this through

        self.processTallyScore(score)
        
    def getAggregrateResults(self) -> ResultsForTeam:
        # Get all scores for this team number and event
        with RCSA_DB.getSQLSession() as db:
            self.count_of_scored_events = db.scalars(select(func.count(distinct(ScoresForEvent.matchNumber))).filter_by(teamNumber=self.teamNumber, eventCode=self.eventCode)).one()
            self.initializeDataStructures()
            all_scores_for_team = db.scalars(select(ScoresForEvent).filter_by(teamNumber=self.teamNumber, eventCode=self.eventCode)).all()
            # Route the math per the scoring item type
            for score in all_scores_for_team:
                scoring_type = self.scoring_items_by_id[score.scoring_item_id].type
                match scoring_type:
                    case "score_tally":
                        self.processTallyScore(score)
                    case "score_flag":
                        self.processFlagScore(score)
                    case _:
                        # Really need a logging capability here
                        raise ValueError(f"Score ID {score.score_id} has type {scoring_type} and I do not know how to process it")
                    

        toreturn = ResultsForTeam(
            teamNumber=self.teamNumber,
            by_mode_results=self.by_mode_results,
            totals=self.totals
        )
        return toreturn
        

def getAggregrateResultsForAllTeams(eventCode:str, scoring_page_id:int) -> AllTeamResults:
    """
    Produces the results for all teams

    Parameters
    ----------
    eventCode:str
        The event we are gathering data for
    scoring_page_id:int
        The ID for the scoring page

    Returns
    -------
    AllTeamResults
        All Team Results object
    """
    data = {}
    with RCSA_DB.getSQLSession() as db:
        all_teams = db.scalars(select(TeamsForEvent).filter_by(eventCode=eventCode)).all()
        for team in all_teams:
            score_gen = GenerateResultsForTeam(
                eventCode=eventCode,
                teamNumber=team.teamNumber,
                scoring_page_id=scoring_page_id
            )
            data[team.teamNumber] = score_gen.getAggregrateResults()

    return AllTeamResults(data=data)



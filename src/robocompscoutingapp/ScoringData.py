from sqlalchemy import select, distinct, func, delete, desc
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

class ScoringPageStatus_pyd(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scoring_page_id: int
    validated:bool
    integrated:bool
    tested:bool

def getCurrentScoringPageData() -> ScoringPageStatus_pyd:
    """
    Returns the current scoring page status
    """
    # global _scoring_page_id
    # if _scoring_page_id is None:
    sp = RCSA_Config.getConfig().ServerConfig.scoring_page
    uhp = UserHTMLProcessing(sp)
    sps = uhp.checkForValidatedPageEntry()
    if sps is None:
        return None
    to_return = ScoringPageStatus_pyd.model_validate(sps)
    # _scoring_page_id = sps.scoring_page_id
    return to_return

def setScoringPageTestResult(success:bool, scoring_page_id:int):
    """
    Sets the scoring page status to that indicated in success

    Parameters
    ----------
    success:bool
        The success of the test
    scoring_page_id:int
        Scoring page to update
    """
    with RCSA_DB.getSQLSession() as db:
        sps = db.scalars(select(ScoringPageStatus).where(ScoringPageStatus.scoring_page_id==scoring_page_id)).one()
        sps.tested = success
        db.commit()

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

################ Match and Team Data ###################

from robocompscoutingapp.FirstEventsAPI import FirstEventsAPI, FirstMatch, FirstTeam

def deleteMatchesFromEvent(eventCode:str, delete_only_unscored:bool = False):
    """
    Will delete all matches from the given event

    Parameters
    ----------
    eventCode:str
        The FRC Event Code
    delete_only_unscored:bool
        Will only delete unscored matches for this event.  Intended for possibility an event has its matches re-organized for some reason
    """
    with RCSA_DB.getSQLSession() as db:
        if delete_only_unscored:
            db.execute(delete(MatchesForEvent).filter_by(eventCode=eventCode, scored=False))
        else:
            db.execute(delete(MatchesForEvent).filter_by(eventCode=eventCode))
        db.commit()

    
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
    eventCode:str

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
            teams=teams, 
            eventCode=eventCode
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
            teams=teams,
            eventCode=eventCode
        )

class MatchesAndTeamsLoaded(BaseModel):
    matches_are_loaded:bool
    teams_are_loaded:bool

def isEventAlreadyLoaded(eventCode:str) -> MatchesAndTeamsLoaded:
    """
    Returns the MatchesAndTeamsLoaded with correct boolean values sent

    Parameters
    ----------
    eventCode:str
        The FRC Event code
    
    Returns
    -------
    MatchesAndTeamsLoaded
        Matches and team loaded object
    """
    mat = getMatchesAndTeams(eventCode=eventCode, unscored_only=False)
    toreturn = MatchesAndTeamsLoaded(
        matches_are_loaded = len(mat.matches) > 0,
        teams_are_loaded = len(mat.teams) > 0
    )
    return toreturn

def loadEventData(
        eventCode:str,
        reset_all_data:bool = False,
        refresh_match_data:bool = False,
        season:int = None
    ):
    """
    Will load all matches and teams for the configured event.

    Parameters
    ----------
    eventCode:str
        The FRC Event Code
    reset_all_data:bool
        Will delete and reset all match, team, and scoring data, generally used if you tested on the real match and team data and want to prepare for the actual event.
    refresh_match_data:bool
        Will delete all UNSCORED matches and scoring data.  Used if FRC re-structures the remaining matches in an event.
    season:int
        If provided, will override the default season in the FRC API (used for testing against previous seasons)
    """
    # Set up First API
    config = RCSA_Config.getConfig()
    fapi = FirstEventsAPI(config=config, season=season)
    already_loaded = isEventAlreadyLoaded(eventCode)
    if not (already_loaded.matches_are_loaded and already_loaded.teams_are_loaded):
        # There's no data load all of it
        allTeams = fapi.getTeamsAtEvent(eventCode=eventCode)
        storeTeams(allTeams)
        allMatches = fapi.getMatchesAtEvent(eventCode=eventCode)
        storeMatches(allMatches)
        # Just make sure the scoring data is empty for this event
        deleteScoresFromDB(eventCode)
        return
    
    # If we are here, there is data already
    # Process the remaining flags.  I count on the CLI to ensure mutually exclusive flags are not set
    # In any rate only a single flag will be processed before returning
    if reset_all_data:
        deleteMatchesFromEvent(eventCode)
        deleteScoresFromDB(eventCode)
        allTeams = fapi.getTeamsAtEvent(eventCode=eventCode)
        storeTeams(allTeams)
        allMatches = fapi.getMatchesAtEvent(eventCode=eventCode)
        storeMatches(allMatches)
        return
    
    if refresh_match_data:
        deleteMatchesFromEvent(eventCode=eventCode, delete_only_unscored=True)
        # There may have been new teams added?
        # storeTeams prevents attempts to add same team to same event multiple times
        allTeams = fapi.getTeamsAtEvent(eventCode=eventCode)
        storeTeams(allTeams)
        # storeMatches will prevent overwriting already scored events
        allMatches = fapi.getMatchesAtEvent(eventCode=eventCode)
        storeMatches(allMatches)
        return

################## Scoring Functions #################

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

def deleteScoresFromDB(eventCode:str):
    """
    Delete all scores from the DB for this event and scoring page

    Parameters
    ----------
    eventCode:str
        Event code for the scored event
    scoring_page_id:int
        Scoring page ID
    """
    with RCSA_DB.getSQLSession() as db:
        db.execute(delete(ScoresForEvent).filter_by(eventCode=eventCode))
        db.commit()


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
    scoring_page_id = getCurrentScoringPageData().scoring_page_id
    with RCSA_DB.getSQLSession() as db:
        try:
            to_add = [ScoresForEvent(**a_score.model_dump() | {
                "scoring_page_id":scoring_page_id,
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
            self.count_of_scored_events = db.scalars(select(func.count(distinct(ScoresForEvent.matchNumber))).filter_by(teamNumber=self.teamNumber, eventCode=self.eventCode, scoring_page_id=self.scoring_page_id)).one()
            self.initializeDataStructures()
            all_scores_for_team = db.scalars(select(ScoresForEvent).filter_by(teamNumber=self.teamNumber, eventCode=self.eventCode, scoring_page_id=self.scoring_page_id)).all()
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

class PageIDUsedForEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scoring_page_id:int
    count_of_scores_found:int

def getPageIDsUsedForThisEvent(eventCode:str) -> List[PageIDUsedForEvent]:
    """
    Produces a list of scoring page IDs that have scores for the chosen event

    Parameters
    ----------
    eventCode:str
        The event we are gathering data for
    
    Returns
    -------
    List[PageIDUsedForEvent]
        List of PageIDUsedForEvent objects
    """
    with RCSA_DB.getSQLSession() as db:
        stmt = select(
                ScoresForEvent.scoring_page_id,
                func.count(ScoresForEvent.score_id).label("count_of_scores_found")
            ).group_by("scoring_page_id").order_by(desc("count_of_scores_found")).having(ScoresForEvent.eventCode == eventCode)
        all_ids_used = db.execute(stmt).all()
        to_return = [PageIDUsedForEvent(scoring_page_id=row[0], count_of_scores_found=row[1]) for row in all_ids_used]
        return to_return    

class MigratePageResults(BaseModel):
    success_messages:List[str] = Field(default=[])
    warning_messages:List[str] = Field(default=[])
    error_message:List[str] = Field(default=[])
    

def migrateDataForEventToNewPage(eventCode:str, old_scoring_page_id:int, new_scoring_page_id:int) -> MigratePageResults:
    """
    Attempts to migrate data for an event to a new scoring page ID.  Used if teams change scoring pages in the middle of an event.

    Parameters
    ----------
    eventCode:str
        Event code to try
    old_scoring_page_id:int
        Page migrating from
    new_scoring_page_id:int
        Page migrating to

    Returns
    -------
    MigratePageResults
        Object with messages to pass along
    """
    # NEED TO TRANSFER MODE IDs also
    to_return = MigratePageResults()
    # Get scoring item names from new page number
    new_modes_and_items = getGameModeAndScoringElements(new_scoring_page_id)
    # Get scoring item names from old
    old_modes_and_items = getGameModeAndScoringElements(old_scoring_page_id)
    # diff.  Any in old and not in new will not be moved: generate warning
    # items
    not_migrated_old_names = list(set(old_modes_and_items.scoring_items.keys()) - set((new_modes_and_items.scoring_items.keys())))
    if len(not_migrated_old_names) > 0:
        msg = f"The following item(s) will not be migrated because they are not scored in the new scoring page: {', '.join(not_migrated_old_names)}.  This data will not be visible on the analytics page"
        to_return.warning_messages.append(msg)
    brand_new_names = list(set(new_modes_and_items.scoring_items.keys()) - set((old_modes_and_items.scoring_items.keys())))
    if len(brand_new_names) > 0:
        msg = f"Matches scored before using this page will not have these item(s): {', '.join(brand_new_names)}.  They were not previously logged."
        to_return.warning_messages.append(msg)
    names_to_migrate = list(set(new_modes_and_items.scoring_items.keys()).intersection(set(old_modes_and_items.scoring_items.keys())))
    # Modes
    not_migrated_old_modes = list(set(old_modes_and_items.modes.keys()) - set((new_modes_and_items.modes.keys())))
    if len(not_migrated_old_modes) > 0:
        msg = f"The following modes(s) will not be migrated because they are not used in the new scoring page: {', '.join(not_migrated_old_modes)}.  This data will not be visible on the analytics page"
        to_return.warning_messages.append(msg)
    brand_new_modes = list(set(new_modes_and_items.modes.keys()) - set((old_modes_and_items.modes.keys())))
    if len(brand_new_modes) > 0:
        msg = f"Matches scored before using this page will not have these mode(s): {', '.join(brand_new_modes)}.  They did not previously exist."
        to_return.warning_messages.append(msg)
    modes_to_migrate = list(set(new_modes_and_items.modes.keys()).intersection(set(old_modes_and_items.modes.keys())))
    
    
    with RCSA_DB.getSQLSession() as db:        
        # Iterate over common names
        # Convert old names to scoring_item_ids for SQL
        item_ids = [old_modes_and_items.scoring_items[item_name].scoring_item_id for item_name in names_to_migrate]
        # make dict for lookups for new item ids from old item ids
        new_item_lookup = {
            old_modes_and_items.scoring_items[item_name].scoring_item_id:new_modes_and_items.scoring_items[item_name].scoring_item_id
            for item_name in names_to_migrate
        }
        # Convert old modes to mode_ids for SQL
        mode_ids = [old_modes_and_items.modes[mode_name].mode_id for mode_name in modes_to_migrate]
        # make mode dict lookup old_mode_id:new_mode_id
        new_mode_lookup = {
            old_modes_and_items.modes[mode_name].mode_id:new_modes_and_items.modes[mode_name].mode_id
            for mode_name in modes_to_migrate
        }
        try:
            old_records = db.scalars(
                select(ScoresForEvent).
                where(
                    ScoresForEvent.eventCode == eventCode, 
                    ScoresForEvent.scoring_page_id == old_scoring_page_id,
                    ScoresForEvent.scoring_item_id.in_(item_ids),
                    ScoresForEvent.mode_id.in_(mode_ids)
                )
            ).all()
            for old_rec in old_records:
                new_rec = ScoresForEvent(
                    scoring_page_id = new_scoring_page_id,
                    mode_id = new_mode_lookup[old_rec.mode_id],
                    matchNumber = old_rec.matchNumber,
                    eventCode = eventCode,
                    teamNumber =  old_rec.teamNumber,
                    scoring_item_id = new_item_lookup[old_rec.scoring_item_id],
                    value = old_rec.value
                )
                db.add(new_rec)
            db.commit()
            msg = f"Successfuly migrated {len(old_records)} {', '.join(names_to_migrate)} records for modes {', '.join(modes_to_migrate)} to new scoring page."
            to_return.success_messages.append(msg)
        except Exception as badnews:
            msg = f"Failed to migrate data because {type(badnews).__name__}: {badnews}"
            to_return.error_message.append(msg)

        return to_return
         
    
    



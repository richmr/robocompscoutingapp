from enum import Enum
from fastapi import FastAPI, Query, HTTPException, Response, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from pydantic import BaseModel, Field, field_validator 
import platform
from time import sleep
from typing import Annotated, List
from importlib_resources import files
# import asyncio
import logging
from contextlib import asynccontextmanager, contextmanager

from robocompscoutingapp.GlobalItems import (
    RCSA_Config,
    AutomatedTestMessage
)

from robocompscoutingapp.ScoringData import (
    getCurrentScoringPageData,
    setScoringPageTestResult,
    ScoringPageStatus_pyd
)

# auto_error = False allows no auth requests to go through to next stage
# see source code at https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBasic
security = HTTPBasic(auto_error=False)
# modified from https://fastapi.tiangolo.com/advanced/security/http-basic-auth/
def authorized_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
) -> bool:
    # Do we even want authorization
    app_secrets = RCSA_Config.getConfig().Secrets
    if bool(app_secrets.basic_auth_username) == False:
        # No we don't want to check, so just return
        return True
    
    if credentials is None:
        # Then no credentials were provided so we fail automatically
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Some data there, so lets process
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = app_secrets.basic_auth_username.encode("utf8")
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = app_secrets.basic_auth_password.encode("utf8")
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

_scoring_page_id = None
_eventCode = None

@asynccontextmanager
async def lifespan(app:FastAPI):
    # Set up the static pages
    rcsa_api_app.mount(f"/app", StaticFiles(directory=RCSA_Config.getConfig().ServerConfig.user_static_folder), name="app")
    # establish scoring page ID
    global _scoring_page_id
    global _eventCode
    _scoring_page_id = getCurrentScoringPageData().scoring_page_id
    _eventCode = RCSA_Config.getConfig().FRCEvents.first_event_id
    yield
    

rcsa_api_app = FastAPI(title="RoboCompScoutingApp", 
                       lifespan=lifespan,
                       dependencies=[Depends(authorized_user)]
)

@rcsa_api_app.get("/lifecheck")
def lifecheck():
    return {"alive":True}

@rcsa_api_app.get("/errorcheck")
def errorcheck():
    raise HTTPException(status_code=418, detail="Error check")

########################

from robocompscoutingapp.ScoringData import (
    getGameModeAndScoringElements,
    ModesAndItems
) 

@rcsa_api_app.get("/api/gameModesAndScoringElements")
def gameModeAndScoringElements() -> ModesAndItems:
    return getGameModeAndScoringElements(_scoring_page_id)

########################

from robocompscoutingapp.ScoringData import (
    getMatchesAndTeams,
    getMatches,
    MatchesAndTeams
)


@rcsa_api_app.get("/")
def home():
    """
    Redirect to the main page
    """
    tosend = """
        <!DOCTYPE html>
        <html>
            <head>
                <meta http-equiv="refresh" content="1; url='app/index.html'" />
            </head>
            <body>
                <p>Redirecting to main menu</p>
            </body>
        </html>
    """
    return HTMLResponse(tosend)

@rcsa_api_app.get("/scoring")
def goToScoring():
    """
    Redirect to the chosen scoring page
    """
    tosend = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta http-equiv="refresh" content="1; url='app/{RCSA_Config.getConfig().ServerConfig.scoring_page.name}'" />
            </head>
            <body>
                <p>Redirecting to scoring page</p>
            </body>
        </html>
    """
    return HTMLResponse(tosend)

@rcsa_api_app.get("/api/getMatchesAndTeams")
def matchesAndTeams(unscored_only:bool = True) -> MatchesAndTeams:
    """
    Retrieve all the matches and teams for this event.  By default only returns the remaining unscored matches.
    This is in place to allow for faster match selection during the event.

    Parameters
    ----------
    unscored_only:bool
        Set to False to get ALL matches, regardless if they have been scored already

    Returns
    -------
    MatchesAndTeams
        Filled matches and team JSON object
    """
    try:
        data = getMatchesAndTeams(_eventCode, unscored_only=unscored_only)
        return data
    except Exception as badnews:
        raise HTTPException(status_code=500, detail=f"Unable to get matches and teams because {type(badnews).__name__}: {badnews}")

@rcsa_api_app.get("/api/getMatches")
def justMatches(unscored_only:bool = True) -> MatchesAndTeams:
    """
    Retrieve the matches for this event.  By default only returns the remaining unscored matches.
    This is in place to allow for faster match selection during the event.

    Parameters
    ----------
    unscored_only:bool
        Set to False to get ALL matches, regardless if they have been scored already

    Returns
    -------
    MatchesAndTeams
        Filled matches and team JSON object.  The "teams" element will be an empty dictionary.
    """
    try:
        return getMatches(_eventCode, unscored_only=unscored_only)
    except Exception as badnews:
        raise HTTPException(status_code=500, detail=f"Unable to get matches because {type(badnews).__name__}: {badnews}")

from robocompscoutingapp.ScoringData import (
    addScoresToDB,
    teamAlreadyScoredForThisMatch,
    ScoredMatchForTeam,
)

@rcsa_api_app.post("/api/addScores")
def addScores(team_score_for_match:ScoredMatchForTeam):
    """
    Add recorded scores for a team for a given match.  Will return an error if this team already scored for this match.

    Parameters
    ----------
    team_score_for_match:ScoredMatchForTeam
        Filled out ScoredMatchForTeam object
    """
    # Check to see if already scored
    if teamAlreadyScoredForThisMatch(
        teamNumber=team_score_for_match.teamNumber,
        matchNumber=team_score_for_match.matchNumber,
        eventCode=_eventCode
    ):
        raise HTTPException(status_code=409, detail=f"Match #{team_score_for_match.matchNumber} data for team {team_score_for_match.teamNumber} already submitted for this match")
    
    # Store it
    try:
        addScoresToDB(eventCode=_eventCode, match_score=team_score_for_match)
        return 
    except Exception as badnews:
        raise HTTPException(status_code=500, detail=f"Unable to save score because {type(badnews).__name__}: {badnews}")

from robocompscoutingapp.ScoringData import (
    getAggregrateResultsForAllTeams,
    AllTeamResults,
)

@rcsa_api_app.get("/api/getAllScores")
def getAllScores() -> AllTeamResults:
    """
    Get aggregrate results for this event

    Returns
    -------
    AllTeamResults
        Layered data object with all results for all teams, organized by mode and total
    """
    try:
        return getAggregrateResultsForAllTeams(eventCode=_eventCode, scoring_page_id=_scoring_page_id)
    except Exception as badnews:
        raise HTTPException(status_code=500, detail=f"Unable to get scores {type(badnews).__name__}: {badnews}")
    

@rcsa_api_app.get("/api/currentPageStatus")
def getAllScores() -> ScoringPageStatus_pyd:
    """
    Get scoring page data

    Returns
    -------
    ScoringPageStatus
        SPS for the configured scoring page
    """
    try:
        return getCurrentScoringPageData()
    except Exception as badnews:
        raise HTTPException(status_code=500, detail=f"Unable to get scoring page info because {type(badnews).__name__}: {badnews}") 
      
#####################

class TestMode(BaseModel):
    in_test_mode:bool

@rcsa_api_app.get("/test/checkTestMode")
def checkTestMode() -> TestMode:
    """
    Intended to be checked by the test mode script before executing tests.  Here to prevent contaminating data by accidently running the test sequence on a live server.
    """
    return TestMode(in_test_mode=RCSA_Config.getConfig().ServerConfig.test_mode)

@rcsa_api_app.post("/test/testMessage")
def testMessage(message:AutomatedTestMessage):
    # Only works if in test mode
    if RCSA_Config.getConfig().ServerConfig.test_mode:
        RCSA_Config.storeTestMessage(message)
    return {}

@rcsa_api_app.get("/test/testingComplete")
def testingComplete(success:bool):
    """
    Sets the global testing complete variable.  Intended to allow automated testing to shut down the server when complete

    Parameters
    ----------
    success:bool
        Set to true if the automated testing was a success (warnings count as success); false if otherwise

    """
    # Only works if the server was started in test mode to begin with
    if RCSA_Config.getConfig().ServerConfig.test_mode:
        RCSA_Config.getConfig().ServerConfig.test_success = success
        setScoringPageTestResult(success, _scoring_page_id)
        RCSA_Config.getConfig().ServerConfig.testing_complete = True

    return {}


        


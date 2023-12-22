from fastapi import FastAPI, Query, HTTPException, Response, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from pydantic import BaseModel, Field 
import platform
from time import sleep
from typing import Annotated, List
from importlib_resources import files
# import asyncio
import logging
from contextlib import asynccontextmanager, contextmanager

from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.ScoringData import (
    getCurrentScoringPageID
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
    rcsa_api_app.mount(f"/scoring", StaticFiles(directory=RCSA_Config.getConfig().ServerConfig.user_static_folder), name="scoring")
    # analysis static pages
    analysis_dir = files('robocompscoutingapp.web').joinpath("pages")
    rcsa_api_app.mount(f"/analysis", StaticFiles(directory=analysis_dir), name="analysis")
    # establish scoring page ID
    global _scoring_page_id
    _scoring_page_id = getCurrentScoringPageID()
    _eventCode = RCSA_Config.getConfig().FRCEvents.first_event_id
    yield
    

rcsa_api_app = FastAPI(title="RoboCompScoutingApp", 
                       lifespan=lifespan,
                       dependencies=[Depends(authorized_user)]
)

@rcsa_api_app.get("/lifecheck")
def lifecheck():
    return {"alive":True}

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

@rcsa_api_app.get("/api/getMatchesAndTeams")
def matchesAndTeams() -> MatchesAndTeams:
    return getMatchesAndTeams(_eventCode, unscored_only=True)

@rcsa_api_app.get("/api/getMatches")
def justMatches() -> MatchesAndTeams:
    return getMatches(_eventCode, unscored_only=True)
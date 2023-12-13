from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field 
import platform
from time import sleep
from typing import Annotated, List
from importlib_resources import files
# import asyncio
import logging
from contextlib import asynccontextmanager, contextmanager

from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.ScoringData import getCurrentScoringPageID


_scoring_page_id = None

@asynccontextmanager
async def lifespan(app:FastAPI):
    # Set up the static pages
    rcsa_api_app.mount(f"/scoring", StaticFiles(directory=RCSA_Config.getConfig()["Server_Config"]["user_static_folder"]), name="scoring")
    # analysis static pages
    analysis_dir = files('robocompscoutingapp.web').joinpath("pages")
    rcsa_api_app.mount(f"/analysis", StaticFiles(directory=analysis_dir), name="analysis")
    # establish scoring page ID
    global _scoring_page_id
    _scoring_page_id = getCurrentScoringPageID()
    yield
    

rcsa_api_app = FastAPI(title="RoboCompScoutingApp", lifespan=lifespan)

#lifecycle, get the scoring page ID

@rcsa_api_app.get("/lifecheck")
def lifecheck():
    return {"alive":True}
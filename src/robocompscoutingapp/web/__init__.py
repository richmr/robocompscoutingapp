from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field 
import platform
from time import sleep
from typing import Annotated, List
from importlib import resources
# import asyncio
import logging
from contextlib import asynccontextmanager

rcsa_api_app = FastAPI(title="RoboCompScoutingApp")


@rcsa_api_app.get("/lifecheck")
def lifecheck():
    return {"alive":True}
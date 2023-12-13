from sqlalchemy import select
from pydantic import BaseModel, ConfigDict
from typing import Dict

from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing
from robocompscoutingapp.ORMDefinitionsAndDBAccess import (
    ScoringPageStatus,
    ModesForScoringPage,
    ScoringItemsForScoringPage,
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



"""
Functions to ensure databases are ready to receive scoring information
"""
from pathlib import Path
from pydantic import BaseModel
from sqlalchemy import select

from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing
from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.AppExceptions import IntegrationPageNotValidated
from robocompscoutingapp.ScoringPageParser import ScoringPageParser, ScoringParseResult
from robocompscoutingapp.ORMDefinitionsAndDBAccess import (
    ScoringPageStatus,
    ModesForScoringPage,
    ScoringItemsForScoringPage,
    RCSA_DB
)

class Integrate:

    def __init__(self) -> None:
        self.scoring_page = RCSA_Config.getConfig()["Server_Config"]["scoring_page"]
        pass

    def verifyScoringPageValidated(self) -> ScoringPageStatus:
        """
        Simply verifies the supplied scoring page is validated.  We need the page id to further integrate
        """
        uhp = UserHTMLProcessing(self.scoring_page)
        valid_found = uhp.checkForValidatedPageEntry()
        if valid_found is None:
            raise IntegrationPageNotValidated(f"{self.scoring_page} is not validated")
        return valid_found
    
    def getScoringPageResult(self) -> ScoringParseResult:
        """
        We need the game modes and scoring activities in order to add to the database
        """
        with Path(self.scoring_page).open() as f:
            spp = ScoringPageParser(f)
            spr = spp.parseScoringElement()
            return spr

    def addGameModesToDatabase(self, scoring_page_id:int, game_modes:list) -> dict:
        """
        Stores the discovered game modes in the data base so we have accurate indices

        Parameters
        ----------
        scoring_page_id:int
            The primary key for the designated scoring page

        game_modes:list
            List of the game_modes from a ScoringPageResult

        Returns
        -------
        dict
            Dictionary of the game modes with their primary key in the data base
        """
        game_mode_dict = {}
        with RCSA_DB.getSQLSession() as dbsession:
            for game_mode in game_modes:
                gm = ModesForScoringPage(scoring_page_id=scoring_page_id, mode_name=game_mode)
                dbsession.add(gm)
                dbsession.commit()
                game_mode_dict[game_mode] = gm.mode_id
            
        return game_mode_dict

    def addScoringItemsToDatabase(self, scoring_page_id:int, scoring_items:dict) -> dict:
        """
        Stores the discovered scoring items in the data base so we have accurate IDs

        Parameters
        ----------
        scoring_page_id:int
            The primary key for the designated scoring page

        scoring_items:dict
            Dictionary of the scoring_elements from a ScoringPageResult

        Returns
        -------
        dict
            Dictionary of the scoring items with their primary key in the data base
        """
        to_return = {}
        with RCSA_DB.getSQLSession() as db:
            for index, (key, value) in enumerate(scoring_items.items()):
                if isinstance(value, str):
                    # Prevent issues, single item instead of list as expected
                    si = ScoringItemsForScoringPage(scoring_page_id=scoring_page_id, name=value, type=key)
                    db.add(si)
                    db.commit()
                    to_return[value] = si.scoring_item_id
                elif isinstance(value, list):
                    for an_item in value:
                        si = ScoringItemsForScoringPage(scoring_page_id=scoring_page_id, name=an_item, type=key)
                        db.add(si)
                        db.commit()
                        to_return[an_item] = si.scoring_item_id
                else:
                    raise TypeError(f"I don't know how to handle a {type(value)} object")
        
        return to_return

    def updateToIntegrated(self, scoring_page_id:int):
        """
        Updates the record for this page in the database to indicate it has been successfully integrated

        Parameters
        ----------
        scoring_page_id:int
            The primary key for this page
        """
        with RCSA_DB.getSQLSession() as db:
            this_page = db.scalars(select(ScoringPageStatus).where(ScoringPageStatus.scoring_page_id==scoring_page_id)).one()
            this_page.integrated = True
            db.commit()

    def integrate(self):
        db_result = self.verifyScoringPageValidated()
        scoring_page_id = db_result.scoring_page_id
        # Get the scoring page result
        spr = self.getScoringPageResult()
        # Store items in db
        mode_id_dict = self.addGameModesToDatabase(scoring_page_id, spr.game_modes)
        scoring_item_id_dict = self.addScoringItemsToDatabase(scoring_page_id, spr.scoring_elements)
        # Update the database
        self.updateToIntegrated(scoring_page_id)        
        return (mode_id_dict, scoring_item_id_dict)



        


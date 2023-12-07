"""
Functions to ensure databases are ready to receive scoring information
"""
from pathlib import Path
from pydantic import BaseModel

from robocompscoutingapp.UserHTMLProcessing import UserHTMLProcessing
from robocompscoutingapp.GlobalItems import RCSA_Config
from robocompscoutingapp.AppExceptions import IntegrationPageNotValidated
from robocompscoutingapp.ScoringPageParser import ScoringPageParser, ScoringParseResult
from robocompscoutingapp.ORMDefinitionsAndDBAccess import (
    ScoringPageStatus,
    ModesForScoringPage,
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
                game_mode_dict[game_mode] = gm.mode_id
            dbsession.commit()
        return game_mode_dict

    def addToDatabase(self):
        pass

    def integrate(self):
        db_result = self.verifyScoringPageValidated()
        # Get the scoring page result
        spr = self.getScoringPageResult()
        return



        


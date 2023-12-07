"""
Functions to fully validate, process, and prepare the user's HTML for scoring
"""

from pathlib import Path
from pydantic import BaseModel
import hashlib
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy import select

from robocompscoutingapp.ScoringPageParser import ScoringPageParser, ScoringParseResult
from robocompscoutingapp.MatchAndTeamSelectionParser import MatchAndTeamSelectionParser, MatchAndTeamSelectionParseResult
from robocompscoutingapp.JSScriptParser import JSScriptParser
from robocompscoutingapp.ORMDefinitionsAndDBAccess import ScoringPageStatus, RCSA_DB
from robocompscoutingapp.Initialize import Initialize


class UserHTMLProcessing:

    def __init__(self, path_to_user_file:Path) -> None:
        # Rewrap in Path to catch plain string paths.  Has no affect if its actually a path
        self.html_file = Path(path_to_user_file)
        # Call RCSA_DB to ensure it is ready
        # RCSA_DB()
        # Need a single dbsession to prevent detached records
        self.dbsession = RCSA_DB.getSQLSession()

    def validate(self) -> bool:
        """
        Runs all validations and returns True if the file is ready for further processing
        The various parse results are stored as attributes to the instance for access.

        Returns
        -------
        bool
            Validation was successful
        """
        # Have we already validated this page?
        existing = self.checkForValidatedPageEntry()
        if existing is not None:
            return existing.validated
        
        # Nope, so lets validate
        success = self.validateHTML()
        if success:
            self.createValidatedPageEntry()

        return success
        

    def validateHTML(self) -> bool:
        """
        Performs the validation of HTML elements of user-supplied scoring page.  The results of each parse are
        stored in the indicated instance attributes

        Returns
        -------
        bool
            HTML Validation was successful
        """
        errors = []
        with self.html_file.open() as f:
            self.scoring_parse_result = ScoringPageParser(f).validateScoringElement()
            errors.append(self.scoring_parse_result.hasErrors())

            # Need to reset the file handle between parsing
            f.seek(0)

            self.match_team_element_parse_result = MatchAndTeamSelectionParser(f).validate()
            errors.append(self.match_team_element_parse_result.hasErrors())

            f.seek(0)

            self.js_parse_result = JSScriptParser(f).validate()
            errors.append(self.js_parse_result.hasErrors())

        return not max(errors)  # If any hasErrors is True this will return False as in "not good"
    
    def createValidatedPageEntry(self):
        """
        Adds a validated page entry to the database for tracking
        """
        self.dbsession.add(ScoringPageStatus(scoring_page_hash=self.getFileHash(), validated=True))
        self.dbsession.commit()

    def checkForValidatedPageEntry(self) -> ScoringPageStatus:
        """
        Checks database for this page existing already
        
        Returns
        -------
        ScoringPageStatus
            A valid ORM object
        """
        try:
            # Find the object
            page_result = self.dbsession.execute(select(ScoringPageStatus).filter_by(scoring_page_hash=self.getFileHash())).one()
            # Return the current status
            return page_result              
        except NoResultFound:
            # Needs to be added
            return None

    def getFileHash(self) -> str:
        """
        Returns the SHA256 hash of the file
        """
        with self.html_file.open(mode="rb") as f:
            digest = hashlib.file_digest(f, "sha256")
            return digest.hexdigest()


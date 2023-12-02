"""
Functions to fully validate, process, and prepare the user's HTML for scoring
"""

from pathlib import Path
from pydantic import BaseModel

from robocompscoutingapp.ScoringPageParser import ScoringPageParser, ScoringParseResult
from robocompscoutingapp.MatchAndTeamSelectionParser import MatchAndTeamSelectionParser, MatchAndTeamSelectionParseResult
from robocompscoutingapp.JSScriptParser import JSScriptParser


class UserHTMLProcessing:

    def __init__(self, path_to_user_file:Path) -> None:
        self.html_file = path_to_user_file

    def validate(self) -> bool:
        """
        Runs all validations and returns True if the file is ready for further processing
        The various parse results are stored as attributes to the instance for access.

        Returns
        -------
        bool
            Validation was successful
        """
        errors = self.validateHTML()
        return errors
        

    def validateHTML(self) -> bool:
        """
        Performs the validation of HTML elements of user-supplied scoring page.  The results of each parse are
        stored in the indicated instance attributes

        Returns
        -------
        bool
            HTML Validaton was successful
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
    
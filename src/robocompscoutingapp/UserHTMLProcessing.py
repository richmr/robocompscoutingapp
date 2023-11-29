"""
Functions to fully validate, process, and prepare the user's HTML for scoring
"""

from pathlib import Path
from pydantic import BaseModel

from robocompscoutingapp.ScoringPageParser import ScoringPageParser, ScoringParseResult
from robocompscoutingapp.MatchAndTeamSelectionParser import MatchAndTeamSelectionParser, MatchAndTeamSelectionParseResult



class UserHTMLProcessing:

    def __init__(self, path_to_user_file:Path) -> None:
        self.html_file = path_to_user_file

    def validate(self) -> bool:
        """
        Runs all validations and returns True if the file is ready for further processing
        The various parse results are stored as attributes to the instance for access.
        """
        errors = False
        self.scoring_parse_result = ScoringPageParser(self.html_file).validateScoringElement()
        errors = errors or self.scoring_parse_result.hasErrors()

        self.match_team_element_parse_result = MatchAndTeamSelectionParser(self.html_file).validate()
        errors = errors or self.match_team_element_parse_result.hasErrors()

        return errors



from bs4 import BeautifulSoup
from typing import List

from robocompscoutingapp.AppExceptions import ScoringPageParseError, ScoringPageParseWarning

class ScoringPageParser:

    def __init__(self, input_html) -> None:
        self.soup = BeautifulSoup(input_html, features="html.parser")

    def scoringDivPresent(self) -> bool:
        """
        Returns true if the div is present, raise exception if not
        """
        selection = self.soup.select(".scoring")
        if len(selection) != 1:
            raise ScoringPageParseError("No element with 'scoring' class present")
        return True

    def gameModeGroupPresent(self) -> bool:
        """
        Returns true if the div is present, raise exception if not
        """
        selection = self.soup.select(".game_mode_group")
        if len(selection) == 0:
            raise ScoringPageParseWarning("No element with 'game_mode_group' class present.  Its not mandatory but its a good idea to keep your game_mode selectors in one area of UI")
        elif len(selection) > 1:
            raise ScoringPageParseError("Multiple elements with 'game_mode_group' class.  There should be a max of one")
        return True
    
    def collectGameModes(self) -> List:
        """
        Returns list of discovered game modes
        """
        selection = self.soup.select(".game_mode")
        game_modes = []
        for gm in selection:
            try:
                mode_name = gm["data-modename"]
            except KeyError:
                raise ScoringPageParseError(f"This line: {gm} does not declare the mode name in 'data-modename' attribute.")
            
            if mode_name in game_modes:
                raise ScoringPageParseError(f"Game mode {mode_name} has been used more than once.  Mode names must be unique")
        



        
    
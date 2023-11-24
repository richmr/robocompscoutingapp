from bs4 import BeautifulSoup
from typing import List, Dict
import warnings

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
            warnings.warn("No element with 'game_mode_group' class present.  Its not mandatory but its a good idea to keep your game_mode selectors in one area of UI", ScoringPageParseWarning)
            return False
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
                raise ScoringPageParseError(f"This line: '{gm}' does not declare the mode name in 'data-modename' attribute.")
            
            if mode_name in game_modes:
                raise ScoringPageParseError(f"Game mode {mode_name} has been used more than once.  Mode names must be unique")
            
            game_modes.append(mode_name)

        if len(game_modes) == 0:
            warnings.warn(f"No elements with 'game_mode' class detected.  Please see the template file for examples if your competition has multiple phases", ScoringPageParseWarning)
        
        return game_modes
    
    def collectScoringItems(self) -> Dict:
        """
        Returns dictionary of named scoring activities, organized by score type
        """
        # Add possible scoring types here
        scoring_class_markers = ["score_tally", "score_flag"]

        scoring_dict = {key:[] for key in scoring_class_markers}
        found_score_names = []

        # Collect game modes in case a "data-onlyForMode" is applied
        game_modes = self.collectGameModes()

        for score_class in scoring_class_markers:
            selection = self.soup.select(f".{score_class}")
            for element in selection:
                try:
                    activity_name = element["data-scorename"]
                    if activity_name in found_score_names:
                        raise ScoringPageParseError(f"Duplicate scoring activity {activity_name} found.  Please use unique names for all scoring activities.")
                    try:
                        only_mode = element["data-onlyformode"]
                        if only_mode not in game_modes:
                            raise ScoringPageParseError(f"This element {element} declares it is only for mode {only_mode} however that mode is not defined as a an available mode.  The only available modes detected are {game_modes}")
                    except KeyError:
                        # Its okay if this attr is not set, and other exceptions need to be passed
                        pass

                    found_score_names.append(activity_name)
                    scoring_dict[score_class].append(activity_name)
                except KeyError:
                    raise ScoringPageParseError(f"This element {element} does not define the scoring activity name id 'data-scorename' attribute")

        if len(found_score_names) == 0:
            raise ScoringPageParseError("No scoring activities found in markup.  Please see template for guidance.")
                
        return scoring_dict



        
    
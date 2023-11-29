from bs4 import BeautifulSoup
from typing import List, Dict
import warnings
from pydantic import Field
from typing_extensions import Annotated

from robocompscoutingapp.AppExceptions import ScoringPageParseError, ScoringPageParseWarning
from robocompscoutingapp.BaseParsingModel import BaseParsingModel, ParsingFunctionToCall
from robocompscoutingapp.GlobalItems import ScoringClassTypes
from robocompscoutingapp.GlobalItems import FancyText as ft

class ScoringParseResult(BaseParsingModel):
    game_modes: Annotated[List, Field(default=[], description="List of game modes defined in the scoring element markup")]
    scoring_elements: Annotated[Dict, Field(default={}, description="Discovered scoring activities")]   


class ScoringPageParser:

    def __init__(self, input_html_or_file_handle) -> None:
        self.soup = BeautifulSoup(input_html_or_file_handle, features="html.parser")

    def scoringDivPresent(self) -> bool:
        """
        Returns true if the div is present, raise exception if not
        If the element is found, resets the soup so we only look for scoring tags in the scoring div
        If the element is NOT found, will reset the soup to an empty file to prevent attempting to execute
        soup functions on None.  BUT all further tests will fail.
        """
        # Reset the soup to just this div
        scoring_div = self.soup.find_all("div", {"class":"scoring"})
        if len(scoring_div) == 0:
            # First reset the soup
            self.soup = BeautifulSoup("", features="html.parser")
            raise ScoringPageParseError("No element with 'scoring' class present. All further parse tests will be invalid until this is fixed.")
        if len(scoring_div) > 1:
            # First reset the soup
            self.soup = BeautifulSoup("", features="html.parser")
            raise ScoringPageParseError("Multiple divs with scoring class. Only one is permitted.")
        # Reset the soup to just this div
        self.soup = scoring_div[0]
        return True

    def gameModeGroupPresent(self) -> bool:
        """
        Returns true if the div is present, raise exception if not
        """
        selection = self.soup.select(".game_mode_group")
        if len(selection) == 0:
            warnings.warn(ScoringPageParseWarning("No element with 'game_mode_group' class present.  It's not mandatory but it's a good idea to keep your game_mode selectors in one area of UI"))
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
            warnings.warn(ScoringPageParseWarning(f"No elements with 'game_mode' class detected.  Please see the template file for examples if your competition has multiple phases"))
        
        return game_modes
    
    def collectScoringItems(self) -> Dict:
        """
        Returns dictionary of named scoring activities, organized by score type
        """
        
        scoring_class_markers = ScoringClassTypes.list()

        scoring_dict = {key:[] for key in scoring_class_markers}
        found_score_names = []

        # Collect game modes in case a "data-onlyForMode" is applied
        # Suppress the warning from game_modes though, as already caught under normal parsing activity
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
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
                            raise ScoringPageParseError(f"This element {element} declares it is only for mode {only_mode} however that mode is not defined as an available mode.  The only available modes detected are {game_modes}")
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
    
    def checkForReportSubmit(self) -> bool:
        selection = self.soup.select(".report_submit")
        if len(selection) == 0:
            raise ScoringPageParseError("No report_submit element found.  This is required. It's usually a button at the bottom of the scoring element.")
            return False
        elif len(selection) > 1:
            warnings.warn(ScoringPageParseWarning("Multiple elements with 'report_submit' class found.  That's ok, but did you mean it?"))
        return True
    
    def parseScoringElement(self) -> ScoringParseResult:
        errors = []
        spr = ScoringParseResult()
        with warnings.catch_warnings(record=True) as caught_warnings:
            parsers = [
                ParsingFunctionToCall(method_to_call=self.scoringDivPresent),
                ParsingFunctionToCall(method_to_call=self.gameModeGroupPresent),
                ParsingFunctionToCall(method_to_call=self.collectGameModes, field_to_store_result="game_modes"),
                ParsingFunctionToCall(method_to_call=self.collectScoringItems, field_to_store_result="scoring_elements"),
                ParsingFunctionToCall(method_to_call=self.checkForReportSubmit)
            ]
            for a_parser in parsers:
                try:
                    a_parser.runParse(spr)
                except Exception as badnews:
                    errors.append(str(badnews))
        
        # Convert to simple strings which is what I need for this application
        spr.warnings = [str(cw.message) for cw in caught_warnings]
        spr.errors = errors
        return spr
            
    

    def validateScoringElement(self) -> ScoringParseResult:
        """
        This is the "user readable output" part of parsing a scoring element
        It parses the element and returns the SPR if valid after printing a success message
        If the element has errors, prints them and raises the ScoringParseError exception, which is intended to be caught by the CLI tool
        If has only warnings, prints them but still returns the ScoringParseResults
        """
        spr = self.parseScoringElement()
        for err in spr.errors:
            ft.error(err)
        for wrn in spr.warnings:
            ft.warning(wrn)
        
        
        if spr.hasErrors():
            # Don't say anything here, caught at higher level
            pass
        elif spr.hasWarnings():
            ft.success("Scoring element passed validaton, but please read through warnings to make sure you didn't miss anything important to you!")
        else:
            ft.success("Scoring element passed validation!")
        
        return spr



        
    
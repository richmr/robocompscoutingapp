from bs4 import BeautifulSoup
from typing import List, Dict
import warnings
from pydantic import Field
from typing_extensions import Annotated

from robocompscoutingapp.AppExceptions import MatchAndTeamSelectionParseError, MatchAndTeamSelectionParseWarning
from robocompscoutingapp.BaseParsingModel import BaseParsingModel, ParsingFunctionToCall
from robocompscoutingapp.GlobalItems import FancyText as ft

class MatchAndTeamSelectionParseResult(BaseParsingModel):
    pass

class MatchAndTeamSelectionParser:

    def __init__(self, input_html_or_file_handle) -> None:
        self.soup = BeautifulSoup(input_html_or_file_handle, features="html.parser")

    def matchDivPresent(self) -> bool:
        """
        Returns true if the div is present, raise exception if not
        If the element is found, resets the soup so we only look for scoring tags in the scoring div
        If the element is NOT found, will reset the soup to an empty file to prevent attempting to execute
        soup functions on None.  BUT all further tests will fail.
        """
        # Reset the soup to just this div
        target_div = self.soup.find_all("div", {"class":"match_and_team_selection"})
        if len(target_div) == 0:
            # First reset the soup
            self.soup = BeautifulSoup("", features="html.parser")
            raise MatchAndTeamSelectionParseError("No element with 'match_and_team_selection' class present. All further parse tests will be invalid until this is fixed.")
        if len(target_div) > 1:
            # First reset the soup
            self.soup = BeautifulSoup("", features="html.parser")
            raise MatchAndTeamSelectionParseError("Multiple divs with match_and_team_selection class. Only one is permitted.")
        # Reset the soup to just this div
        self.soup = target_div[0]
        return True
    
    def matchSelectorParse(self) -> bool:
        """
        Returns true if the match_selector div is present
        """
        target_div = self.soup.find_all("select", {"class":"match_selector"})
        if len(target_div) == 0:
            raise MatchAndTeamSelectionParseError("No selection element with 'match_selector' class present.")
        if len(target_div) > 1:
            raise MatchAndTeamSelectionParseError("Multiple selection elements with 'match_selector' class. Only one is permitted.")
        return True
    
    def teamSelectorParse(self) -> bool:
        """
        Returns true if the match_selector div is present
        """
        target_div = self.soup.find_all("select", {"class":"team_selector"})
        if len(target_div) == 0:
            raise MatchAndTeamSelectionParseError("No selection element with 'team_selector' class present.")
        if len(target_div) > 1:
            raise MatchAndTeamSelectionParseError("Multiple selection elements with 'team_selector' class. Only one is permitted.")
        return True
    
    def beginScoringButtonParse(self) -> bool:
        """
        Returns true if the begin_scoring button is present
        """
        target_div = self.soup.find_all("button", {"class":"begin_scoring"})
        if len(target_div) == 0:
            raise MatchAndTeamSelectionParseError("No button element with 'begin_scoring' class present.  This should be present after the match and team selection")
        if len(target_div) > 1:
            raise MatchAndTeamSelectionParseWarning("Multiple button elements with 'begin_scoring' class. This is ok, but did you want this?")
        return True
    
    def parseElement(self) -> MatchAndTeamSelectionParseResult:
        errors = []
        pr = MatchAndTeamSelectionParseResult()
        with warnings.catch_warnings(record=True) as caught_warnings:
            parsers = [
                ParsingFunctionToCall(method_to_call=self.matchDivPresent),
                ParsingFunctionToCall(method_to_call=self.matchSelectorParse),
                ParsingFunctionToCall(method_to_call=self.teamSelectorParse),
                # ParsingFunctionToCall(method_to_call=self.beginScoringButtonParse)
            ]
            for a_parser in parsers:
                try:
                    a_parser.runParse(pr)
                except Exception as badnews:
                    errors.append(str(badnews))
        
        # Convert to simple strings which is what I need for this application
        pr.warnings = [str(cw.message) for cw in caught_warnings]
        pr.errors = errors
        return pr
    
    def validate(self) -> MatchAndTeamSelectionParseResult:
        result = self.parseElement()
        for err in result.errors:
            ft.error(err)
        for wrn in result.warnings:
            ft.warning(wrn)

        if result.hasErrors():
            # Don't say anything here, caught at higher level
            pass
        elif result.hasWarnings():
            ft.success("Match selection element passed validaton, but please read through warnings to make sure you didn't miss anything important to you!")
        else:
            ft.success("Match selection element passed validation!")

        return result
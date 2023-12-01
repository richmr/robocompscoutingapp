from bs4 import BeautifulSoup
from typing import List, Dict
import warnings
from pydantic import Field
from typing_extensions import Annotated

from robocompscoutingapp.AppExceptions import JavaScriptParseError, JavaScriptParseWarning
from robocompscoutingapp.BaseParsingModel import BaseParsingModel, ParsingFunctionToCall
from robocompscoutingapp.GlobalItems import rcsa_js_loader
from robocompscoutingapp.GlobalItems import FancyText as ft

class JSParseResult(BaseParsingModel):
    pass

class JSScriptParser:
    """
    Checks the user-supplied HTML to make sure the required javascript tags are there
    """

    def __init__(self, input_html_or_file_handle) -> None:
        self.soup = BeautifulSoup(input_html_or_file_handle, features="html.parser")

    def jSScriptPresent(self) -> bool:
        """
        Returns True if the required JS script tags are present
        """ 
        scripts = self.soup.find_all("script", {"src":rcsa_js_loader})
        if len(scripts) == 0:
            raise JavaScriptParseError(f"There must be a script tag like <script src='{rcsa_js_loader}'></script> for the scoring mechanics to work.  Please add this to the end of the <body> element.")
        if len(scripts) > 1:
            raise JavaScriptParseError(f"Multiple loader script tags found.  Please only have one of: <script src='{rcsa_js_loader}'></script>")
        return True
    
    def parseElement(self) -> JSParseResult:
        errors = []
        pr = JSParseResult()
        with warnings.catch_warnings(record=True) as caught_warnings:
            parsers = [
                ParsingFunctionToCall(method_to_call=self.jSScriptPresent),
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
    
    def validate(self) -> JSParseResult:
        result = self.parseElement()
        for err in result.errors:
            ft.error(err)
        for wrn in result.warnings:
            ft.warning(wrn)

        if result.hasErrors():
            # Don't say anything here, caught at higher level
            pass
        elif result.hasWarnings():
            ft.success("Required Javascript tags are present, but please read through warnings to make sure you didn't miss anything important to you!")
        else:
            ft.success("Required Javascript tags are present!")

        return result




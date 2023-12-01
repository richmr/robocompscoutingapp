"""
Custom Exceptions used in the app
"""

class RCSAWarning(Warning):
    """
    Subclass of Warnings to meet needs for this app
    """

    def __str__(self) -> str:
        """
        We just want the warning message here
        """
        return self.args[0]

####### Scoring Parse ########

class ScoringPageParseError(Exception):
    "Raised when the user-supplied scoring page has issues that will break processing"
    pass

class ScoringPageParseWarning(RCSAWarning):
    "Used when the user-supplied scoring page has issues that deviate from norm but won't break processing"
    pass

####### Match and Team Selection Parse ########

class MatchAndTeamSelectionParseError(Exception):
    pass

class MatchAndTeamSelectionParseWarning(RCSAWarning):
    pass

##### JavaScript Parsing #############

class JavaScriptParseError(Exception):
    pass

class JavaScriptParseWarning(RCSAWarning):
    pass

"""
Custom Exceptions used in the app
"""

class ScoringPageParseError(Exception):
    "Raised when the user-supplied scoring page has issues that will break processing"
    pass

class ScoringPageParseWarning(Warning):
    "Used when the user-supplied scoring page has issues that deviate from norm but won't break processing"
    
    def __str__(self) -> str:
        """
        We just want the warning message here
        """
        return self.args[0]
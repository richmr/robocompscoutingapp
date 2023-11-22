"""
Custom Exceptions used in the app
"""

class ScoringPageParseError(Exception):
    "Raised when the user-supplied scoring page has issues that will break processing"
    pass

class ScoringPageParseWarning(Exception):
    "Raised when the user-supplied scoring page has issues that deviate from norm but won't break processing"
    pass
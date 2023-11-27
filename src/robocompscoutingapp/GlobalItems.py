"""
Collection of configuration items that are used across many parts of application
"""
#from rich import print
from enum import Enum
import rich

class ExtendedEnum(Enum):
    """
    Taken from: https://stackoverflow.com/questions/29503339/how-to-get-all-values-from-python-enum-class
    """
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

class ScoringClassTypes(ExtendedEnum):
    """
    Add possible scoring types here
    The value is the class name the parser will look for and also use to set up scoring logic
    You'll also need to add logic to the API end to understand and handle these scoring types
    """
    score_tally = "score_tally"     # Scoring events that additively increase per event (i.e. balls in a goal)
    score_flag = "score_flag"       # Scoring events that are True/False (i.e. it happened or didn't)

# 'Rich' text 
class FancyText:
    err = "[bold red]\[!]"
    wrn = "[yellow]\[w]"

    @classmethod
    def error(cls, message):
        rich.print(f"{cls.err} {message}")

    @classmethod
    def warning(cls, message):
        rich.print(f"{cls.wrn} {message}")

    @classmethod
    def success(cls, message):
        rich.print(f"[green]\[+] {message}[/green]")

    @classmethod
    def print(cls, message):
        # Pass through to rich.print to prevent needing to import if a specific message has specfic needs.
        rich.print(cls, message) 

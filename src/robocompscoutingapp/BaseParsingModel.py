"""
Base parsing model to return results from parsing user markup input
"""

from pydantic import BaseModel, Field 
from typing_extensions import Annotated
from typing import List, Callable, Any, AnyStr

class BaseParsingModel(BaseModel):
    errors: Annotated[List, Field(default=[], description="List of received error messages")]
    warnings: Annotated[List, Field(default=[], description="List of received warning messages")]

    def hasErrors(self) -> bool:
        """
        Returns true if there were errors in the parsing
        """
        return len(self.errors) > 0
    
    def hasWarnings(self):
        """
        Returs true if there were warning in the parsing
        """
        return len(self.warnings) > 0
    
class ParsingFunctionToCall(BaseModel):
    method_to_call: Annotated[Callable, Field(description="The method that will called for next parsing function")]
    field_to_store_result: Annotated[AnyStr, Field(default=None, description="String that described where to store the parse result in the target object")]

    def runParse(self, destination_object: Any):
        """
        Will run this parse, and store the result in the destination object (per the field_to_store_result field)

        Parameter
        ---------
        destination_object: any
            The object to store results in.  Will override any value already in the field_to_store_result
        """
        result = self.method_to_call()
        if self.field_to_store_result is not None:
            setattr(destination_object, self.field_to_store_result, result)

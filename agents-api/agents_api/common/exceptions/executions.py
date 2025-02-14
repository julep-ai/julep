from simpleeval import NameNotDefined
from thefuzz import fuzz


class EvaluateError(Exception):
    def __init__(self, error, expression, values):
        error_message = error.message if hasattr(error, "message") else str(error)
        message = error_message

        # Catch a possible jinja template error
        if "unhashable" in error_message and "{{" in expression:
            message += "\nSuggestion: It seems like you used a jinja template, did you mean to use a python expression?"

        # Catch a possible misspell in a variable name
        if isinstance(error, NameNotDefined):
            misspelledName = error_message.split("'")[1]
            for variableName in values:
                if fuzz.ratio(variableName, misspelledName) >= 90.0:
                    message += f"\nDid you mean '{variableName}' instead of '{misspelledName}'?"
        super().__init__(message)

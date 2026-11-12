"""Errors raised by the evaluation engine.

The engine knows nothing about HTTP; status_code is a hint for the API adapter.
"""


class EvaluationError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code

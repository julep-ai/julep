class BaseException(Exception):
    pass


class InvalidPromptException(BaseException):
    def __init__(self, msg: str):
        super().__init__(f"Invalid prompt format: {msg}")


class InvalidFunctionName(BaseException):
    def __init__(self, msg: str):
        super().__init__(f"Invalid function name: {msg}")

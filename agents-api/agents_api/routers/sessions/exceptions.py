class BaseSessionException(Exception):
    pass


class InputTooBigError(BaseSessionException):
    def __init__(self, actual_tokens, required_tokens):
        super().__init__(
            f"input is too big, {required_tokens} tokens required, but you got {actual_tokens} tokens"
        )

class BaseSessionException(Exception):
    pass


class InputTooBigError(BaseSessionException):
    def __init__(self, actual_tokens, required_tokens):
        super().__init__(
            f"Input is too big, {actual_tokens} tokens provided, but only {required_tokens} tokens are allowed."
        )

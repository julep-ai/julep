class AgentsBaseException(Exception):
    pass


class ModelNotSupportedError(AgentsBaseException):
    def __init__(self, model_name):
        super().__init__(f"model {model_name} is not supported")


class PromptTooBigError(AgentsBaseException):
    def __init__(self, token_count, max_tokens):
        super().__init__(
            f"prompt is too big, {token_count} tokens provided, exceeds maximum of {max_tokens}"
        )


class UnknownTokenizerError(AgentsBaseException):
    def __init__(self):
        super().__init__("unknown tokenizer")

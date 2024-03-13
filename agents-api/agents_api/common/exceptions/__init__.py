class BaseCommonException(Exception):
    def __init__(self, msg: str, http_code: int):
        super().__init__(msg)
        self.http_code = http_code

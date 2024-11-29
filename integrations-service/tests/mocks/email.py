"""Mock implementation of email client"""


class MockEmailClient:
    def __init__(self, host: str, port: int, user: str, password: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    def send(self, to: str, from_: str, subject: str, body: str) -> bool:
        """Mock email sending that always succeeds"""
        return True


class MockEmailException(Exception):
    """Mock exception for email errors"""

    pass

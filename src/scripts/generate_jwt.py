from datetime import UTC, datetime, timedelta

import jwt

dev_secret = ""
prod_secret = ""
test_secret = "your-supersupersecret-jwt-token-with-at-least-32-characters-long"
encoded_jwt = jwt.encode(
    {
        "sub": "097720c5-ab84-438c-b8b0-68e0eabd31ff",
        "email": "e@mail.com",
        "iat": datetime.now(UTC),  # Specify timezone
        "exp": datetime.now(UTC) + timedelta(days=100),  # Specify timezone
    },
    test_secret,
    algorithm="HS512",
)
print(encoded_jwt)

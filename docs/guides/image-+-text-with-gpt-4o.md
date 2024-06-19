# Image + Text with GPT-4o

Julep supports using GPT-4o (or GPT-4-Vision) for image input.

## Setting Up an Agent and Session

Initialize the Julep Client and create an Agent with `gpt-4o`.

```python
from julep import Client
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.environ["JULEP_API_KEY"]
base_url = os.environ["JULEP_API_URL"]

client = Client(api_key=api_key, base_url=base_url)

agent = client.agents.create(
    name="XKCD Explainer",
    about="An XKCD Comic Explainer",
    model="gpt-4o",
    metadata={"name": "XKCD Explainer"},
)
session = client.sessions.create(
    agent_id=agent.id,
    situation="Your purpose in life is to explain XKCD Comics to n00bs",
    metadata={"agent": "XKCD Explainer"},
)
```

## Sending an image

> Make sure to follow the changed `content` object spec for sending in images.

### Image as a URL

```python
res = client.sessions.chat(
    session_id=session.id,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://imgs.xkcd.com/comics/earth_like_exoplanet.png"
                    },
                }
            ],
        }
    ],
    max_tokens=1024,
)
print(res.response[0][0].content)
```

### Image as a file (base64 encoded)

```python
IMAGE_PATH = "images/xkcd_little_bobby_tables.png"
def encode_image(image_path: str):
    # check if the image exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

base64_image = encode_image(IMAGE_PATH)


res = client.sessions.chat(
    session_id=session.id,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    },
                }
            ],
        }
    ],
    max_tokens=1024,
)
print(res.response[0][0].content)
```

\

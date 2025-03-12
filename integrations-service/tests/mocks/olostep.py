from typing import Dict, Any

def mock_olostep_response() -> Dict[str, Any]:
    return {
        "id": "mock_scrape_id",
        "object": "scrape",
        "created": 1738850463,
        "url_to_scrape": "https://julep.ai",
        "result": {
            "markdown_content": "Example content",
            "html_content": "<p>Example content</p>"
        }
    }
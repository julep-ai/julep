from beartype import beartype
from tenacity import retry, stop_after_attempt, wait_exponential
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional

from ...autogen.Tools import OlostepScrapeArguments, OlostepSetup
from ...env import olostep_api_key  # Import env var like Spider does
from ...models import OlostepOutput, OlostepResponse

async def get_olostep_client(api_key: str):
    """Create aiohttp session with proper headers"""
    return aiohttp.ClientSession(
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )

def get_api_key(setup: OlostepSetup) -> str:
    """Helper function to get API key"""
    return setup.olostep_api_key if setup.olostep_api_key != "DEMO_API_KEY" else olostep_api_key

def create_olostep_response(result: Dict) -> List[OlostepResponse]:
    """Convert API response to our format"""
    return [OlostepResponse(
        url=result.get("url_to_scrape"),
        content=result.get("result", {}).get("markdown_content", ""),
        error=result.get("error"),
        status="success" if result.get("result") else "error"
    )]

@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def scrape(setup: OlostepSetup, arguments: OlostepScrapeArguments) -> OlostepOutput:
    """
    Scrape website content using Olostep API
    """
    assert isinstance(setup, OlostepSetup), "Invalid setup"
    assert isinstance(arguments, OlostepScrapeArguments), "Invalid arguments"

    api_key = get_api_key(setup)
    final_result = []

    try:
        async with get_olostep_client(api_key) as client:
            payload = {
                "url_to_scrape": arguments.url,
                "formats": arguments.params.get("formats", ["markdown"]),
                "transformer": arguments.params.get("transformer", "postlight"),
                "remove_css_selectors": arguments.params.get("remove_css_selectors", "default"),
                "screen_size": arguments.params.get("screen_size", {"screen_type": "desktop"}),
                "actions": arguments.params.get("actions", [])
            }

            # Add optional parameters if provided
            for key in ["wait_before_scraping", "country", "remove_images", 
                       "remove_class_names", "links_on_page"]:
                if value := arguments.params.get(key):
                    payload[key] = value

            async with client.post("https://api.olostep.com/v1/scrapes", json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                final_result = create_olostep_response(result)

    except Exception as e:
        # Log the exception or handle it as needed
        msg = f"Error executing Olostep scrape: {str(e)}"
        raise RuntimeError(msg)

    return OlostepOutput(result=final_result)
import json

from algoliasearch.search.client import SearchClient
from beartype import beartype
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import AlgoliaSearchArguments, AlgoliaSetup
from ...env import algolia_api_key, algolia_application_id
from ...models import AlgoliaSearchOutput


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def search(setup: AlgoliaSetup, arguments: AlgoliaSearchArguments) -> AlgoliaSearchOutput:
    """
    Searches for content in an Algolia index asynchronously.
    """

    # Use walrus operator to simplify assignment and condition
    if (api_key := setup.algolia_api_key) == "DEMO_API_KEY":
        api_key = algolia_api_key
    if (application_id := setup.algolia_application_id) == "DEMO_APPLICATION_ID":
        application_id = algolia_application_id

    # Build the search request
    search_request = {
        "requests": [
            {
                "indexName": arguments.index_name,
                "query": arguments.query,
                "hitsPerPage": arguments.hits_per_page or 20,
                **(arguments.attributes_to_retrieve or {}),
            }
        ]
    }

    # Initialize the Algolia client
    async with SearchClient(application_id, api_key) as client:
        result = json.loads((await client.search(search_request)).to_json())

        # Direct array access instead of get() for known structure
        first_result = result["results"][0]

        # Build metadata dict in one go
        metadata = {
            "nbHits": first_result["nbHits"],
            "page": first_result["page"],
            "nbPages": first_result["nbPages"],
            "processingTimeMS": first_result["processingTimeMS"],
            "query": arguments.query,
        }

        # Avoid redundant print statements in production code
        return AlgoliaSearchOutput(hits=first_result["hits"], metadata=metadata)

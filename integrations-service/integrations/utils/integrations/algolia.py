import json

from algoliasearch.search.client import SearchClient
from beartype import beartype
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import AlgoliaSearchArguments, AlgoliaSetup
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

    api_key = setup.algolia_api_key
    application_id = setup.algolia_application_id

    # Build the search request
    search_params = {
        "indexName": arguments.index_name,
        "query": arguments.query,
        "hitsPerPage": arguments.hits_per_page,
    }

    # Add attributes to retrieve if provided
    if arguments.attributes_to_retrieve is not None:
        search_params["attributesToRetrieve"] = arguments.attributes_to_retrieve

    # Finalize the search request
    search_request = {"requests": [search_params]}

    # Initialize the Algolia client
    async with SearchClient(application_id, api_key) as client:
        result = json.loads((await client.search(search_request)).to_json())

    # Extract results safely and get the first result if available
    results = result.get("results", [])
    first_result = results[0] if results else {}

    # Extract hits directly from first_result
    hits = first_result.get("hits", [])

    # Build metadata dict with all relevant information
    metadata = {
        "query": arguments.query,
        "nbHits": first_result.get("nbHits", 0),
        "page": first_result.get("page", 0),
        "nbPages": first_result.get("nbPages", 0),
        "processingTimeMS": first_result.get("processingTimeMS", 0),
    }

    # Return with appropriate hits based on whether results were found
    return AlgoliaSearchOutput(
        hits=hits,
        metadata=metadata,
    )

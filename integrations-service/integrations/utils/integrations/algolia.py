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

    # Extract the parameters
    index_name = arguments.index_name
    query = arguments.query
    hits_per_page = arguments.hits_per_page or 20

    # Initialize the Algolia client
    async with SearchClient(application_id, api_key) as client:
        result = await client.search({
            "requests": [
                {
                    "indexName": index_name,
                    "query": query,
                    "hitsPerPage": hits_per_page,
                }
            ]
        })

        # Extract the results from the first query
        result = result.to_json()

        # Extract relevant information
        hits = result.get("hits", [])
        metadata = {
            "nbHits": result.get("nbHits", 0),
            "page": result.get("page", 0),
            "nbPages": result.get("nbPages", 0),
            "processingTimeMS": result.get("processingTimeMS", 0),
            "query": query,
        }

        return AlgoliaSearchOutput(hits=hits, metadata=metadata)

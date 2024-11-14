from beartype import beartype
from langchain_community.document_loaders import WikipediaLoader
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import WikipediaSearchArguments
from ...models import WikipediaSearchOutput
from ...models.execution import ExecutionError


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def search(
    arguments: WikipediaSearchArguments,
) -> WikipediaSearchOutput | ExecutionError:
    """
    Searches Wikipedia for a given query and returns formatted results.
    """
    try:
        query = arguments.query
        if not query:
            raise ValueError("Query parameter is required for Wikipedia search")

        load_max_docs = arguments.load_max_docs

        loader = WikipediaLoader(query=query, load_max_docs=load_max_docs)
        documents = loader.load()

        return WikipediaSearchOutput(documents=documents)
    except Exception as e:
        return ExecutionError(error=str(e))

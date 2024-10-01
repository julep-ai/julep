from langchain_community.document_loaders import BrowserbaseLoader

from ...models import BrowserBaseLoadArguments, BrowserBaseLoadOutput, BrowserBaseSetup


async def load(
    setup: BrowserBaseSetup, arguments: BrowserBaseLoadArguments
) -> BrowserBaseLoadOutput:
    """
    Loads documents from the provided urls using BrowserBase.
    """

    assert isinstance(setup, BrowserBaseSetup), "Invalid setup"
    assert isinstance(arguments, BrowserBaseLoadArguments), "Invalid arguments"

    urls = [str(url) for url in arguments.urls]

    loader = BrowserbaseLoader(
        api_key=setup.api_key,
        project_id=setup.project_id,
        session_id=setup.session_id,
        urls=urls,
        text_content=False,
    )

    documents = loader.load()
    return BrowserBaseLoadOutput(documents=documents)

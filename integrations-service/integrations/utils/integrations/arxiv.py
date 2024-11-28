import base64
import os
import tempfile

import arxiv
from beartype import beartype
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import ArxivSearchArguments
from ...models import ArxivSearchOutput, ArxivSearchResult


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def search(arguments: ArxivSearchArguments) -> ArxivSearchOutput:
    """
    Searches Arxiv with the provided query.

    Args:
        arguments (ArxivSearchArguments): The search parameters including query,
                                           maximum results, sorting criteria, and
                                           download options.

    Returns:
        ArxivSearchOutput: The search results wrapped in an output object.
    """
    assert isinstance(arguments, ArxivSearchArguments), "Invalid arguments"

    client = arxiv.Client()
    sort_criterion = {
        "submittedDate": arxiv.SortCriterion.SubmittedDate,
        "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
    }.get(arguments.sort_by, arxiv.SortCriterion.Relevance)

    sort_order = (
        arxiv.SortOrder.Descending
        if arguments.sort_order == "descending"
        else arxiv.SortOrder.Ascending
    )

    search = arxiv.Search(
        query=arguments.query,
        max_results=arguments.max_results,
        sort_by=sort_criterion,
        sort_order=sort_order,
    )

    results = []
    search_results = client.results(search)

    def create_arxiv_search_result(result, pdf_content=None):
        return ArxivSearchResult(
            entry_id=result.entry_id,
            title=result.title,
            authors=[author.name for author in result.authors],
            summary=result.summary.replace("\n", ""),
            published=result.published.strftime("%Y-%m-%d %H:%M:%S"),
            updated=result.updated.strftime("%Y-%m-%d %H:%M:%S"),
            comment=result.comment,
            journal_ref=result.journal_ref,
            doi=result.doi,
            primary_category=result.primary_category,
            categories=result.categories,
            links=[link.href for link in result.links],
            pdf_url=result.pdf_url,
            pdf_downloaded={
                "base64": pdf_content,
                "mime_type": "application/pdf",
                "title": result.title,
            }
            if pdf_content
            else None,
        )

    if arguments.download_pdf:
        for result in search_results:
            with tempfile.TemporaryDirectory() as temp_dir:
                result.download_pdf(dirpath=temp_dir, filename=f"{result.title}.pdf")
                with open(f"{temp_dir}/{result.title}.pdf", "rb") as pdf_file:
                    pdf_content = base64.b64encode(pdf_file.read()).decode("utf-8")
            results.append(create_arxiv_search_result(result, pdf_content))
    else:
        for result in search_results:
            results.append(create_arxiv_search_result(result))

    return ArxivSearchOutput(result=results)

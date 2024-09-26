from ...models import SpiderExecutionArguments, SpiderExecutionSetup

import requests, os, json

async def spider(
    setup: SpiderExecutionSetup, arguments: SpiderExecutionArguments) -> str:
    """
    Fetches data from a specified URL.
    """

    assert isinstance(setup, SpiderExecutionSetup), "Invalid setup"
    assert isinstance(arguments, SpiderExecutionArguments), "Invalid arguments"

    query = arguments.query

    if not query:
        raise ValueError("URL parameter is required for spider")
    
    headers = {
        'Authorization': setup.spider_api_key,
        'Content-Type': 'application/json',
    }

    json_data = {"limit":arguments.limit,
                 "metadata":arguments.metdata,
                 "url":arguments.query,
                 "return_format":arguments.return_format,
                 "request": arguments.request}
                 

    response = requests.post(arguments.base_url,  headers=headers, json=json_data)

    # Ensure the request was successful
    status = response.raise_for_status()

    if status != 200:
        raise Exception(f"Failed to fetch data from {query}")

    # Read and return the entire response content as JSON
    return str(response.json())

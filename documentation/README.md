# Julep Mintlify Documentation

## Development

Install the [Mintlify CLI](https://www.npmjs.com/package/mintlify) to preview the documentation changes locally. To install, use the following command:

```
npm i -g mintlify
```

Run the following command at the root of your documentation (where mint.json is):

```
mintlify dev
```

### Troubleshooting

- Mintlify dev isn't running - Run `mintlify install` to re-install dependencies.
- Page loads as a 404 - Make sure you are running in a folder with `mint.json`.

## API Call Execution

The `execute_api_call.py` module has been updated to include new request arguments that enhance the flexibility of API calls. These changes introduce the following new options:

### New Request Arguments

- **files**: `dict[str, Any] | None`
  - Allows you to send files with your API request. This is useful for endpoints that require file uploads.

- **method**: `str | None`
  - Specifies the HTTP method to use for the request (e.g., GET, POST, PUT). This can override the default method specified in the `ApiCallDef`.

- **follow_redirects**: `bool | None`
  - Determines whether the request should automatically follow HTTP redirects. This can override the default behavior specified in the `ApiCallDef`.

### Usage

When making an API call using the `execute_api_call` function, you can now include these new arguments in the `request_args` dictionary to customize the behavior of your request. Here is an example of how to use these new options:

```python
request_args = {
    "url": "https://api.example.com/data",
    "method": "POST",
    "headers": {"Authorization": "Bearer token"},
    "files": {"file": open("example.txt", "rb")},
    "follow_redirects": True,
}

response = await execute_api_call(api_call, request_args)
```

This example demonstrates how to send a POST request with a file upload and custom headers, while also ensuring that any redirects are followed automatically.

### Response Handling

The response from the API call is processed to include:

- **status_code**: The HTTP status code of the response.
- **headers**: A dictionary of the response headers.
- **content**: The base64-encoded content of the response.
- **json**: The parsed JSON content of the response, if available. If parsing fails, this will be `None`.

### Error Handling

If the response is not successful (i.e., the status code indicates an error), an exception will be raised. Ensure that your implementation handles these exceptions appropriately to maintain robust error handling in your application.
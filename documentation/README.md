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

## Algolia Integration

The project now includes an integration with Algolia, a powerful search-as-a-service platform. This integration allows you to perform searches within an Algolia index and retrieve relevant results efficiently.

### Purpose

The Algolia integration is designed to enhance search capabilities within your application by leveraging Algolia's fast and scalable search engine. It allows you to search for content in an Algolia index and retrieve search results along with additional metadata.

### Usage

To use the Algolia integration, you need to define the setup and search arguments. The integration supports the following components:

- **AlgoliaSetup**: Contains the necessary configuration for connecting to Algolia, including the `algolia_application_id` and `algolia_api_key`.
- **AlgoliaSearchArguments**: Defines the parameters for performing a search, such as `index_name`, `query`, `attributes_to_retrieve`, and `hits_per_page`.

### Setup Instructions

1. **Environment Variables**: Ensure that the following environment variables are set in your `docker-compose.yml` or environment configuration:
   - `ALGOLIA_API_KEY`: Your Algolia API key.
   - `ALGOLIA_APPLICATION_ID`: Your Algolia Application ID.

2. **Configuration**: Define the setup and search arguments in your application code. For example:

   ```python
   from your_module import AlgoliaSetup, AlgoliaSearchArguments

   setup = AlgoliaSetup(
       algolia_application_id="YourApplicationID",
       algolia_api_key="YourAPIKey"
   )

   search_arguments = AlgoliaSearchArguments(
       index_name="YourIndexName",
       query="YourSearchQuery",
       hits_per_page=10
   )
   ```

3. **Performing a Search**: Use the defined setup and search arguments to perform a search operation. The search results will include hits and additional metadata.

### Additional Information

- **Documentation**: For more detailed information on using Algolia, refer to the [Algolia Documentation](https://www.algolia.com/doc/).
- **Provider Information**: The Algolia provider is identified by the name "algolia" and supports the "search" method.

By integrating Algolia, you can significantly improve the search functionality of your application, providing users with fast and relevant search results.
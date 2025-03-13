# Exit on error
set -e

# Run the TypeSpec compiler to generate OpenAPI and Pydantic models for the Responses API
uv_run () {
  uvx \
    --with ruff --with datamodel-code-generator \
    --from typespec-responses/openapi-responses.yaml
}

cd typespec-responses && \
  tsp compile . --output-file openapi-responses.yaml
cd -

cd responses-api && \
  uv_run
cd -

# Generate JSON schema from OpenAPI specification
# This function is a placeholder for generating JSON schema from the OpenAI Responses API

#!/usr/bin/env bash

# Turn on echo command
set -x

# Exit on error
set -e

uv_run () {
  uvx \
    --with ruff --with datamodel-code-generator \
    --from ${2:-poethepoet} \
    $1
}

codegen_then_format () {
  uv_run 'poe codegen' && \
  uv_run 'poe format'  && \
  uv_run 'poe lint' || exit 0
}


cd typespec-responses && \
  tsp compile .
cd -

cd responses-api && \
  codegen_then_format
cd -

# Generate JSON schema from OpenAPI specification
# This function is a placeholder for generating JSON schema from the OpenAI Responses API

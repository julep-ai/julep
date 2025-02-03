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
    uv_run 'ruff check --fix --unsafe-fixes .' 'ruff' || exit 0
}

generate_schemas () {
  # FIXME: This repeated pipe is a crude hack coz I couldn't figure out how to do it in the jq script...
  cat openapi.yaml | yq -o json | jq -f ./schemas/walk.jq | jq -f ./schemas/walk.jq | jq -f ./schemas/walk.jq | jq -f ./schemas/walk.jq | jq -f ./schemas/walk.jq > /tmp/combined.json
  cat /tmp/combined.json | jq '.components.schemas.CreateTaskRequest' > ./schemas/create_task_request.json
  cat /tmp/combined.json | jq '.components.schemas.CreateAgentRequest' > ./schemas/create_agent_request.json
}

cd typespec/ && \
    tsp compile .
cd -

generate_schemas

cd agents-api && \
  codegen_then_format
cd -

cd integrations-service && \
  codegen_then_format
cd -

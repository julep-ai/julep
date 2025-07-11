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

generate_json_schema_local () {
  \cat openapi.yaml | yq -o json | jq -f src/schemas/walk.jq --arg target "${1}" > $2
}

generate_json_schema () {
  curl -sL http://dev.julep.ai/api/openapi.json | jq -f src/schemas/walk.jq --arg target "${1}" > $2
}

cd src/typespec/ && \
  tsp compile .
cd -

generate_json_schema CreateTaskRequest src/schemas/create_task_request.json
generate_json_schema CreateAgentRequest src/schemas/create_agent_request.json

cd src/agents-api && \
  codegen_then_format
cd -

cd src/integrations-service && \
  codegen_then_format
cd -

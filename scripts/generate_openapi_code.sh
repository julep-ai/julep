#!/usr/bin/env bash

# Turn on echo command
set -x

# Exit on error
set -e

cd typespec/ && \
    tsp compile .
cd -

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

cd agents-api && \
  codegen_then_format
cd -

cd integrations-service && \
  codegen_then_format
cd -

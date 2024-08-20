#!/usr/bin/env bash

# Turn on echo command
set -x

# Exit on error
set -e

cd typespec/ && \
    tsp compile .
cd -

# fern generate

cd sdks/python && \
    poetry update && \
    poetry run poe format
cd -

cd agents-api && \
    poetry update && \
    poetry run poe codegen && \
    poetry run poe format
cd -

cd sdks/ts && \
    npm i && npm run codegen
cd -

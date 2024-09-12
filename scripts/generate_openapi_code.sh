#!/usr/bin/env bash

# Turn on echo command
set -x

# Exit on error
set -e

cd typespec/ && \
    tsp compile .
cd -

cd agents-api && \
    poetry run poe codegen && \
    poetry run poe format
cd -

cd sdks/python && \
    poetry run poe codegen
cd -

cd sdks/ts && \
    npm i && npm run codegen
cd -

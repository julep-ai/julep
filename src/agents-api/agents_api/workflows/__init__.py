#!/usr/bin/env python3
# AIDEV-NOTE: Configure Temporal workflow unsafe imports and logging setup for agents-api workflows.
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    import logging

    logging.basicConfig(level=logging.INFO)

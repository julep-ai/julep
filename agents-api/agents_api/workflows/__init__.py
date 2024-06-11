#!/usr/bin/env python3

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    import logging

    logging.basicConfig(level=logging.INFO)

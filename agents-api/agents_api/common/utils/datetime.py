#!/usr/bin/env python3

from datetime import UTC, datetime


def utcnow():
    return datetime.now(UTC)

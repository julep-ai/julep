#!/usr/bin/env python3

from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)

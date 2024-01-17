#!/usr/bin/env python3

from datetime import datetime, timezone

utcnow = lambda: datetime.now(timezone.utc)

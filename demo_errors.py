"""Shared safe error type, including when agent.py is executed as __main__."""

import re


class DemoError(Exception):
    """Only fixed application messages belong here, never upstream error text."""

    def __init__(self, message, *, stage="demo", category="validation_failed", http_status=None, request_id=None):
        super().__init__(message)
        self.stage = stage
        self.category = category
        self.http_status = http_status
        # Retain only the expected opaque identifier shape, not arbitrary headers.
        self.request_id = request_id if isinstance(request_id, str) and re.fullmatch(r"req_[0-9a-fA-F]{32}", request_id) else None

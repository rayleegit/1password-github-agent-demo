"""Synthetic example only. No production integration."""


def retry_delay(attempt: int) -> int:
    if type(attempt) is not int or not 0 <= attempt <= 20:
        raise ValueError("attempt must be an integer between 0 and 20")
    return 2 ** attempt

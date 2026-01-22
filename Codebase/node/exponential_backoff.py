"""
Define Retry class for exponential backoff with jitter
"""
from random import randint

class Retry:
    """
    Implement exponential backoff with jitter.
    """
    def __init__(self, limit: int) -> None:
        if limit < 2:
            raise ValueError(f"{limit=} is invalid. The minimum limit is 2.")
        self.limit    = limit
        self.base     = 0
        self.attempts = 0

    def get_sleep(self):
        wait_time = self.base * 2 ** (self.attempts - 1)
        return randint(self.base, min(self.limit, wait_time))

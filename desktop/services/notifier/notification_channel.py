from typing import Callable


class NotificationChannel:
    __slots__ = "notify_fn"

    def __init__(self, notify_fn=Callable[[str], None]):
        self.notify_fn = notify_fn

    def notify(self, message: str) -> None:
        self.notify_fn(message=message)

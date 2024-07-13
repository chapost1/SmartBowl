from models import Alert
from typing import Protocol


class NotificationChannel(Protocol):
    def notify(self, message: str) -> None:
        pass


class AlertManager:
    def __init__(self, notification_channels: list[NotificationChannel]):
        self.notification_channels = notification_channels

    def on_new_alert(self, alert: Alert) -> None:
        self.notify(message=alert.message)

    def notify(self, message: str):
        for channel in self.notification_channels:
            channel.notify(message=message)

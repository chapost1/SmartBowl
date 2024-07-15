from dataclasses import dataclass
from enum import Enum


class RefillState(Enum):
    OFF = 0
    ON = 1


class OutEventTypes(str, Enum):
    REFILL = "REFILL"
    NEW_TARGET_WEIGHT = "NEW_TARGET_WEIGHT"


@dataclass(frozen=True, slots=True)
class OutEvent:
    command: str
    value: int = 0

    def __str__(self) -> str:
        return f"<value={self.value} command={self.command}>"


class InEventTypes(str, Enum):
    BOWL_CAPACITY = "BOWL_CAPACITY"
    BOWL_WEIGHT = "BOWL_WEIGHT"
    TARGET_WEIGHT_UPDATE = "TARGET_WEIGHT_UPDATE"
    REFILL_STATE_UPDATE = "REFILL_STATE_UPDATE"
    EMPTY_BOWL_ALERT = "EMPTY_BOWL_ALERT"
    GENERAL_ERROR_ALERT = "GENERAL_ERROR_ALERT"


@dataclass(frozen=True, slots=True)
class IncomingEvent:
    time_ms: int
    type: str
    value: float = 0
    error: str = ""

    @staticmethod
    def get_time_field_name() -> str:
        return "time_ms"


@dataclass(frozen=True, slots=True)
class Alert:
    message: str
    ...

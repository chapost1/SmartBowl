from models import IncomingEvent, Alert, InEventTypes, OutEventTypes, OutEvent
from typing import Protocol, Callable
from circuikit.protocols import SendSmiInputFn
import logging

logger = logging.getLogger(__name__)


class BowlGui(Protocol):
    def set_capacity_value(self, capacity: float): ...

    def set_current_weight(self, weight: float): ...

    def set_target_weight(self, weight: float): ...

    def set_refill_state(self, state: int): ...

    def set_refill_callback(self, callback: Callable[[], None]): ...

    def set_propose_new_target_weight_callback(
        self, callback: Callable[[int], None]
    ): ...

    def on_new_target_proposal_denial(self, error_message: str): ...


class AlertFn(Protocol):
    def __call__(self, alert: Alert) -> None: ...


class Bowl:
    def __init__(
        self,
        gui: BowlGui,
        alert_fn: AlertFn,
    ):
        self.alert_fn = alert_fn

        self.gui = gui
        self.gui.set_refill_callback(callback=self.request_refill)
        self.gui.set_propose_new_target_weight_callback(
            callback=self.propose_new_target_weight
        )

        self.send_message_fn = lambda message: ...  # default

    def set_send_message_fn(self, send_message_fn: SendSmiInputFn):
        self.send_message_fn = send_message_fn

    def request_refill(self) -> None:
        self.send_message_to_bowl(message=OutEvent(command=OutEventTypes.REFILL.value))

    def propose_new_target_weight(self, value: int) -> None:
        self.send_message_to_bowl(
            message=OutEvent(value=value, command=OutEventTypes.NEW_TARGET_WEIGHT.value)
        )

    def on_new_event(self, message: dict) -> None:
        event = IncomingEvent(**message)
        match event.type:
            case InEventTypes.BOWL_CAPACITY:
                self.gui.set_capacity_value(capacity=event.value)
            case InEventTypes.BOWL_WEIGHT:
                self.gui.set_current_weight(weight=event.value)
            case InEventTypes.TARGET_WEIGHT_UPDATE:
                if event.error != "":
                    self.gui.on_new_target_proposal_denial(error_message=event.error)
                else:
                    self.gui.set_target_weight(weight=event.value)
            case InEventTypes.REFILL_STATE_UPDATE:
                self.gui.set_refill_state(state=int(event.value))
            case InEventTypes.EMPTY_BOWL_ALERT:
                self.alert_fn(alert=Alert(message="Bowl is empty :("))
            case InEventTypes.GENERAL_ERROR_ALERT:
                logger.error(event.error)

    def send_message_to_bowl(self, message: OutEvent):
        self.send_message_fn(message=message.__str__())

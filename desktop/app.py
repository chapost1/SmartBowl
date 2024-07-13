from circuikit import Circuikit
from circuikit.serial_monitor_interface import (
    ThinkercadInterface,
)
from circuikit.serial_monitor_interface.types import SerialMonitorOptions
from circuikit.services import Service, ServiceAdapter
import services.notifier as notifier
from utils import osx
from functools import partial
from services import bowl
from models import IncomingEvent
import logging

logging.basicConfig(level=logging.INFO)

from dirty.env import (
    THINKERCAD_URL,
    THINKERCAD_OPEN_SIMULATION_TIMEOUT_SECONDS,
    SMS_DESTINATION_PHONE_NUMBER,
    SERIAL_MONITOR_SAMPLE_RATE_MS,
)

if __name__ == "__main__":
    serial_monitor_options = SerialMonitorOptions(
        timestamp_field_name=IncomingEvent.get_time_field_name(),
        interface=ThinkercadInterface(
            thinkercad_url=THINKERCAD_URL,
            open_simulation_timeout=THINKERCAD_OPEN_SIMULATION_TIMEOUT_SECONDS,
        ),
        sample_rate_ms=SERIAL_MONITOR_SAMPLE_RATE_MS,
    )

    alert_manager = notifier.AlertManager(
        notification_channels=[
            notifier.NotificationChannel(
                notify_fn=partial(
                    osx.send_sms, phone_number=SMS_DESTINATION_PHONE_NUMBER
                )
            )
        ]
    )

    bowl_gui = bowl.BowlGUI()

    bowl_service = bowl.Bowl(
        gui=bowl_gui,
        alert_fn=alert_manager.on_new_alert,
    )

    services: list[Service] = [
        ServiceAdapter(on_new_message_fn=bowl_service.on_new_event)
    ]

    kit = Circuikit(
        serial_monitor_options=serial_monitor_options,
        services=services,
    )
    bowl_service.set_send_message_fn(send_message_fn=kit.send_smi_input)

    # avoid blocking the main thread so we can start the gui
    kit.start(block=False)

    # most gui apps requires to start from the main thread
    # and it is a blocking fn, thus starting it after starting the kit
    bowl_gui.start_mainloop()

from abc import ABC
from dataclasses import dataclass, field
from typing import Any

from rov.command import ROVCommands
from rov.enums import SystemModes

"""
Ordering format:
    System Critical: 0 <--- 9
    State Change: 10 <--- 19
    Sensor Readings: 20 <--- 29
    
Notifications:
    System Critical:
        VEHICLE_DISCONNECTED
        VEHICLE_CONNECTED
        ARMED
        DISARMED
    
    State Change:
        GAIN_CHANGE
        SYSTEM_MODE_CHANGE
    
    Sensor Readings:

"""


class ROVNotification:
    def __init__(self, priority: int):
        self.priority = priority

    def __lt__(self, other):
        if not isinstance(other, ROVNotification):
            return False

        return self.priority < other.priority

# SYSTEM CRITICAL
class VehicleDisconnected(ROVNotification):
    def __init__(self):
        super().__init__(1)


class VehicleConnected(ROVNotification):
    def __init__(self):
        super().__init__(2)


class Armed(ROVNotification):
    def __init__(self):
        super().__init__(3)


class Disarmed(ROVNotification):
    def __init__(self):
        super().__init__(4)

# CHANGE OF STATE
class GainChange(ROVNotification):
    def __init__(self, new_gain: int):
        super().__init__(10)
        self.new_gain = new_gain

class SystemModeChanged(ROVNotification):
    def __init__(self, mode: SystemModes):
        super().__init__(11)
        self.mode = mode
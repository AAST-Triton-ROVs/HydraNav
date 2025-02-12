from dataclasses import dataclass
from typing import Tuple


@dataclass
class TelemeteryData:
    cpu_usage: int
    cpu_temp: int
    ram_usage: int
    disk_usage: int
    gpu_usage: int
    gpu_temp: int
    network_usage: Tuple[int, int]

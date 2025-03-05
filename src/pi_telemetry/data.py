from dataclasses import dataclass
from typing import Tuple

@dataclass
class TelemetryData:
    """
    Stores system telemetry data.

    :param cpu_usage: CPU usage as a percentage
    :type cpu_usage: int
    :param cpu_temp: CPU temperature in Celsius
    :type cpu_temp: int
    :param ram_usage: RAM usage as a percentage
    :type ram_usage: int
    :param disk_usage: Disk usage as a percentage
    :type disk_usage: int
    :param gpu_usage: GPU usage as a percentage
    :type gpu_usage: int
    :param gpu_temp: GPU temperature in Celsius
    :type gpu_temp: int
    :param network_usage: Network usage (download, upload) in bytes
    :type network_usage: Tuple[int, int]
    """
    cpu_usage: int
    cpu_temp: int
    ram_usage: int
    disk_usage: int
    gpu_usage: int
    gpu_temp: int
    network_usage: Tuple[int, int]

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
    :param gpu_temp: GPU temperature in Celsius
    :type gpu_temp: int
    :param network_usage: Network usage (download, upload) in bytes
    :type network_usage: Tuple[int, int]
    """
    cpu_usage: int
    cpu_temp: int
    ram_usage: int
    disk_usage: int
    gpu_temp: int
    network_usage: Tuple[int, int]

    def __str__(self) -> str:
        return (
            f"CPU Usage: {self.cpu_usage}% | "
            f"CPU Temp: {self.cpu_temp}°C | "
            f"RAM Usage: {self.ram_usage}% | "
            f"Disk Usage: {self.disk_usage}% | "
            f"GPU Temp: {self.gpu_temp}°C | "
            f"Network Usage: Download {self.network_usage[0]} bytes, "
            f"Upload {self.network_usage[1]} bytes"
        )
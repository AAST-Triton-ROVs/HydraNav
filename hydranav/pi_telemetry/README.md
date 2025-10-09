# Pi Telemetry Module

The Pi Telemetry module provides real-time system monitoring capabilities for remote Raspberry Pi devices. It receives telemetry data over UDP and displays it both in the web interface and through the event system for other modules to consume.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
- [Data Structure](#data-structure)
- [Network Protocol](#network-protocol)
- [Web Interface](#web-interface)
- [Event Integration](#event-integration)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)

## Architecture Overview

The Pi Telemetry module operates using a multi-process architecture:

```
Remote Raspberry Pi
└── Telemetry Client (sends UDP packets)
    │
    │ UDP Socket (Port 2010)
    ▼
Main Process (HydraNav)
├── PiTelemetry Module
│   ├── TelemetryDaemon (subprocess)
│   ├── Data Queue (main → event system)
│   └── UI Queue (main → web interface)
└── Event Dispatcher
    └── Other modules receive telemetry events
```

### Process Flow

1. **Remote Pi** collects system metrics and sends UDP packets
2. **TelemetryDaemon** receives packets in separate process
3. **Data queues** transport telemetry between processes
4. **Main module** dispatches events and updates web interface
5. **Other modules** can subscribe to telemetry events

## Core Components

### PiTelemetry Class

The main module class that coordinates telemetry operations:

```python
class PiTelemetry(GCSModule, Updatable, HasWebGUI):
    def __init__(self):
        # Sets up daemon, queues, and starts telemetry reception
        
    def update(self):
        # Processes incoming telemetry and dispatches events
        
    def webgui_contents(self):
        # Creates web interface with real-time telemetry display
```

**Key Features:**
- **Dual queue system**: Separate queues for event system and web UI
- **Real-time updates**: Continuous processing of incoming telemetry
- **Web integration**: Built-in web interface for telemetry visualization
- **Event broadcasting**: Telemetry data available to other modules

### TelemetryDaemon Class

Background process that handles network communication:

```python
class TelemetryDaemon(multiprocessing.Process, LoggerMixin):
    def __init__(self, queue, quit_event):
        # Sets up UDP socket and process configuration
        
    def run(self):
        # Main loop: receives UDP packets and queues telemetry data
        
    def __create_socket(self):
        # Creates and binds UDP socket with error handling
```

**Key Features:**
- **Robust networking**: Automatic reconnection on socket errors
- **Process isolation**: Runs independently of main application
- **Timeout handling**: Non-blocking socket operations
- **Error recovery**: Graceful handling of network issues

## Data Structure

### TelemetryData Class

Structured representation of system telemetry:

```python
@dataclass
class TelemetryData:
    cpu_usage: int      # CPU usage percentage (0-100)
    cpu_temp: int       # CPU temperature in Celsius
    ram_usage: int      # RAM usage percentage (0-100)  
    disk_usage: int     # Disk usage percentage (0-100)
    gpu_temp: int       # GPU temperature in Celsius
    voltage: float      # System voltage in volts
```

**Data Types:**
- **Percentages**: Integer values 0-100 for usage metrics
- **Temperatures**: Integer values in Celsius
- **Voltage**: Float value for precise power monitoring
- **String representation**: Human-readable format for logging

## Network Protocol

### UDP Packet Structure

The module expects UDP packets with the following binary structure:

```
Packet Format (24 bytes total):
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ CPU Usage   │ CPU Temp    │ RAM Usage   │ Disk Usage  │
│ (4 bytes)   │ (4 bytes)   │ (4 bytes)   │ (4 bytes)   │
├─────────────┼─────────────┼─────────────┴─────────────┤
│ GPU Temp    │ Voltage     │                           │
│ (4 bytes)   │ (4 bytes)   │                           │
└─────────────┴─────────────┴───────────────────────────┘

Encoding: Network byte order (big-endian)
CPU Usage, CPU Temp, RAM Usage, Disk Usage, GPU Temp: unsigned int (I)
Voltage: float (f)
```

### Struct Format String
```python
FORMAT = "!" + "I" * 5 + "f"  # Big-endian, 5 uints + 1 float
BUFFER_SIZE = struct.calcsize(FORMAT)  # 24 bytes
```

### Network Configuration

```python
HOST = "0.0.0.0"        # Bind to all interfaces
PORT = 2010             # Default telemetry port
SOCKET_TIMEOUT = 1      # Non-blocking timeout (seconds)
RECONNECT_DELAY = 2     # Retry delay on socket errors (seconds)
```

## Web Interface

### Real-time Dashboard

The web interface provides a live telemetry dashboard:

**Features:**
- **Responsive table** showing all telemetry metrics
- **Real-time updates** via NiceGUI timer (0.8s interval)
- **Formatted display** with proper units and alignment
- **N/A handling** for missing or invalid data

### Table Structure

| Metric     | Value      |
|------------|------------|
| CPU Usage  | XX %       |
| CPU Temp   | XX °C      |
| RAM Usage  | XX %       |
| Disk Usage | XX %       |
| GPU Temp   | XX °C      |
| Voltage    | XX.XX V    |

### Styling

```python
# Main container
ui.column(align_items="center").classes("w-full")

# Title styling
ui.label("Pi Telemetry").classes(
    "mb-4 text-4xl font-extrabold md:text-5xl lg:text-6xl dark:text-white"
)

# Table styling
ui.table(...).classes("w-full")
```

## Event Integration

### Event Broadcasting

The module dispatches telemetry events that other modules can subscribe to:

```python
# In PiTelemetry.update()
event_dispatcher.dispatch("telemetry", telemetry_data)
```

### Subscribing to Telemetry Events

Other modules can receive telemetry data:

```python
from hydranav.core import event_dispatcher

def handle_telemetry(data):
    print(f"CPU: {data.cpu_usage}%, Temp: {data.cpu_temp}°C")

event_dispatcher.subscribe("telemetry", handle_telemetry)
```

## Configuration

### Network Settings

Configuration is managed through the main config system:

```yaml
# config.yaml
networking:
  baseIP: "0.0.0.0"           # Server bind address
  retryDelaySec: 2            # Socket error retry delay
  socketTimeout: 1            # Socket timeout

piTelemetry:
  port: 2010                  # UDP port for telemetry
```

### Module Priority

```python
@classmethod
def init_order(cls):
    return 1  # Early initialization for system monitoring
```

## Usage Examples

### Basic Telemetry Monitoring

```python
# The module automatically starts when initialized
telemetry = PiTelemetry()

# Access via module manager
from hydranav.core import module_manager
telemetry_module = module_manager.get_instance("PiTelemetry")
```

### Custom Telemetry Handler

```python
class MyModule(GCSModule):
    def __init__(self):
        super().__init__()
        event_dispatcher.subscribe("telemetry", self.handle_telemetry)
    
    def handle_telemetry(self, data: TelemetryData):
        # Log high CPU usage
        if data.cpu_usage > 80:
            self._logger.warning(f"High CPU usage: {data.cpu_usage}%")
        
        # Monitor temperature
        if data.cpu_temp > 70:
            self._logger.error(f"CPU overheating: {data.cpu_temp}°C")
```

### Telemetry Client (Raspberry Pi Side)

Example client code for sending telemetry from a Raspberry Pi:

```python
import socket
import struct
import psutil
import time

def send_telemetry():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ("192.168.1.100", 2010)  # GCS IP and port
    
    while True:
        # Collect system metrics
        cpu_usage = int(psutil.cpu_percent())
        cpu_temp = int(psutil.sensors_temperatures()['cpu_thermal'][0].current)
        ram_usage = int(psutil.virtual_memory().percent)
        disk_usage = int(psutil.disk_usage('/').percent)
        gpu_temp = 45  # Mock GPU temperature
        voltage = 5.1  # Mock voltage reading
        
        # Pack data
        packet = struct.pack("!" + "I" * 5 + "f",
                           cpu_usage, cpu_temp, ram_usage, 
                           disk_usage, gpu_temp, voltage)
        
        # Send packet
        sock.sendto(packet, server_address)
        time.sleep(1)  # Send every second
```

## Architecture Benefits

### Dual Queue Design
- **Event system queue**: For module-to-module communication
- **UI queue**: For web interface updates without blocking events
- **Independent processing**: Web UI and event system don't interfere

### Process Isolation
- **Network reliability**: Socket errors don't crash main application
- **Performance**: Network I/O doesn't block main event loop
- **Recovery**: Automatic reconnection on network failures

### Real-time Monitoring
- **Low latency**: Direct UDP communication
- **Continuous updates**: Non-blocking queue operations
- **Live dashboard**: Real-time web interface updates

## Technical Notes

### Network Considerations
- **UDP protocol**: Fast, connectionless communication suitable for telemetry
- **Packet loss tolerance**: System can handle occasional dropped packets
- **Network discovery**: Supports multiple network interfaces

### Performance
- **Memory efficiency**: Small queue sizes (1 item) prevent memory buildup
- **CPU overhead**: Minimal processing for binary data unpacking
- **Update frequency**: Configurable via web interface timer

### Error Handling
- **Socket timeouts**: Prevent blocking operations
- **Queue overflow**: Graceful handling of full queues
- **Data validation**: Struct unpacking validates packet format
- **Process monitoring**: Health checks via `status_ok()`

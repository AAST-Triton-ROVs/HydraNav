# Pi Admin Module

The Pi Admin module provides remote system administration capabilities for Raspberry Pi devices. It enables secure remote control of critical system operations like power management, service restarts, and system maintenance through both web interface and programmatic commands.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
- [Command Structure](#command-structure)
- [Network Protocol](#network-protocol)
- [Web Interface](#web-interface)
- [Request Integration](#request-integration)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)

## Architecture Overview

The Pi Admin module uses a client-server architecture with TCP communication:

```
HydraNav GCS
├── PiAdmin Module
│   ├── Command Queue
│   └── PiAdminDaemon (subprocess)
│       └── TCP Server (Port 2015)
            │
            │ TCP Connection
            ▼
Remote Raspberry Pi
└── Admin Client
    ├── Receives Commands
    └── Executes System Operations
        ├── systemctl (service management)
        ├── shutdown/reboot
        └── process control
```

### Communication Flow

1. **Command initiation**: Web interface or other modules trigger admin commands
2. **Queue processing**: Commands are queued for the daemon process
3. **TCP transmission**: Daemon sends binary command packets to remote Pi
4. **Remote execution**: Pi client receives commands and executes system operations
5. **Process monitoring**: Daemon tracks connection status and handles errors

## Core Components

### PiAdmin Class

The main module class that provides administrative control interface:

```python
class PiAdmin(GCSModule, Updatable, HasWebGUI):
    def __init__(self):
        # Sets up daemon, queues, and request handlers
        
    def poweroff(self):
        # Initiates remote system shutdown
        
    def restart_mavproxy(self):
        # Restarts MAVProxy service on remote Pi
```

**Key Features:**
- **Process isolation**: Admin daemon runs in separate process
- **Web interface**: Built-in control panel for all admin functions
- **Request integration**: Exposes commands through request manager
- **Input mapping**: Supports controller button mappings for admin functions

### PiAdminDaemon Class

Background process that handles network communication:

```python
class PiAdminDaemon(multiprocessing.Process, LoggerMixin):
    def __init__(self, admin_queue, quit_event):
        # Sets up TCP server socket
        
    def run(self):
        # Listens for connections and sends commands
        
    def __create_socket(self):
        # Creates TCP server with error handling
```

**Key Features:**
- **TCP reliability**: Connection-oriented protocol ensures command delivery
- **Command queuing**: Thread-safe queue for command processing
- **Connection management**: Handles client connections and disconnections
- **Error recovery**: Robust socket error handling and recovery

## Command Structure

### AdminCommands Enum

All administrative commands are defined in a centralized enum:

```python
class AdminCommands(Enum):
    POWEROFF = 0          # Shutdown the remote system
    REBOOT = 1            # Restart the remote system
    RESTART_MAVPROXY = 2  # Restart MAVProxy service
    RESTART_GRIPPER = 3   # Restart gripper/manfaloty service
    RESTART_TELEMETRY = 4 # Restart telemetry service
    RESTART_ADMIN = 10    # Restart admin service itself
```

### Command Categories

**System Power Management:**
- `POWEROFF`: Safe system shutdown
- `REBOOT`: System restart with proper service shutdown

**Service Management:**
- `RESTART_MAVPROXY`: Autopilot communication service
- `RESTART_GRIPPER`: Gripper and sampling system service
- `RESTART_TELEMETRY`: System monitoring service
- `RESTART_ADMIN`: Admin service restart (self-restart)

## Network Protocol

### TCP Packet Structure

Commands are sent as binary packets over TCP:

```
Packet Format (4 bytes):
┌─────────────────────────────────┐
│        Command Value            │
│         (4 bytes)               │
│     Network Byte Order          │
└─────────────────────────────────┘

Encoding: Big-endian unsigned integer
Struct Format: "!I"
```

### Protocol Details

```python
# Command encoding
command_value = AdminCommands.POWEROFF.value  # 0
packet = struct.pack("!I", command_value)     # 4 bytes

# Network configuration
HOST = "0.0.0.0"        # Bind to all interfaces
PORT = 2015             # Admin service port
SOCKET_TIMEOUT = 1      # Connection timeout
```

### Connection Handling

- **Protocol**: TCP (reliable, connection-oriented)
- **Port**: 2015 (configurable via config.yaml)
- **Timeout**: 1 second for connection operations
- **Reconnection**: Automatic retry on socket errors

## Web Interface

### Control Panel

The web interface provides a comprehensive admin dashboard:

```
┌─────────────────────────────────────┐
│              Pi Admin               │
├─────────────────────────────────────┤
│          [Power Off]                │
│          [Reboot]                   │
│          [Restart MAVProxy]         │
│          [Restart Manfaloty Bridge] │
│          [Restart Telemetry]        │
│          [Restart Admin]            │
└─────────────────────────────────────┘
```

### Interface Features

- **Full-width buttons**: Easy touch/click targets
- **Clear labeling**: Descriptive button text
- **Responsive design**: Works on mobile and desktop
- **Immediate feedback**: Actions execute immediately on click

### Styling

```python
# Container styling
ui.column(align_items="center").classes("w-full")

# Card layout
ui.card().classes("w-1/2 justify-center items-center")

# Title styling  
ui.label("Pi Admin").classes(
    "mb-4 text-4xl font-extrabold md:text-5xl lg:text-6xl dark:text-white"
)

# Button styling
ui.button("Power Off", on_click=self.poweroff).classes("w-full")
```

## Request Integration

### Request Handler Registration

The module exposes all admin functions through the request manager:

```python
# System power control
request_manager.register_handler("pi-admin/poweroff", self.poweroff)
request_manager.register_handler("pi-admin/reboot", self.reboot)

# Service restart commands
request_manager.register_handler("pi-admin/restart/mavproxy", self.restart_mavproxy)
request_manager.register_handler("pi-admin/restart/telemetry", self.restart_telemetry)

# Controller button mappings
request_manager.register_handler("mapper/PI_POWEROFF", self.poweroff)
request_manager.register_handler("mapper/PI_REBOOT", self.reboot)
```

### Request Naming Convention

- **Namespace**: All requests prefixed with `pi-admin/`
- **Categories**: `poweroff`, `reboot`, `restart/<service>`
- **Mapping integration**: Special `mapper/` prefix for controller buttons

## Configuration

### Network Configuration

```yaml
# config.yaml
networking:
  baseIP: "0.0.0.0"           # Server bind address
  socketTimeout: 1            # Connection timeout

piAdmin:
  port: 2015                  # TCP port for admin commands
```

### Controller Integration

Admin commands can be mapped to controller buttons:

```yaml
userInput:
  mappings:
    - name: "admin-mapping"
      SELECT: "PI_POWEROFF"     # Maps to mapper/PI_POWEROFF
      START: "PI_REBOOT"        # Maps to mapper/PI_REBOOT
```

### Module Priority

```python
@classmethod
def init_order(cls):
    return 1  # Early initialization for system management
```

## Usage Examples

### Basic Admin Operations

```python
# Access through module manager
from hydranav.core import module_manager
admin = module_manager.get_instance("PiAdmin")

# Execute admin commands
admin.poweroff()              # Shutdown remote system
admin.reboot()                # Restart remote system
admin.restart_mavproxy()      # Restart autopilot service
```

### Programmatic Command Execution

```python
from hydranav.core import request_manager

# Execute via request manager
request_manager.request("pi-admin/poweroff")
request_manager.request("pi-admin/restart/telemetry")
```

### Remote Pi Client Implementation

Example client code for the Raspberry Pi side:

```python
import socket
import struct
import subprocess
import sys
from enum import Enum

class AdminCommands(Enum):
    POWEROFF = 0
    REBOOT = 1
    RESTART_MAVPROXY = 2
    RESTART_GRIPPER = 3
    RESTART_TELEMETRY = 4
    RESTART_ADMIN = 10

def execute_command(command_value):
    """Execute the received admin command."""
    command = AdminCommands(command_value)
    
    if command == AdminCommands.POWEROFF:
        subprocess.run(["sudo", "shutdown", "-h", "now"])
    elif command == AdminCommands.REBOOT:
        subprocess.run(["sudo", "reboot"])
    elif command == AdminCommands.RESTART_MAVPROXY:
        subprocess.run(["sudo", "systemctl", "restart", "mavproxy"])
    elif command == AdminCommands.RESTART_GRIPPER:
        subprocess.run(["sudo", "systemctl", "restart", "gripper-daemon"])
    elif command == AdminCommands.RESTART_TELEMETRY:
        subprocess.run(["sudo", "systemctl", "restart", "telemetry-daemon"])
    elif command == AdminCommands.RESTART_ADMIN:
        subprocess.run(["sudo", "systemctl", "restart", "admin-daemon"])

def admin_client():
    """Pi-side admin client that receives and executes commands."""
    GCS_IP = "192.168.1.10"  # GCS IP address
    PORT = 2015
    
    while True:
        try:
            # Connect to GCS admin daemon
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((GCS_IP, PORT))
            
            # Receive command packet
            data = sock.recv(4)
            if len(data) == 4:
                command_value = struct.unpack("!I", data)[0]
                print(f"Received admin command: {command_value}")
                execute_command(command_value)
                
        except Exception as e:
            print(f"Admin client error: {e}")
            time.sleep(5)  # Wait before reconnecting
        finally:
            sock.close()

if __name__ == "__main__":
    admin_client()
```

### Service Integration

Create systemd service for the admin client:

```ini
# /etc/systemd/system/admin-daemon.service
[Unit]
Description=HydraNav Admin Client
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/python3 /home/pi/admin_client.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Architecture Benefits

### Process Isolation
- **Daemon separation**: Network operations don't block main application
- **Error containment**: Socket errors don't crash main system
- **Independent monitoring**: Daemon health tracked separately

### Reliable Communication
- **TCP protocol**: Guaranteed command delivery
- **Connection management**: Proper connection handling and cleanup
- **Error recovery**: Automatic retry on network failures

### Security Considerations
- **Command validation**: Enum-based command structure prevents invalid commands
- **Network binding**: Configurable network interface binding
- **Process permissions**: Daemon runs with limited privileges

### Operational Safety
- **Graceful shutdown**: Proper process termination
- **Service restart**: Individual service control without full reboot
- **Remote diagnostics**: Enable troubleshooting without physical access

## Technical Notes

### Queue Management
- **Single item queue**: Prevents command buildup and ensures latest command priority
- **Non-blocking operations**: Queue operations don't block main thread
- **Thread safety**: Multiprocessing queue ensures safe inter-process communication

### Network Reliability
- **Connection timeout**: Prevents hanging connections
- **Socket reuse**: SO_REUSEADDR for rapid restart capability
- **Error logging**: Comprehensive logging for debugging network issues

### Command Execution
- **Atomic operations**: Each command executed independently
- **Immediate execution**: Commands processed as soon as connection established
- **State independence**: No persistent state between commands

### Monitoring and Diagnostics
- **Process health**: `status_ok()` method for daemon monitoring
- **Connection logging**: Detailed logs for connection events
- **Error tracking**: Comprehensive error reporting and recovery

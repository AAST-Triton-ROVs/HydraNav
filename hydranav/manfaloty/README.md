# Manfaloty Module

The Manfaloty module controls the ROV's manipulation and sampling systems, including gripper operations, pump control, and pH sensing capabilities. The name "Manfaloty" was inspired by Abdallah, the electrical head, who mentioned it spontaneously - it's the name of a famous Egyptian poet, adding a touch of cultural heritage to this technical system.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
- [Command Structure](#command-structure)
- [Network Protocol](#network-protocol)
- [Web Interface](#web-interface)
- [Morse Code Feature](#morse-code-feature)
- [Event Integration](#event-integration)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)

## Architecture Overview

The Manfaloty module uses a UDP-based command system to control remote manipulation hardware:

```
HydraNav GCS
├── Manfaloty Module
│   ├── Command Queue
│   ├── ManfalotyDaemon (subprocess)
│   │   └── UDP Client (Port 2005)
│   └── Web Interface
       │
       │ UDP Packets
       ▼
Remote Raspberry Pi
├── Manfaloty Client
└── Arduino/Hardware Interface
    ├── Gripper Control (servo motors)
    ├── Pump/Relay Control
    ├── pH Sensor
    └── Motor Controllers
```

### System Integration

1. **Command generation**: Web interface or controller inputs trigger commands
2. **Queue processing**: Commands are queued for reliable transmission
3. **UDP transmission**: Daemon sends command packets to remote hardware
4. **Hardware control**: Remote client translates commands to hardware actions
5. **Feedback systems**: pH readings and status updates return via events

## Core Components

### Manfaloty Class

The main module class that coordinates manipulation operations:

```python
class Manfaloty(GCSModule, HasWebGUI):
    def __init__(self):
        # Sets up daemon, event subscriptions, and request handlers
        
    def gripper_open_jaws(self):
        # Controls gripper jaw opening
        
    def pump_on(self):
        # Activates sampling pump
        
    def play_morse_code(self, text: str):
        # Morse code communication via pump relay
```

**Key Features:**
- **Process isolation**: Command transmission runs in separate process
- **Web interface**: Comprehensive control panel for all functions
- **Event integration**: Subscribes to controller and system events
- **Morse code**: Novel communication feature using pump relay
- **TTS integration**: Audio feedback for pump operations

### ManfalotyDaemon Class

Background process handling network communication:

```python
class ManfalotyDaemon(multiprocessing.Process, LoggerMixin):
    def __init__(self, command_queue, quit_event):
        # Sets up UDP socket and process configuration
        
    def run(self):
        # Main loop: processes commands and sends UDP packets
        
    def __create_socket(self):
        # Creates UDP socket with error handling
```

**Key Features:**
- **Burst transmission**: Special handling for gripper commands (multiple packets)
- **Non-blocking I/O**: Handles network congestion gracefully
- **Error recovery**: Comprehensive logging and error handling
- **Queue processing**: Thread-safe command consumption

## Command Structure

### ManfalotyCommands Enum

All manipulation commands are centrally defined:

```python
class ManfalotyCommands(Enum):
    GRIPPER_JAW_CLOSE = -1      # Close gripper jaws
    GRIPPER_JAW_OPEN = 1        # Open gripper jaws
    RELAY_ON = 2                # Activate pump/relay
    RELAY_OFF = -2              # Deactivate pump/relay
    PH_TAKE_READING = 4         # Trigger pH sensor reading
    RESET_MOTORS = 100          # Reset all motor controllers
    RESTART_ARDUINO = 1000      # Restart Arduino system
```

### Command Categories

**Gripper Control:**
- `GRIPPER_JAW_OPEN/CLOSE`: Primary manipulation functions
- Special burst transmission for reliable actuation

**Sampling System:**
- `RELAY_ON/OFF`: Pump control for water sampling
- `PH_TAKE_READING`: Chemical analysis trigger

**System Management:**
- `RESET_MOTORS`: Recovery from motor errors
- `RESTART_ARDUINO`: Full hardware system restart

### Command Values

The enum uses meaningful integer values:
- **Positive/Negative**: Opposite actions (open/close, on/off)
- **Magnitude scaling**: Larger values for system-level operations
- **Hardware compatibility**: Values designed for Arduino interpretation

## Network Protocol

### UDP Packet Structure

Commands are transmitted as compact binary packets:

```
Packet Format (4 bytes):
┌─────────────────────────────────┐
│        Command Value            │
│         (4 bytes)               │
│     Network Byte Order          │
└─────────────────────────────────┘

Encoding: Big-endian signed integer
Struct Format: "!i"
```

### Transmission Logic

```python
# Standard transmission
data = struct.pack("!i", command.value)
socket.sendto(data, pi_address)

# Burst transmission (gripper commands)
for _ in range(JAWS_BURST_FREQ):
    socket.sendto(data, pi_address)
```

### Network Configuration

```python
BASE_IP = "0.0.0.0"        # Local bind address
PI_IP = "192.168.1.100"    # Remote Pi address
PORT = 2005                # Manfaloty service port
SOCKET_TIMEOUT = 1.0       # Operation timeout
RETRY_DELAY = 2            # Reconnection delay
JAWS_BURST_FREQ = 3        # Gripper command repetition
```

## Web Interface

### Control Dashboard

The web interface provides comprehensive manipulation control:

```
┌─────────────────────────────────────┐
│              Manfaloty              │
├─────────────────────────────────────┤
│ Gripper Jaws    [Open]    [Close]   │
│ Pump           [On]       [Off]     │
│ [    PH: 7.2    ]  [Take PH Reading]│
│ [Morse: hello___]  [Submit]         │
│ [        Restart Arduino        ]   │
│ [        Reset Motors           ]   │
└─────────────────────────────────────┘
```

### Interface Features

- **Organized controls**: Grouped by function (gripper, pump, sensors)
- **Real-time feedback**: pH reading display with status updates
- **Morse code input**: Text-to-morse conversion and transmission
- **System management**: Arduino and motor reset capabilities
- **Responsive design**: Touch-friendly button layout

### Dynamic Updates

```python
# pH reading display
self.__webgui_ph_reading_label.set_text("...")  # Processing
self.__webgui_ph_reading_label.set_text("7.2")  # Result

# Styling for different states
.classes("bg-blue-500 text-white text-xl h-12 flex items-center justify-center")
```

## Morse Code Feature

### International Standard Implementation

The module implements International Telecommunication Union morse code standards:

```python
MORSE_LETTERS = {
    "a": ".-",    "b": "-...",  "c": "-.-.",   # ... (full alphabet)
}

# Timing standards:
# - Dash = 3 dots
# - Letter spacing = 3 dots  
# - Word spacing = 7 dots
# - Signal spacing = 1 dot
```

### Morse Code Transmission

```python
def play_morse_code(self, text: str):
    for letter in text:
        if letter == " ":
            time.sleep(DOT_TIME * 7)  # Word spacing
            continue
            
        morse_letter = MORSE_LETTERS[letter]
        for char in morse_letter:
            self.relay_on()  # Signal start
            if char == ".":
                time.sleep(DOT_TIME)      # Dot duration
            else:  # Dash
                time.sleep(DOT_TIME * 3)  # Dash duration
            self.relay_off() # Signal end
            time.sleep(DOT_TIME)          # Signal spacing
```

### Use Cases

- **Emergency communication**: Backup communication channel
- **System testing**: Verify pump relay functionality
- **Educational**: Demonstrate morse code principles
- **Novelty**: Unique feature for demonstrations

## Event Integration

### Event Subscriptions

The module subscribes to various system events:

```python
# Controller mappings
event_dispatcher.subscribe("mapper/GRIPPER_JAW_OPEN", self.gripper_open_jaws)
event_dispatcher.subscribe("mapper/PUMP_ON", self.relay_on)
event_dispatcher.subscribe("mapper/PH_TAKE_READING", self.take_ph_reading)

# Hold button support
event_dispatcher.subscribe("mapper/hold/GRIPPER_JAW_OPEN", self.gripper_open_jaws)
```

### Event Broadcasting

The module generates events for other systems:

```python
# System notifications
event_dispatcher.dispatch("manfaloty/arduino-restart")
event_dispatcher.dispatch("manfaloty/pump-on") 
event_dispatcher.dispatch("manfaloty/ph-take-reading")
```

### TTS Integration

Audio feedback for pump operations:

```python
PUMP_ON_LINE = TTS.register_line("Pump On")
PUMP_OFF_LINE = TTS.register_line("Pump OFF")

TTS.attach_to_event(PUMP_ON_LINE, "manfaloty/pump-on")
TTS.attach_to_event(PUMP_OFF_LINE, "manfaloty/pump-off")
```

## Configuration

### Network Settings

```yaml
# config.yaml
networking:
  baseIP: "0.0.0.0"           # Local bind address
  raspIP: "192.168.1.100"     # Remote Pi IP

manfaloty:
  port: 2005                  # UDP port
  jawsBurstFreq: 3            # Gripper command repetition
  morseCodeDotTimeSec: 0.2    # Morse code timing
```

### Controller Integration

```yaml
userInput:
  mappings:
    - name: "rov-controls"
      R1: "GRIPPER_JAW_OPEN"     # Right bumper
      L1: "GRIPPER_JAW_CLOSE"    # Left bumper  
      X: "PUMP_ON"               # X button
      O: "PUMP_OFF"              # Circle button
      TRIANGLE: "PH_TAKE_READING" # Triangle button
```

## Usage Examples

### Basic Manipulation Control

```python
# Access through module manager
from hydranav.core import module_manager
manfaloty = module_manager.get_instance("Manfaloty")

# Direct control
manfaloty.gripper_open_jaws()     # Open gripper
manfaloty.pump_on()               # Start sampling
manfaloty.take_ph_reading()       # Measure pH
```

### Request Manager Integration

```python
from hydranav.core import request_manager

# Execute via request system
request_manager.request("manfaloty/start-pump")
request_manager.request("manfaloty/restart") 
```

### Event-Based Control

```python
from hydranav.core import event_dispatcher

# Trigger via events
event_dispatcher.dispatch("mapper/GRIPPER_JAW_OPEN")
event_dispatcher.dispatch("mapper/PUMP_ON")
```

### Remote Hardware Client

Example Arduino/Pi client implementation:

```python
import socket
import struct
from enum import Enum

class ManfalotyCommands(Enum):
    GRIPPER_JAW_CLOSE = -1
    GRIPPER_JAW_OPEN = 1
    RELAY_ON = 2
    RELAY_OFF = -2
    PH_TAKE_READING = 4
    RESET_MOTORS = 100
    RESTART_ARDUINO = 1000

def execute_command(command_value):
    """Execute received manipulation command."""
    command = ManfalotyCommands(command_value)
    
    if command == ManfalotyCommands.GRIPPER_JAW_OPEN:
        # Control servo to open position
        servo.write(90)  
    elif command == ManfalotyCommands.GRIPPER_JAW_CLOSE:
        # Control servo to closed position
        servo.write(0)
    elif command == ManfalotyCommands.RELAY_ON:
        # Activate pump relay
        digitalWrite(RELAY_PIN, HIGH)
    elif command == ManfalotyCommands.PH_TAKE_READING:
        # Read pH sensor and send back result
        ph_value = analogRead(PH_SENSOR_PIN)
        send_ph_reading(ph_value)

def manfaloty_client():
    """Pi-side client for manipulation commands."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 2005))
    
    while True:
        try:
            data, client = sock.recvfrom(4)
            command_value = struct.unpack("!i", data)[0]
            execute_command(command_value)
        except Exception as e:
            print(f"Manfaloty client error: {e}")
```

## Architecture Benefits

### Reliable Communication
- **UDP protocol**: Fast, suitable for real-time control
- **Burst transmission**: Ensures critical commands (gripper) are received
- **Non-blocking I/O**: Prevents network issues from blocking operations

### Modular Design
- **Command enumeration**: Type-safe command definitions
- **Event integration**: Seamless controller and system integration  
- **Process isolation**: Network operations don't affect main system

### Creative Features
- **Morse code**: Innovative backup communication channel
- **TTS feedback**: Audio confirmation of operations
- **Web interface**: Comprehensive remote control capabilities

### Operational Safety
- **Queue management**: Prevents command overflow
- **Error handling**: Robust network error recovery
- **Status monitoring**: Health checking via `status_ok()`

## Technical Notes

### Hardware Considerations
- **Servo control**: Gripper requires precise positioning
- **Relay switching**: Pump control via electrical relay
- **Sensor integration**: pH sensor analog-to-digital conversion
- **Power management**: Arduino restart/reset capabilities

### Network Performance  
- **Packet size**: Minimal 4-byte packets for efficiency
- **Transmission frequency**: Configurable burst rates for reliability
- **Error tolerance**: UDP packet loss handling
- **Latency**: Real-time control requirements

### Threading and Concurrency
- **Daemon isolation**: Network I/O in separate process
- **Morse code threading**: Non-blocking morse transmission
- **Queue safety**: Thread-safe command queuing
- **Event coordination**: Synchronized event handling

### Cultural Heritage
The "Manfaloty" name, suggested spontaneously by Abdallah (our electrical head), references the famous Egyptian poet Ahmed Fouad Negm (known as "El-Abnoudy" or sometimes "Manfaloty" in colloquial references). This adds a touch of cultural pride to our technical system, embodying the fusion of engineering excellence with cultural identity.

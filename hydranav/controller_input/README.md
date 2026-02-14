# HydraNav Controller Input Module

The `controller_input` module provides comprehensive gamepad/controller support for HydraNav, enabling precise underwater vehicle control through modern gaming controllers like PlayStation DualSense and Xbox controllers. This module handles device detection, input processing, and seamless integration with the core input mapping system.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
  - [ControllerInput (Main Module)](#controllerinput-main-module)
  - [ControllerDaemon (Process Handler)](#controllerdaemon-process-handler)
  - [Controller Events System](#controller-events-system)
- [Supported Controllers](#supported-controllers)
- [Input Processing](#input-processing)
- [Configuration System](#configuration-system)
- [Integration with Core Systems](#integration-with-core-systems)
- [Technical Implementation](#technical-implementation)
- [Usage Examples](#usage-examples)

## Architecture Overview

The controller input system uses a dedicated process for hardware interaction, communicating with the main application through a multiprocessing queue for reliable, low-latency input handling.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONTROLLER INPUT ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MAIN PROCESS                          CONTROLLER PROCESS                   │
│  ┌─────────────────────┐              ┌─────────────────────┐               │
│  │ ControllerInput     │              │ ControllerDaemon    │               │
│  │ - Event Processing  │◄─────────────┤ - Hardware I/O      │               │
│  │ - Module Lifecycle  │  Event Queue │ - Input Processing  │               │
│  │ - Health Monitoring │              │ - Device Management │               │
│  └─────────────────────┘              └─────────────────────┘               │
│           │                                       │                         │
│           ▼                                       ▼                         │
│  ┌─────────────────────┐              ┌─────────────────────┐               │
│  │ Core Integration    │              │ Pyglet Input System │               │
│  │ - InputMapper       │              │ - Cross-platform    │               │
│  │ - EventDispatcher   │              │ - Device Detection  │               │
│  │ - TextToSpeech      │              │ - Callback System   │               │
│  └─────────────────────┘              └─────────────────────┘               │
│                                                  │                          │
│                                                  ▼                          │
│                                       ┌─────────────────────┐               │
│                                       │ Physical Controllers│               │
│                                       │ - PlayStation       │               │
│                                       │ - 8BitDo            │               │
│                                       │ - Xbox              │               │
│                                       └─────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘

Process Communication Flow:
Physical Input → Pyglet → ControllerDaemon → Event Queue → ControllerInput → Core Systems
```

---

## Core Components

### ControllerInput (Main Module)

**File:** `__init__.py`

The main module class that integrates controller input into HydraNav's module system, handling the lifecycle and event processing.

#### Architecture
- **GCSModule Integration**: Full lifecycle management with health monitoring
- **Updatable Interface**: Regular event queue processing in main loop
- **Multiprocess Coordination**: Manages controller daemon process
- **Event Translation**: Converts controller events to input mapper actions
- **Audio Feedback**: TTS notifications for connection status

#### Core Responsibilities
```python
class ControllerInput(GCSModule, Updatable):
    def update(self):
        # Process events from controller daemon
        while not self.__event_queue.empty():
            event = self.__event_queue.get_nowait()
            
            # Route different event types
            if isinstance(event, ButtonDown):
                input_mapper.digital_input(event.button)
            elif isinstance(event, AbsoluteAxisMotion):
                input_mapper.analogue_input(event.axis, event.value)
```

#### Event Processing Flow
1. **Queue Monitoring**: Continuously checks multiprocessing queue for events
2. **Event Classification**: Routes events by type (button, axis, connection)
3. **Input Translation**: Forwards controller events to InputMapper
4. **System Integration**: Dispatches connection events to EventDispatcher
5. **Audio Feedback**: Triggers TTS for user notifications

---

### ControllerDaemon (Process Handler)

**File:** `controller_daemon.py`

A dedicated process that handles low-level controller interaction using Pyglet, providing isolated and responsive input processing.

#### Architecture
- **Process Isolation**: Runs in separate process to prevent blocking
- **Pyglet Integration**: Uses Pyglet input system for cross-platform support
- **Dynamic Discovery**: Automatically detects and configures supported controllers
- **Event Generation**: Converts raw input to structured events
- **Connection Management**: Handles device connection/disconnection gracefully

#### Key Features

##### Device Detection & Configuration
```python
def __get_controller(self):
    devices = pyglet.input.get_devices()
    for config in CONTROLLER_CONFIGS:
        for device in devices:
            if device.name == config["deviceName"]:
                self.__controller_device = device
                self.__controller_connected = True
                self.__setup_mappings(config)
```

##### Input Processing Types
- **Button Handling**: Press/release detection with hold state management
- **Axis Processing**: Joystick movement with dead zone filtering and scaling
- **Hat Processing**: D-pad input as discrete directional events
- **Trigger Processing**: Analog trigger support with threshold detection

##### Hold State Management
```python
def __process_digital_hold(self):
    # Implements hold detection for both buttons and hats
    # - Initial hold trigger after configured delay
    # - Repeated hold events at configured intervals
    # - Automatic cleanup on release
```

---

### Controller Events System

**File:** `controller_events.py`

Structured event classes that represent different types of controller input, providing type safety and clear data contracts.

#### Event Types
```python
class ButtonDown(ControllerEvents):
    """Discrete button press event"""
    def __init__(self, button: str):
        self.button = button  # Mapped button name (e.g., "A", "R1")

class ButtonHold(ControllerEvents):
    """Continuous button hold event"""
    def __init__(self, button: str):
        self.button = button

class AbsoluteAxisMotion(ControllerEvents):
    """Analog axis movement (joysticks, triggers)"""
    def __init__(self, axis: str, value: int):
        self.axis = axis      # Mapped axis name (e.g., "LJ-X", "RJ-Y")
        self.value = value    # Normalized value (-100 to 100)

class ControllerConnected(ControllerEvents):
    """Controller connection notification"""
    def __init__(self, name: str):
        self.device_name = name

class ControllerDisconnected(ControllerEvents):
    """Controller disconnection notification"""
```

#### Event Flow
```
Physical Input → Pyglet → ControllerDaemon → Event Objects → Queue → ControllerInput → InputMapper
```

---

## Supported Controllers

The system supports multiple controller types through configurable device mappings:

### PlayStation DualSense (Wired)
```yaml
controller:
  configs:
    - displayName: "DualSense Wired"
      deviceName: "Sony Interactive Entertainment DualSense Wireless Controller"
      mappings:
        # Face buttons
        A: {"type": "button", "names": ["BTN_A"]}
        B: {"type": "button", "names": ["BTN_B"]}
        # D-pad as hat
        1: {"type": "hat", "names": ["ABS_HAT0Y"], "onValue": 1}
        # Analog sticks
        LJ-X: {"type": "axis", "names": ["ABS_X"]}
        LJ-Y: {"type": "axis", "names": ["ABS_Y"]}
```

### 8BitDo Ultimate 2C (Bluetooth)
```yaml
- displayName: "8BitDo Ultimate 2C Bluetooth"
  deviceName: "8BitDo Ultimate 2C Wireless"
  mappings:
    # Supports both Linux input names and raw hex codes
    A: {"type": "button", "names": ["BTN_A", "0x9:1"]}
    LJ-X: {"type": "axis", "names": ["ABS_X", "0x1:30"]}
```

### Mapping Types
- **Button**: Digital on/off inputs (face buttons, triggers, bumpers)
- **Hat**: D-pad directional input treated as digital buttons
- **Axis**: Analog inputs (joysticks, analog triggers)

---

## Input Processing

### Analog Stick Processing
```python
def __process_axis_joystick(self, axis, value):
    center_point = int((axis.min + axis.max) / 2)
    
    # Apply dead zone filtering
    if abs(value - center_point) <= JOYSTICK_DEAD_ZONE:
        return
    
    # Normalize to -100 to +100 range
    mapped_value = int(interp(value, [axis.min, axis.max], [-100, 100]))
    self.__absolute_axis_motion_event(mapping, mapped_value)
```

### Hold Detection System
```python
# Configuration
TIME_UNTIL_HOLD_TRIGGERED = 0.3  # Initial hold delay
TIME_BETWEEN_HOLD_TRIGGERS = 0.1  # Repeat rate

# Implementation tracks press time and generates hold events
def __process_digital_hold(self):
    for mapping, state in self.__button_hold_states.items():
        elapsed = time.monotonic() - state["lastPressed"]
        
        if elapsed >= TIME_UNTIL_HOLD_TRIGGERED and not state["pressedBefore"]:
            # First hold trigger
            state["pressedBefore"] = True
            self.__button_hold_event(mapping)
        elif elapsed >= TIME_BETWEEN_HOLD_TRIGGERS and state["pressedBefore"]:
            # Repeated hold triggers
            self.__button_hold_event(mapping)
```

### Dead Zone Filtering
- **Purpose**: Eliminates stick drift and unintended inputs near center
- **Implementation**: Configurable dead zone radius around stick center
- **Benefits**: Precise control with elimination of noise

---

## Configuration System

### Controller Configuration Structure
```yaml
controller:
  joystickDeadZone: 10                    # Dead zone radius
  timeUntilHoldTriggeredSec: 0.3         # Hold detection delay  
  timeBetweenHoldTriggerSec: 0.1         # Hold repeat rate
  triggerPressThreshold: 0.8             # Analog trigger threshold
  
  configs:
    - displayName: "Human-readable name"
      deviceName: "Exact Pyglet device name"
      mappings:
        # Logical name: hardware mapping
        A: {"type": "button", "names": ["BTN_A"]}
        LJ-X: {"type": "axis", "names": ["ABS_X"]}
```

### Adding New Controllers
1. **Detect Device Name**: Use Pyglet to identify exact device string
2. **Map Controls**: Create mapping for each button/axis/hat
3. **Test Configuration**: Verify all inputs work correctly
4. **Add to Config**: Include in controller configs array

---

## Integration with Core Systems

### InputMapper Integration
```python
# Controller events → InputMapper actions
if isinstance(event, ButtonDown):
    input_mapper.digital_input(event.button)        # "A" → "ARM"
elif isinstance(event, ButtonHold):
    input_mapper.digital_input_hold(event.button)   # Hold "1" → Repeat "GAIN_DOWN"
elif isinstance(event, AbsoluteAxisMotion):
    input_mapper.analogue_input(event.axis, event.value)  # "LJ-X" → Surge control
```

### Event System Integration
```python
# Connection status events
event_dispatcher.dispatch("controller/connected", device_name)
event_dispatcher.dispatch("controller/disconnected")

# TTS feedback
TTS.attach_to_event(CONTROLLER_CONNECTED_LINE, "controller/connected")
TTS.attach_to_event(CONTROLLER_DISCONNECTED_LINE, "controller/disconnected")
```

### Module Manager Integration
- **Initialization Order**: Priority 100 (after core systems, before high-level modules)
- **Health Monitoring**: `status_ok()` checks daemon process health
- **Graceful Shutdown**: Properly terminates daemon process and cleans up resources

---

## Technical Implementation

### Process Architecture

**Input Processing Flow:**
```
1. User Input
   │
   ▼
2. Physical Controller (Button Press/Stick Movement)
   │
   ▼ 
3. Pyglet Input System (Raw Hardware Events)
   │
   ▼
4. ControllerDaemon Process (Event Processing & Mapping)
   │
   ▼
5. Event Queue (Multiprocessing Communication)
   │
   ▼
6. ControllerInput Module (Main Loop Processing)
   │
   ▼
7. InputMapper (Action Translation)
   │
   ▼
8. Core Systems (Event Dispatch & Request Handling)
```

**Key Benefits:**
- Process isolation prevents input blocking
- Reliable inter-process communication via queues
- Automatic error recovery and reconnection

### Error Handling & Recovery
- **Process Monitoring**: Main module monitors daemon health via `is_alive()`
- **Connection Recovery**: Automatic reconnection on device disconnect/reconnect
- **Queue Management**: Non-blocking queue operations with overflow protection
- **Graceful Degradation**: System continues functioning without controller input

### Performance Considerations
- **Process Isolation**: Input processing doesn't block main application
- **Dead Zone Filtering**: Reduces unnecessary event generation
- **Event Queuing**: Efficient inter-process communication
- **Callback Registration**: Direct Pyglet callbacks minimize processing overhead

---

## Usage Examples

### Basic Controller Setup
```python
from hydranav.controller_input import ControllerInput

# Module automatically initializes in module manager
# No manual setup required - plug and play operation

# Check controller status
if controller_input.status_ok():
    print("Controller daemon running")
```

### Custom Controller Configuration
```yaml
# Add to config.yaml
controller:
  configs:
    - displayName: "Custom Controller"
      deviceName: "My Custom Device Name"
      mappings:
        # Map controller inputs to logical actions
        A: {"type": "button", "names": ["BTN_SOUTH"]}
        START: {"type": "button", "names": ["BTN_START"]}
        LJ-X: {"type": "axis", "names": ["ABS_X"]}
        UP: {"type": "hat", "names": ["ABS_HAT0Y"], "onValue": -1}
```

### Event Monitoring
```python
from hydranav.core import event_dispatcher

def on_controller_connected(device_name):
    print(f"Controller connected: {device_name}")

def on_controller_disconnected(_):
    print("Controller disconnected")

event_dispatcher.subscribe("controller/connected", on_controller_connected)
event_dispatcher.subscribe("controller/disconnected", on_controller_disconnected)
```

### Input Action Mapping
```yaml
# In config.yaml inputMapper section
inputMapper:
  mappings:
    - name: "rov-control"
      # Controller buttons → ROV actions
      A: "ARM"                    # A button arms the vehicle
      B: "DISARM"                 # B button disarms
      R1: "GRIPPER_JAW_CLOSE"     # Right bumper closes gripper
      L1: "GRIPPER_JAW_OPEN"      # Left bumper opens gripper
      LJ-X: "SURGE"               # Left stick X-axis for forward/backward
      LJ-Y: "HEAVE"               # Left stick Y-axis for up/down
      RJ-X: "YAW"                 # Right stick X-axis for rotation
```

The controller input module provides robust, responsive gamepad support that seamlessly integrates with HydraNav's action mapping system, enabling intuitive underwater vehicle control through familiar gaming controllers.

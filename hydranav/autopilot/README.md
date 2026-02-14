# HydraNav Autopilot Module (DEPRECATED)

⚠️ **DEPRECATED MODULE - REFERENCE ONLY** ⚠️

The `autopilot` module is currently **deprecated** and exists solely as a reference for future development. This module previously provided MAVLink-based communication with Pixhawk autopilots for underwater vehicle control, but was retired due to critical stability issues with its underlying dependencies.

## ⚠️ Deprecation Notice

### The Problem: Pygame-CE/SDL2 Critical Failure

What stunted the development of this autopilot module was a critical **unrecoverable segmentation fault** in the SDL2 library used by pygame-ce in the **controller input system**. This critical issue:

- Caused the **controller process to crash**, resulting in **complete loss of control ability**
- Was **unrecoverable** and required full system restart
- Took **over 4 months** of debugging to identify the root cause
- Led to this autopilot module being **isolated and suspected as flawed** during the debugging phase
- Made the entire system unreliable for competition and real-world operations

**Important**: The failure was in pygame-ce (controller input), not in this autopilot module itself, but the debugging process led to this module being deprecated as one of the first suspected components.

### Impact on Development

This failure was a major setback that taught us:
- Never assume any dependency is "bulletproof"
- The importance of having fallback systems
- Critical evaluation of third-party library stability
- The need for extensive stress testing of all dependencies

### Current Status

- **Module Status**: Deprecated and non-functional
- **Usage**: Reference implementation only
- **Future Plans**: Complete rewrite with different architecture
- **Replacement**: Future module will be "much more powerful and flexible"

---

## Table of Contents

- [Technical Implementation](#technical-implementation) 
- [MAVLink Communication](#mavlink-communication)
- [Core Components](#core-components)
- [Control Systems](#control-systems)
- [Configuration System](#configuration-system)
- [Lessons Learned](#lessons-learned)

## Technical Implementation

### Core Module Structure

The autopilot module consisted of several interconnected components:

#### Main Module (`__init__.py`)
- **GCSModule Integration**: Full HydraNav module lifecycle compliance
- **Multi-Queue Communication**: Separate queues for movement, commands, and notifications
- **Event System Integration**: Connected to HydraNav's event dispatcher
- **Input Mapping**: Processed controller and keyboard inputs into movement commands

#### Daemon Process (`daemon.py`) 
- **MAVLink Connection**: UDP connection to Pixhawk autopilot
- **PWM Generation**: Conversion of movement commands to PWM signals
- **Heartbeat Management**: Connection monitoring and health checking
- **Command Processing**: Handled arming, mode changes, and gain adjustments

---

## MAVLink Communication

### Protocol Implementation
The module used PyMAVLink for communication with ArduSub-based Pixhawk autopilots:

```python
class AutopilotConnectionDaemon:
    def __init__(self):
        # UDP MAVLink connection
        self.__master = mavutil.mavlink_connection(f"udpin:{BASE_IP}:{PORT}")
    
    def send_movement(self, forward, lateral, throttle, yaw, roll):
        # Convert to PWM values (1100-1900μs)
        rc_values = [NEUTRAL_PWM] * 8
        rc_values[ControlChannels.FORWARD.value - 1] = self.__get_scaled_pwm(forward)
        # ... other channels
        
        # Send RC override command
        self.__master.mav.rc_channels_override_send(
            self.__master.target_system,
            self.__master.target_component,
            *rc_values
        )
```

### Control Channel Mapping
```python
class ControlChannels(Enum):
    PITCH = 1      # Nose up/down
    ROLL = 2       # Bank left/right  
    THROTTLE = 3   # Vertical movement
    YAW = 4        # Rotation left/right
    FORWARD = 5    # Forward/backward
    LATERAL = 6    # Strafe left/right
```

### PWM Signal Generation
- **Range**: 1100μs (full reverse) to 1900μs (full forward)
- **Neutral**: 1500μs (no movement)
- **Scaling**: Joystick input (-1.0 to 1.0) mapped to PWM range
- **Gain Control**: Multiple power levels for precise control

---

## Core Components

### Movement System (`movement.py`)
```python
class ROVMovement:
    """6-DOF movement representation"""
    def __init__(self, forward, lateral, throttle, yaw, roll):
        self.forward = forward    # Surge (forward/backward)
        self.lateral = lateral    # Sway (left/right strafe)  
        self.throttle = throttle  # Heave (up/down)
        self.yaw = yaw           # Yaw rotation
        self.roll = roll         # Roll rotation
        # Pitch controlled by dedicated channel
```

### Command System (`command.py`)
```python
class ROVCommands(Enum):
    ARM = 1                    # Enable motors
    DISARM = 0                 # Disable motors
    SYSTEM_MODE_MANUAL = 2     # Full manual control
    SYSTEM_MODE_STABILIZE = 3  # Stabilized flight mode
    GAIN_UP = 4               # Increase control sensitivity
    GAIN_DOWN = 5             # Decrease control sensitivity
```

### Notification System (`notification.py`)
Event-driven status updates:
- **VehicleConnected/Disconnected**: Connection status changes
- **Armed/Disarmed**: Motor enable/disable status
- **GainChange**: Control sensitivity level changes
- **SystemModeChanged**: Flight mode transitions

### System Modes (`enums.py`)
```python
class SystemModes(Enum):
    STABILIZATION = 0  # Auto-leveling active
    MANUAL = 19       # No stabilization assistance
    ALT_HOLD = 2      # Altitude/depth hold
    POSHOLD = 16      # Position hold (GPS/optical)
    # ... additional ArduSub modes
```

---

## Control Systems

### Input Processing Flow
```
Controller Input → Input Mapper → Autopilot Module → Movement Queue → Daemon Process → MAVLink → Pixhawk
```

### PWM Scaling Algorithm
```python
def __get_scaled_pwm(self, value: float) -> int:
    """Convert -1.0 to 1.0 input to PWM microseconds"""
    if value > 0:
        direction = Directions.POSITIVE
    elif value < 0:
        direction = Directions.NEGATIVE
    else:
        return NEUTRAL_PWM  # 1500μs
    
    # Apply current gain level
    percent = int(interp(abs(value), [0, 1.0], [0, GAIN_LEVELS[self.__gain_index]]))
    
    # Convert to PWM microseconds
    return NEUTRAL_PWM + int(percent / 100 * 400) * direction.value
```

### Gain Control System
```yaml
autopilot:
  gainLevels: [25, 40, 50, 75]  # Percentage power levels
  neutralPWM: 1500              # Neutral position (μs)
  maxForwardPWM: 1900           # Maximum forward (μs)  
  maxBackwardPWM: 1100          # Maximum reverse (μs)
```

### Heartbeat Management
```python
def run(self):
    while not self.__quit_event.is_set():
        # Send heartbeat every 0.9 seconds
        if time.monotonic() - self.__time_since_last_heartbeat >= 0.9:
            self.send_heartbeat()
            
            # Check for response
            if not self.receive_heartbeat():
                self.__notify(VehicleDisconnected())
```

---

## Configuration System

### Autopilot Configuration
```yaml
autopilot:
  port: 2000                    # UDP port for MAVLink
  maxBackwardPWM: 1100         # Full reverse PWM value
  maxForwardPWM: 1900          # Full forward PWM value  
  neutralPWM: 1500             # Neutral PWM value
  gainLevels: [25, 40, 50, 75] # Available power levels (%)
  timeoutSec: 2                # Command timeout
  sensorReadingRequestHz: 2     # Sensor polling rate
```

### Network Configuration  
```yaml
networking:
  baseIP: "0.0.0.0"           # Listen on all interfaces
  raspIP: "192.168.1.100"     # Target Pixhawk IP
```

### Input Mapping Integration
```yaml
inputMapper:
  mappings:
    - name: "rov-control"
      # Controller → Autopilot actions
      A: "ARM"                 # Arm the vehicle
      B: "DISARM"              # Disarm the vehicle
      1: "GAIN_DOWN"           # Reduce power
      3: "GAIN_UP"             # Increase power
      C: "STABILIZATION_MODE"  # Enable stabilization
      D: "MANUAL_MODE"         # Disable stabilization
```

---

## Lessons Learned

### Critical Dependency Issues
1. **Cross-Module Impact**: pygame-ce failure in controller input system affected all dependent modules
2. **Debugging Misdirection**: This autopilot module was isolated and suspected first during debugging
3. **Controller Dependency**: Loss of controller input meant complete loss of vehicle control capability  
4. **Debugging Complexity**: 4+ months to identify that the root cause was in pygame-ce, not this module
5. **System Reliability**: A single library failure in one module brought down the entire control system
6. **Competition Impact**: Unreliable controller input made the entire system unusable

### Technical Insights
1. **Process Isolation Limitations**: Even with daemon processes, controller failure eliminated all input capability
2. **Debugging Challenges**: Process isolation made it difficult to identify which module was actually failing
3. **Dependency Chain Effects**: Controller input failure cascaded to make autopilot appear broken
4. **False Positive Debugging**: This module was wrongly suspected and isolated early in debugging
5. **MAVLink Protocol**: Proved robust and suitable for underwater vehicle communication
6. **PWM Control**: Direct PWM control provided precise vehicle movement when input was available

### Development Practices
1. **Systematic Debugging**: Need better methods to identify actual failure points vs. affected systems
2. **Dependency Mapping**: Clear understanding of which modules depend on which libraries
3. **Stress Testing**: Extensive testing of all dependencies under load, especially input systems
4. **Fallback Systems**: Critical systems need backup implementations and redundant input methods
5. **Dependency Auditing**: Regular evaluation of third-party library stability across all modules
6. **Modular Design**: Better isolation to prevent cascading failures and false debugging leads

---

## Reference Usage (Historical)

### Basic Autopilot Control
```python
from hydranav.autopilot import Autopilot

# Module initialization (deprecated)
autopilot = Autopilot()

# Movement control (-1.0 to 1.0 for each axis)
autopilot.move(
    forward=0.5,    # 50% forward
    lateral=0.0,    # No strafe
    throttle=0.2,   # 20% up
    yaw=-0.3,       # 30% left turn
    roll=0.0        # No roll
)

# System commands
autopilot.arm()                    # Enable motors
autopilot.disarm()                 # Disable motors
autopilot.gain_up()                # Increase sensitivity
autopilot.flight_mode_stabilize()  # Enable auto-leveling
```

### Event Integration
```python
from hydranav.core import event_dispatcher

def on_vehicle_connected(_):
    print("Pixhawk autopilot connected")

def on_armed(_):
    print("Vehicle armed - motors enabled")

event_dispatcher.subscribe("rov/vehicle_connected", on_vehicle_connected)
event_dispatcher.subscribe("rov/armed", on_armed)
```

---

**This module serves as a reference for understanding MAVLink-based autopilot communication and the challenges faced during development. The next-generation autopilot system will incorporate lessons learned from this implementation while avoiding the critical stability issues that led to its deprecation.**

# Keyboard Input Module

The Keyboard Input module provides keyboard-based control for HydraNav operations. It enables users to control ROV functions, system operations, and navigation through keyboard shortcuts, making it an essential backup input method and development tool.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
- [Key Mapping System](#key-mapping-system)
- [Input Processing](#input-processing)
- [Integration with Input Mapper](#integration-with-input-mapper)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)

## Architecture Overview

The Keyboard Input module uses a lightweight event-driven architecture:

```
Operating System
├── Keyboard Hardware
└── Pynput Library
    │
    │ Key Events
    ▼
KeyboardInput Module
├── Keyboard Listener (pynput)
├── Key Translation (KeyboardKeys enum)
└── Input Mapper Integration
    │
    │ Formatted Events
    ▼
Input Mapper
├── Button Mapping Resolution
└── Event/Request Dispatch
    │
    │ Mapped Events
    ▼
System Modules
├── Autopilot Commands
├── Manfaloty Control
├── Admin Functions
└── System Operations
```

### Key Features

- **Global key listening**: Captures keyboard input system-wide using pynput
- **Comprehensive key support**: Function keys, letters, numbers, and special keys
- **Case sensitivity**: Distinguishes between uppercase and lowercase letters
- **Input mapper integration**: Seamless integration with the unified input mapping system
- **Non-blocking operation**: Runs in background thread without affecting main application

## Core Components

### KeyboardInput Class

The main module class that manages keyboard event processing:

```python
class KeyboardInput(GCSModule):
    def __init__(self):
        # Sets up pynput keyboard listener
        
    def __on_key_press(self, key):
        # Processes keyboard events and forwards to input mapper
        
    def status_ok(self):
        # Returns keyboard listener health status
        
    def quit(self):
        # Cleanly shuts down keyboard listener
```

**Key Features:**
- **Background listener**: Uses pynput's keyboard listener for global key capture
- **Late initialization**: `init_order()` = 100 ensures other modules are ready
- **Event filtering**: Only processes supported keys defined in KeyboardKeys enum
- **Graceful shutdown**: Proper listener cleanup on module termination

### KeyboardKeys Enum

Comprehensive enumeration of supported keyboard keys:

```python
class KeyboardKeys(Enum):
    # Function keys
    F1 = Key.f1
    F2 = Key.f2
    # ... F1-F12
    
    # Letter keys (case-sensitive)
    A_LOWER = KeyCode(char="a")
    A_UPPER = KeyCode(char="A")
    # ... Full alphabet, both cases
    
    # Number keys
    ZERO = KeyCode(char="0")
    ONE = KeyCode(char="1")
    # ... 0-9
```

**Key Categories:**
- **Function Keys**: F1 through F12 for system functions
- **Letter Keys**: Full alphabet with case distinction (A-Z, a-z)
- **Number Keys**: Digits 0-9 for numeric input
- **Extensible**: Easy to add new key categories as needed

### Key Translation System

The module includes robust key translation from pynput to internal representation:

```python
@staticmethod
def from_pynput(key_input) -> Optional["KeyboardKeys"]:
    """Convert pynput key to KeyboardKeys enum member."""
    for member in KeyboardKeys:
        if isinstance(key_input, Key) and key_input == member.value:
            return member
        if isinstance(key_input, KeyCode):
            if hasattr(key_input, "char") and hasattr(member.value, "char"):
                if key_input.char == member.value.char:
                    return member
    return None
```

## Key Mapping System

### Input Format

Keyboard inputs are prefixed with `K_` when sent to the input mapper:

```
Physical Key → KeyboardKeys Enum → Input Mapper Format
     'q'     →     Q_LOWER        →      "K_Q_LOWER"
     'Q'     →     Q_UPPER        →      "K_Q_UPPER" 
     F1      →        F1          →         "K_F1"
     '1'     →       ONE          →        "K_ONE"
```

### Configuration Integration

Keyboard mappings are configured through the main configuration system:

```yaml
# config.yaml
userInput:
  mappings:
    - name: "keyboard-controls"
      K_Q: "QUIT"                    # Q key quits application
      K_A_LOWER: "ARM"               # 'a' key arms system
      K_D_LOWER: "DISARM"            # 'd' key disarms system
      K_W_LOWER: "FORWARD"           # 'w' key moves forward
      K_S_LOWER: "BACKWARD"          # 's' key moves backward
      K_F1: "EMERGENCY_STOP"         # F1 emergency stop
      K_SPACE: "GRIPPER_JAW_OPEN"    # Space opens gripper
```

### Default Key Mappings

Common keyboard control schemes:

**ROV Movement:**
- `W/A/S/D` - Forward/Left/Backward/Right movement
- `Q/E` - Up/Down movement
- `R/F` - Roll left/right

**System Control:**
- `ESC` - Emergency stop
- `F1-F12` - System functions and shortcuts
- `SPACE` - Primary action (gripper, etc.)

**Administrative:**
- `Ctrl+Q` - Quit application
- `Ctrl+R` - Restart services
- `Ctrl+P` - Power off

## Input Processing

### Event Flow

1. **Key Detection**: Pynput listener captures system-wide key events
2. **Key Translation**: Convert pynput key objects to KeyboardKeys enum
3. **Format Generation**: Create input mapper format (`K_<KEY_NAME>`)
4. **Input Mapping**: Forward to input mapper for action resolution
5. **Event Dispatch**: Input mapper dispatches events and requests

### Processing Pipeline

```python
def __on_key_press(self, key):
    # Step 1: Translate pynput key to internal enum
    keyboard_key = KeyboardKeys.from_pynput(key)
    if keyboard_key is None:
        return  # Unsupported key, ignore
    
    # Step 2: Format for input mapper and forward
    input_mapper.digital_input(f"K_{keyboard_key.name}")
```

### Error Handling

- **Unsupported keys**: Gracefully ignored, no error thrown
- **Translation failures**: Keys not in enum are silently skipped
- **Listener errors**: Automatic restart attempts on listener failure
- **Thread safety**: Pynput handles cross-thread event processing

## Integration with Input Mapper

### Seamless Integration

The keyboard input integrates seamlessly with the existing input mapper system:

```python
# In input_mapper.py
def digital_input(self, button: str):
    # Keyboard inputs arrive as "K_<KEY_NAME>"
    # Same processing as controller buttons
    if self.__current_mapping.get(button) is None:
        return  # Not mapped
    
    # Dispatch events and requests
    event_dispatcher.dispatch(f"mapper/{self.__current_mapping[button]}")
    request_manager.request(f"mapper/{self.__current_mapping[button]}")
```

### Unified Control

Both keyboard and controller inputs use the same mapping system:

```yaml
userInput:
  mappings:
    - name: "unified-controls"
      # Controller inputs
      A: "ARM"              # Controller A button
      B: "DISARM"           # Controller B button
      # Keyboard inputs  
      K_A_LOWER: "ARM"      # 'a' key (same action)
      K_D_LOWER: "DISARM"   # 'd' key (same action)
```

## Configuration

### Module Settings

```python
# Module initialization order
@classmethod
def init_order(cls):
    return 100  # Initialize after other modules
```

### Keyboard Listener Configuration

The module uses pynput's default keyboard listener configuration:
- **Global capture**: Captures keys even when HydraNav isn't focused
- **Non-blocking**: Runs in background thread
- **Platform agnostic**: Works on Windows, macOS, and Linux

### Key Support Extension

Adding new keys is straightforward:

```python
# In keyboard_keys.py
class KeyboardKeys(Enum):
    # Add new keys here
    TAB = Key.tab
    ENTER = Key.enter
    SHIFT = Key.shift
    CTRL = Key.ctrl
    ALT = Key.alt
```

## Usage Examples

### Basic Keyboard Control Setup

```python
# Module automatically starts when initialized
keyboard_input = KeyboardInput()

# Access via module manager
from hydranav.core import module_manager
keyboard_module = module_manager.get_instance("KeyboardInput")
```

### Custom Key Mapping

```yaml
# Custom keyboard control scheme
userInput:
  mappings:
    - name: "wasd-controls"
      K_W_LOWER: "MOVE_FORWARD"
      K_A_LOWER: "MOVE_LEFT"  
      K_S_LOWER: "MOVE_BACKWARD"
      K_D_LOWER: "MOVE_RIGHT"
      K_Q_LOWER: "MOVE_UP"
      K_E_LOWER: "MOVE_DOWN"
      K_SPACE: "GRIPPER_JAW_TOGGLE"
      K_F1: "ARM"
      K_F2: "DISARM"
      K_ESC: "EMERGENCY_STOP"
```

### Development and Testing

Keyboard input is particularly useful for development:

```python
# Quick testing without controller
# Press keys to trigger ROV functions
# F1 = ARM, F2 = DISARM, WASD = movement, etc.

# In development environment
keyboard_mappings = {
    "K_F1": "ARM",
    "K_F2": "DISARM", 
    "K_F3": "CALIBRATE_JOYSTICKS",
    "K_F4": "RESET_MOTORS",
    "K_F5": "RESTART_ARDUINO",
}
```

### Emergency Controls

Critical functions can be mapped to easily accessible keys:

```yaml
# Emergency keyboard controls
userInput:
  mappings:
    - name: "emergency-keys"
      K_ESC: "EMERGENCY_STOP"      # Immediate stop
      K_F12: "SURFACE_IMMEDIATELY"  # Emergency surface
      K_SPACE: "DROP_WEIGHTS"      # Emergency weight release
```

## Architecture Benefits

### Backup Input Method
- **Controller failure**: Keyboard provides backup control method
- **Development**: Easy testing without physical controller
- **Accessibility**: Alternative input for users with different needs

### Development Efficiency
- **Quick testing**: Rapid function testing during development
- **Debug commands**: Easy access to debug and diagnostic functions
- **System control**: Quick access to system management functions

### User Experience
- **Familiar controls**: Standard WASD gaming controls
- **Customizable**: Users can define their own key mappings
- **Consistent**: Same mapping system as controller inputs

### Technical Advantages
- **Global capture**: Works regardless of application focus
- **Low overhead**: Minimal CPU and memory usage
- **Platform independent**: Works across different operating systems
- **Thread safe**: Proper concurrent event handling

## Technical Notes

### Platform Considerations
- **Linux**: Requires proper permissions for global key capture
- **Windows**: May trigger UAC prompts for global keyboard access
- **macOS**: Requires accessibility permissions for system-wide capture

### Performance Characteristics
- **Memory usage**: Minimal - single listener thread and enum lookups
- **CPU overhead**: Very low - event-driven processing only
- **Latency**: Near-instantaneous key response (< 1ms)

### Security Implications
- **Keylogger concerns**: Uses system-wide key capture (legitimate for ROV control)
- **Permission requirements**: May need elevated privileges on some systems
- **Privacy**: Only processes keys defined in KeyboardKeys enum

### Integration Notes
- **Module loading**: Currently commented out in main application (can be enabled)
- **Event priority**: Keyboard events processed after controller events
- **Mapping conflicts**: Keyboard and controller can map to same functions safely
- **State independence**: No persistent state between key presses

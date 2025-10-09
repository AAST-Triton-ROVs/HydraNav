# Web GUI Module

The Web GUI module provides a modern web-based interface for HydraNav using NiceGUI and FastAPI. It creates a responsive, dark-themed control interface that runs in a separate process and serves pages for different system modules.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
- [Module Integration](#module-integration)
- [Page Generation](#page-generation)
- [Utility Functions](#utility-functions)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)

## Architecture Overview

The Web GUI operates as a multiprocess-based web server that:

1. **Runs in a separate process** to isolate web server operations from the main application
2. **Auto-discovers modules** that implement the `HasWebGUI` interface
3. **Dynamically generates pages** for each web-enabled module
4. **Provides consistent navigation** with a footer-based menu system
5. **Serves on a configurable network interface** for remote access

### Process Architecture

```
Main Process (HydraNav)
└── WebGUI Module
    └── Server Process (multiprocessing.Process)
        ├── FastAPI Application
        ├── NiceGUI Integration
        └── Uvicorn ASGI Server
```

## Core Components

### WebGUI Class

The main module class that inherits from `GCSModule` and `Updatable`:

```python
class WebGUI(GCSModule, Updatable):
    def __init__(self):
        # Starts web server in separate process
        
    def __run_server(self):
        # Generates UI and starts FastAPI/Uvicorn server
        
    def quit(self):
        # Terminates and joins server process
        
    def status_ok(self) -> bool:
        # Returns server process health status
```

**Key Features:**
- **Process isolation**: Web server runs independently of main application
- **Late initialization**: Uses `init_order()` = 99 to start after other modules
- **Graceful shutdown**: Properly terminates server process on exit
- **Health monitoring**: Tracks server process status

### HasWebGUI Interface

Modules must implement this abstract class to appear in the web interface:

```python
class HasWebGUI(ABC):
    @abstractmethod
    def webgui_contents(self) -> ui.element:
        # Returns NiceGUI elements for the module's page
        
    @abstractmethod
    def webgui_icon_name(self) -> str:
        # Returns icon name for navigation buttons
```

## Module Integration

### Auto-Discovery Process

The web GUI automatically finds and integrates modules through:

1. **Module filtering**: `module_manager.filter_modules_by_parent(HasWebGUI)`
2. **Dynamic page creation**: Each module gets its own route
3. **Navigation generation**: Footer buttons are created automatically

### Page Structure

Each module page follows a consistent structure:

```
┌─────────────────────────────────────┐
│           Module Content            │
│        (module.webgui_contents())   │
│                                     │
│                                     │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│  [Home] [Module1] [Module2] [...]   │ ← Footer Navigation
└─────────────────────────────────────┘
```

## Page Generation

### Home Page

The root page (`/`) displays:
- **HydraNav title** with large, bold styling
- **Instructions** for using the navigation
- **Network information** showing alternative access URLs
- **Footer navigation** to all available modules

### Module Pages

Each module gets a dedicated page at `/{module-name}`:
- **Custom content** from `module.webgui_contents()`
- **Consistent footer** with navigation to all modules
- **Responsive layout** using NiceGUI's column system

### URL Generation

Module names are converted from CamelCase to URL-friendly formats:

```python
"PiTelemetry" → "/pi-telemetry"  # Route
"PiTelemetry" → "Pi Telemetry"   # Display name
```

## Utility Functions

### String Conversion

**`_camel_to_normal_case(name: str) -> str`**
- Converts `CamelCase` to `Normal Case`
- Used for display names in buttons and titles

**`_camel_to_dash_case(text: str) -> str`**
- Converts `CamelCase` to `dash-case`
- Used for URL paths and routing

### Network Utilities

**`_get_ip_address(interface) -> Optional[str]`**
- Retrieves IPv4 address of specified network interface
- Used to display alternative access URLs
- Handles interface detection errors gracefully

### UI Generation

**`_generate_footer_button(module)`**
- Creates navigation buttons for each module
- Includes module icon and proper routing

**`_create_module_page(module)`**
- Dynamically creates pages for web-enabled modules
- Sets up routing and page structure

## Configuration

### Server Settings

```python
SERVER_IP = "0.0.0.0"           # Bind to all interfaces
SERVER_PORT = 4000              # Web server port
WEBPAGE_TITLE = "HydraNav"      # Browser tab title
DEFAULT_WIRELESS_INTERFACE = "wlo1"  # For IP detection
```

### NiceGUI Configuration

```python
ui.run_with(
    app,
    title="HydraNav",
    dark=True,              # Dark theme enabled
)
```

### Uvicorn Configuration

```python
uvicorn.run(
    app,
    port=SERVER_PORT,
    host=SERVER_IP,
)
```

## Usage Examples

### Adding Web Interface to a Module

1. **Inherit from HasWebGUI**:
```python
from hydranav.core.has_webgui import HasWebGUI
from nicegui import ui

class MyModule(GCSModule, HasWebGUI):
    def webgui_contents(self) -> ui.element:
        with ui.column():
            ui.label("My Module Dashboard")
            ui.button("Action", on_click=self.do_something)
            return ui.column()
    
    def webgui_icon_name(self) -> str:
        return "dashboard"  # Material Icons name
```

2. **The module automatically appears** in the web interface navigation

### Creating Interactive Elements

```python
def webgui_contents(self) -> ui.element:
    with ui.column():
        # Status display
        ui.label("System Status: Online").classes("text-green-500")
        
        # Interactive controls
        ui.button("Start Service", on_click=self.start_service)
        ui.button("Stop Service", on_click=self.stop_service)
        
        # Real-time data (would need periodic updates)
        self.status_label = ui.label("Waiting for data...")
        
        return ui.column()
```

### Styling with Tailwind CSS

NiceGUI supports Tailwind CSS classes:

```python
ui.label("Important Message").classes("text-red-500 font-bold text-xl")
ui.column().classes("w-full max-w-md mx-auto p-4 bg-gray-800 rounded-lg")
```

## Architecture Benefits

### Process Separation
- **Isolation**: Web server crashes don't affect main application
- **Performance**: Web operations don't block main event loop
- **Security**: Web interface runs with limited access to core systems

### Modular Design
- **Auto-discovery**: New modules automatically appear in interface
- **Consistent UX**: All pages follow same navigation pattern
- **Extensibility**: Easy to add new interface components

### Network Accessibility
- **Remote access**: Interface available from any device on network
- **Mobile friendly**: Responsive design works on phones/tablets
- **Multiple interfaces**: Displays alternative access URLs

## Technical Notes

### Process Communication
- Web GUI runs in isolation - limited communication with main process
- Real-time updates require careful design (periodic polling, websockets, etc.)
- Module state should be exposed through appropriate interfaces

### Performance Considerations
- Server starts after other modules (init_order = 99)
- Uses production ASGI server (Uvicorn) for better performance
- Dark theme reduces power consumption on OLED displays

### Error Handling
- Network interface detection handles missing interfaces gracefully
- Server process health monitoring for automatic restarts
- Graceful shutdown prevents orphaned processes

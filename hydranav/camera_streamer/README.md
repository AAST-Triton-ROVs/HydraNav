# HydraNav Camera Streamer Module

The `camera_streamer` module provides real-time video streaming capabilities for HydraNav, enabling operators to view multiple camera feeds from the underwater vehicle simultaneously. This module handles TCP-based video reception, frame processing, and both desktop display and web-based viewing of camera feeds.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
  - [CameraStreamer (Main Module)](#camerastreamer-main-module)
  - [CameraDaemon (Network Handler)](#cameradaemon-network-handler)
- [Video Processing Pipeline](#video-processing-pipeline)
- [Multi-Camera Support](#multi-camera-support)
- [Display Systems](#display-systems)
- [Configuration System](#configuration-system)
- [Technical Implementation](#technical-implementation)
- [Usage Examples](#usage-examples)

## Architecture Overview

The camera streamer uses a multi-process architecture where dedicated daemon processes handle network communication and video decoding, while the main module manages display and user interface integration.

```
Data Flow:
Camera → Pi Server → TCP Stream → CameraDaemon → Frame Queue → Display Grid
```

The system supports up to 4 simultaneous camera feeds, each handled by its own daemon process for optimal performance and isolation.

---

## Core Components

### CameraStreamer (Main Module)

**File:** `__init__.py`

The main orchestrator that manages multiple camera daemons, processes incoming frames, and provides both desktop and web-based viewing interfaces.

#### Architecture
- **Multi-Process Management**: Spawns and monitors dedicated camera daemon processes
- **Frame Aggregation**: Collects frames from all camera daemons via queues
- **Grid Display**: Arranges multiple camera feeds in a unified layout
- **Web Integration**: Provides NiceGUI interface for camera control
- **Real-time Processing**: Handles frame timeout and offline detection

#### Core Responsibilities
```python
class CameraStreamer(GCSModule, Updatable, HasWebGUI):
    def update(self):
        # Collect frames from all camera daemons
        frames = {}
        for i, data_queue in self.__data_queues.items():
            try:
                frame = data_queue.get(block=False)
                frames[i] = frame
            except queue.Empty:
                # Handle camera offline timeout
                if self.__is_camera_offline(i):
                    frames[i] = CAMERA_OFFLINE_FRAME
        
        # Create grid display and show
        self.__create_grid_display(frames)
```

#### Key Features
- **Multi-Camera Management**: Handles 1-4 camera feeds simultaneously
- **Offline Detection**: Shows "Camera Offline" when feeds are lost
- **Grid Layout**: Automatic 2x2 arrangement of camera feeds
- **Real-time Display**: OpenCV-based fullscreen viewing
- **Web Controls**: Browser-based camera enhancement and rotation controls

---

### CameraDaemon (Network Handler)

**File:** `camera_daemon.py`

Dedicated processes that handle TCP connections to Raspberry Pi camera servers, decode video frames, and apply real-time processing.

#### Architecture
- **Process Isolation**: Each camera runs in its own process for stability
- **TCP Client**: Maintains persistent connections to Pi camera servers
- **Frame Protocol**: Handles length-prefixed binary frame protocol
- **Real-time Processing**: Applies enhancement and rotation transformations
- **Queue Communication**: Sends processed frames to main process

#### Network Protocol
```python
def receive_frame(self):
    # 1. Receive 4-byte length header
    packed_msg_size = self.__recv_exact(I_SIZE)
    msg_size = struct.unpack("!I", packed_msg_size)[0]
    
    # 2. Receive frame data of specified length
    frame_data = self.__recv_exact(msg_size)
    
    # 3. Decode JPEG frame
    nparr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # 4. Resize to target dimensions
    frame = cv2.resize(frame, (TARGET_WIDTH, TARGET_HEIGHT))
```

#### Frame Processing Pipeline
1. **Network Reception**: Receive compressed JPEG frames via TCP
2. **Decoding**: Convert JPEG bytes to OpenCV frame format
3. **Resizing**: Standardize to configured dimensions (960x540)
4. **Enhancement** (Optional): Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
5. **Rotation** (Optional): 180-degree rotation for inverted cameras
6. **Queue Delivery**: Send processed frame to main process

#### Enhancement Processing
```python
if self.__use_enhancement.is_set():
    # Convert BGR to LAB color space for better contrast enhancement
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to luminance channel only
    enhanced_l = CLAHE.apply(l)
    
    # Merge channels and convert back to BGR
    lab = cv2.merge((enhanced_l, a, b))
    frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
```

---

## Video Processing Pipeline

### Frame Reception Protocol
The system uses a length-prefixed binary protocol for reliable frame transmission:

```
┌─────────────────┬─────────────────────────────────────┐
│ 4 bytes         │ Variable length                     │
│ Frame Size      │ JPEG Frame Data                     │
│ (Big Endian)    │                                     │
└─────────────────┴─────────────────────────────────────┘
```

### Processing Stages
1. **Network Layer**: TCP connection to Pi camera servers (ports 2031-2034)
2. **Protocol Handling**: Length-prefixed frame reception with error recovery
3. **Frame Decoding**: JPEG decompression to OpenCV format
4. **Standardization**: Resize all frames to uniform dimensions
5. **Enhancement**: Optional CLAHE contrast enhancement for underwater visibility
6. **Transformation**: Optional 180° rotation for inverted camera mounting
7. **Queue Distribution**: Non-blocking frame delivery to main process

### Frame Queue Management
```python
try:
    self.__data_queue.put(frame, block=False)
except queue.Full:
    # Replace old frame with new one to prevent lag
    try:
        self.__data_queue.get(block=False)
        self.__data_queue.put(frame, block=False)
    except queue.Empty:
        continue
```

---

## Multi-Camera Support

### Camera Configuration
```yaml
cameraStreamer:
  basePort: 2030        # Starting port (2031, 2032, 2033, 2034)
  targetWidth: 960      # Standardized frame width
  targetHeight: 540     # Standardized frame height  
  maxCameraCount: 4     # Maximum simultaneous cameras
  FPS: 30              # Target frame rate
```

### Port Assignment
- **Camera 1**: Port 2031
- **Camera 2**: Port 2032  
- **Camera 3**: Port 2033
- **Camera 4**: Port 2034

### Grid Layout System
```python
def create_grid_layout(self, frames):
    columns = 2
    rows = (len(frames) + columns - 1) // columns
    
    grid_image = np.zeros((
        rows * TARGET_HEIGHT,
        columns * TARGET_WIDTH, 
        3
    ), dtype=np.uint8)
    
    for i, frame in enumerate(frames.values()):
        row = i // columns
        col = i % columns
        grid_image[
            row * TARGET_HEIGHT:(row + 1) * TARGET_HEIGHT,
            col * TARGET_WIDTH:(col + 1) * TARGET_WIDTH
        ] = frame
```

### Offline Detection
- **Timeout Mechanism**: 2-second timeout for camera offline detection
- **Offline Frame**: Displays "Camera Offline" message when feed is lost
- **Automatic Recovery**: Resumes display when camera reconnects
- **Per-Camera Status**: Individual offline tracking for each camera

---

## Display Systems

### Desktop Display (OpenCV)
```python
# Fullscreen OpenCV window for operator viewing
cv2.namedWindow("HydraNav Cameras", cv2.WINDOW_NORMAL)
cv2.setWindowProperty(
    "HydraNav Cameras",
    cv2.WND_PROP_FULLSCREEN, 
    cv2.WINDOW_FULLSCREEN
)

# Display grid of all camera feeds
cv2.imshow("HydraNav Cameras", grid_image)
```

**Features:**
- Fullscreen display for maximum visibility
- Real-time grid layout of all active cameras
- Keyboard shortcut ('q') for quick exit
- Automatic scaling and arrangement

### Web Interface (NiceGUI)
```python
def webgui_contents(self):
    with ui.card():
        ui.label("Camera Streamer").classes("text-4xl font-extrabold")
        
        for i in range(1, MAX_CAMERA_COUNT + 1):
            with ui.row():
                ui.label(f"Camera {i}")
                ui.button("Enhance", on_click=lambda: toggle_enhancement(i))
                ui.button("Rotate 180", on_click=lambda: toggle_rotation(i))
```

**Features:**
- Per-camera enhancement controls
- Individual rotation toggles
- Real-time control without interrupting video
- Responsive web-based interface

---

## Configuration System

### Camera Streamer Settings
```yaml
cameraStreamer:
  basePort: 2030          # Base port for camera connections
  targetWidth: 960        # Standardized frame width
  targetHeight: 540       # Standardized frame height
  maxCameraCount: 4       # Maximum number of cameras
  FPS: 30                # Target frames per second
```

### Network Configuration
```yaml
networking:
  raspIP: "192.168.1.100" # Raspberry Pi IP address
  socketTimeout: 1        # Socket timeout in seconds
  retryDelaySec: 2       # Retry delay on connection failure
```

### Processing Options
- **Enhancement**: CLAHE contrast enhancement for underwater visibility
- **Rotation**: 180-degree rotation for inverted camera mounting
- **Timeout**: Camera offline detection threshold
- **Queue Size**: Frame buffer management (size 1 for low latency)

---

## Technical Implementation

### Process Architecture
```
Camera Server (Pi) → TCP Stream → CameraDaemon Process → Frame Queue → Main Process → Display
```

### Connection Management
- **Automatic Reconnection**: Daemons automatically reconnect on connection loss
- **Error Recovery**: Graceful handling of network interruptions
- **Process Isolation**: Camera failures don't affect other cameras or main system
- **Resource Cleanup**: Proper socket and process cleanup on shutdown

### Frame Synchronization
- **Non-blocking Queues**: Prevents camera lag from affecting system
- **Frame Dropping**: Discards old frames to maintain real-time performance
- **Timeout Handling**: Detects and handles camera offline conditions
- **Grid Updates**: Smooth integration of available camera feeds

### Performance Optimization
- **Process Isolation**: Each camera daemon runs independently
- **Frame Buffering**: Minimal buffering (1 frame) for low latency
- **Efficient Processing**: Direct OpenCV operations without unnecessary copies
- **Memory Management**: Automatic cleanup of processed frames

---

## Usage Examples

### Basic Camera Streaming
```python
from hydranav.camera_streamer import CameraStreamer

# Module automatically initializes with configured cameras
# Cameras connect to Pi servers on ports 2031-2034

# Check system status
if camera_streamer.status_ok():
    print("All camera daemons running")
else:
    print("Some camera daemons failed")
```

### Web Interface Control
```python
# Enhancement toggle (improves underwater visibility)
camera_streamer.toggle_enhancement(camera_number=1)

# Rotation toggle (for inverted cameras)  
camera_streamer.toggle_rotation(camera_number=2)
```

### Configuration Example
```yaml
# config.yaml
cameraStreamer:
  basePort: 2030
  targetWidth: 1280     # Higher resolution
  targetHeight: 720
  maxCameraCount: 2     # Only 2 cameras
  FPS: 60              # Higher frame rate

networking:
  raspIP: "10.0.0.100"  # Different network setup
```

### Raspberry Pi Camera Server
The camera streamer expects corresponding camera servers running on the Raspberry Pi:

```python
# Example Pi-side camera server structure
def camera_server(port, camera_index):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(1)
    
    camera = cv2.VideoCapture(camera_index)
    
    while True:
        client_socket, addr = server_socket.accept()
        
        while True:
            ret, frame = camera.read()
            if ret:
                # Encode frame as JPEG
                _, jpeg_frame = cv2.imencode('.jpg', frame)
                frame_data = jpeg_frame.tobytes()
                
                # Send length-prefixed frame
                client_socket.send(struct.pack('!I', len(frame_data)))
                client_socket.send(frame_data)
```

### Advanced Features
- **Multi-Camera Synchronization**: All cameras displayed in unified grid
- **Real-time Enhancement**: CLAHE processing for better underwater visibility  
- **Flexible Layout**: Automatic grid arrangement based on active cameras
- **Web Control Integration**: Browser-based camera controls in HydraNav GUI
- **Fault Tolerance**: Individual camera failures don't affect system operation

The camera streamer module provides comprehensive video streaming capabilities that integrate seamlessly with HydraNav's modular architecture, enabling reliable multi-camera monitoring for underwater vehicle operations.

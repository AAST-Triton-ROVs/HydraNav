# HydraNav

Revolutionary GCS from TritonROVs

## Documentation

To access documentation run 
```bash
./open-docs.sh
```
Then open `localhost:8000`

| Port | Service |
|------|---------|
| 2000 | mavproxy-router |
| 2005 | gripper-daemon |
| 2010 | telemetry-daemon |
| 2015 | admin-daemon |

# TODO:
- [ ] Add new ROV motor control backend

    - Use MANUAL_CONTROL and send joystick values
    - add command to change control backend on the fly

- [ ] Add toggle function for system state and flight mode
- [ ] Support controller double pressing buttons
- [ ] Set autopilot parameters:

    - FRAME_CONFIG
    - FS_LEAK_ENABLE
    - FS_PILOT_INPUT
    - FS_PILOT_TIMEOUT
    - LEAK1_PIN
    - LEAK1_LOGIC
    - LOG_BACKEND_TYPE
- [ ] Create testing infrastructure
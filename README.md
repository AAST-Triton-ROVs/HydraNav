# HydraNav

Revolutionary GCS from TritonROVs

## Documentation

To access documentation run

```bash
./open-docs.sh
```

Then open `localhost:8000`

| Port | Service          |
| ---- | ---------------- |
| 2000 | mavproxy-router  |
| 2005 | gripper-daemon   |
| 2010 | telemetry-daemon |
| 2015 | admin-daemon     |

# TODO:

- [ ] Add new ROV motor control backend

  - Use MANUAL_CONTROL and send joystick values

- [ ] Support controller double pressing buttons
- [ ] Set autopilot parameters:

  - FRAME_CONFIG
  - FS_LEAK_ENABLE
  - FS_PILOT_INPUT
  - FS_PILOT_TIMEOUT
  - LEAK1_PIN
  - LEAK1_LOGIC
  - LOG_BACKEND_TYPE

- [ ] request senor readings

  - SCALED_IMU
  - SCALED_PRESSURE

- [x] Implement RequestManager

- [ ] Create testing infrastructure

- [ ] Implement CentralControl module for dynamically loading/unloading modules and gracefully shutting down
- [ ] Migrate to use Multiprocessing instead of Multithreading to sidestep te GIL

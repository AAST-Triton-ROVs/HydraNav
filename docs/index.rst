Welcome to the documentation of HydraNav
=========================================

HydraNav is a revolutionary Ground Control System (GCS) engineered for underwater ROV operations. Designed with modularity and real-time responsiveness in mind, the code base integrates core functionalities ranging from autopilot control and telemetry data acquisition to comprehensive user input management and administrative oversight.

Overview of Core Functionality
-------------------------------

HydraNav’s architecture is built around an event-driven framework that seamlessly interconnects its various components:

- **Autopilot Module**: 
  The autopilot module manages connection with the Pixhawk autopilot. It manages movement, gain adjustment, arming/disarming, setting system modes and setting autopilot parameters.

- **Telemetry and Data Collection**: 
  The telemetry subsystem utilizes UDP-based communication to receive and parse critical system data such as CPU usage, sensor readings, and vehicle status.

- **User Input Handling**: 
  Handles controller connectivity, joystick movements and button presses. It also handles keyboard input events.

- **Administrative Tools**: 
  The admin daemon enables remote system management by transmitting critical commands such as reboot, poweroff, and process restarts.

- **Notification System**: 
  Integrated with the event dispatcher, audio notifications alert the pilot to significant state changes like vehicle connectivity, command acknowledgments, or system mode updates.

Design and Documentation
--------------------------

HydraNav is structured to promote scalability and maintainability:
  
- **Modularity and Event-Driven Design**:  
  The architecture leverages an internal event dispatcher, allowing modules such as autopilot, telemetry, and notifier to communicate efficiently. This structure supports easy integration of new functionalities.

- **Multithreading and Real-Time Processing**:  
  Critical components run as daemon threads to ensure that high-volume data streams and control loops operate concurrently without bottlenecks, thereby ensuring smooth performance even under demanding conditions.

.. toctree::
   :maxdepth: 5
   :caption: API Documentation

   source/admin
   source/autopilot
   source/gui
   source/manfaloty
   source/notifier
   source/pi_telemetry
   source/user_input
   source/core

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

import os
from pathlib import Path
from typing import Any
import jsonschema
import yaml
import platformdirs
from hydranav.core.logger import LoggerMixin

APP_NAME = "HydraNav"
CONFIG_FILE_PATH = Path(platformdirs.user_config_dir(appname=APP_NAME), "config.yaml")


DEFAULT_CONFIG = {
    "networking": {
        "baseIP": "0.0.0.0",
        "raspIP": "192.168.1.100",
        "retryDelaySec": 2,
        "socketTimeout": 1,
    },
    "tts": {
        "assetsPath": "./assets/audio",
        "piperModel": "en_GB-jenny_dioco-medium",
        "genTimeout": 1,
    },
    "autopilot": {
        "port": 2000,
        "maxBackwardPWM": 1100,
        "maxForwardPWM": 1900,
        "neutralPWM": 1500,
        "gainLevels": [25, 40, 50, 75],
        "timeoutSec": 2,
        "sensorReadingRequestHz": 2,
    },
    "inputMapper": {
        "mappings": [
            {
                "name": "zizo-style",
                "R": "ARM",
                "L": "DISARM",
                "1": "GAIN_DOWN",
                "2": "ROLL_RIGHT",
                "3": "GAIN_UP",
                "4": "ROLL_LEFT",
                "C": "STABILIZATION_MODE",
                "D": "MANUAL_MODE",
                "M": "CALIBRATE_JOYSTICKS",
                "L4": "GRIPPER_ROLL_LEFT",
                "R4": "GRIPPER_ROLL_RIGHT",
                "R2": "GRIPPER_PITCH_UP",
                "L2": "GRIPPER_PITCH_DOWN",
                "R1": "GRIPPER_JAW_OPEN",
                "L1": "GRIPPER_JAW_CLOSE",
                "K_Q_LOWER": "QUIT",
                "K_ONE": "PUMP_ON",
                "K_TWO": "PUMP_OFF",
            },
        ],
    },
    "manfaloty": {
        "port": 2005,
        "jawsBurstFreq": 4,
    },
    "piTelemetry": {"port": 2010},
    "piAdmin": {"port": 2015},
    "controller": {
        "joystickDeadZone": 10,
        "timeUntilHoldTriggeredSec": 0.3,
        "timeBetweenHoldTriggerSec": 0.1,
        "triggerPressThreshold": 0.8,
        "configs": [
            {
                "displayName": "DualSense Wired",
                "deviceName": "Sony Interactive Entertainment DualSense Wireless Controller",
                "mappings": {
                    "1": {"type": "hat", "names": ["ABS_HAT0Y"], "onValue": 1},
                    "2": {"type": "hat", "names": ["ABS_HAT0X"], "onValue": 1},
                    "3": {"type": "hat", "names": ["ABS_HAT0Y"], "onValue": -1},
                    "4": {"type": "hat", "names": ["ABS_HAT0X"], "onValue": -1},
                    "A": {"type": "button", "names": ["BTN_A"]},
                    "B": {"type": "button", "names": ["BTN_B"]},
                    "C": {"type": "button", "names": ["BTN_X"]},
                    "D": {"type": "button", "names": ["BTN_Y"]},
                    "L": {"type": "button", "names": ["BTN_SELECT"]},
                    "M": {"type": "button", "names": ["BTN_MODE"]},
                    "R": {"type": "button", "names": ["BTN_START"]},
                    "L1": {"type": "button", "names": ["BTN_TL"]},
                    "L2": {"type": "button", "names": ["BTN_TL2"]},
                    "L3": {"type": "button", "names": ["BTN_THUMBL"]},
                    "R1": {"type": "button", "names": ["BTN_TR"]},
                    "R2": {"type": "button", "names": ["BTN_TR2"]},
                    "R3": {"type": "button", "names": ["BTN_THUMBR"]},
                    "LJ-X": {"type": "axis", "names": ["ABS_X"]},
                    "LJ-Y": {"type": "axis", "names": ["ABS_Y"]},
                    "RJ-X": {"type": "axis", "names": ["ABS_RX"]},
                    "RJ-Y": {"type": "axis", "names": ["ABS_RY"]},
                    # "L4": {"type": "button", "mapping": 2},
                    # "R4": {"type": "button", "mapping": 5},
                },
            },
            {
                "displayName": "8BitDo Ultimate 2C Bluetooth",
                "deviceName": "8BitDo Ultimate 2C Wireless",
                "mappings": {
                    "1": {"type": "hat", "names": ["ABS_HAT0Y"], "onValue": 1},
                    "2": {"type": "hat", "names": ["ABS_HAT0X"], "onValue": 1},
                    "3": {"type": "hat", "names": ["ABS_HAT0Y"], "onValue": -1},
                    "4": {"type": "hat", "names": ["ABS_HAT0X"], "onValue": -1},
                    "A": {"type": "button", "names": ["BTN_A", "0x9:1"]},
                    "B": {"type": "button", "names": ["BTN_B", "0x9:2"]},
                    "C": {"type": "button", "names": ["BTN_X", "0x9:5"]},
                    "D": {"type": "button", "names": ["BTN_Y", "0x9:4"]},
                    "L": {"type": "button", "names": ["BTN_SELECT", "0x9:b"]},
                    "M": {"type": "button", "names": ["BTN_MODE", "0x9:d"]},
                    "R": {"type": "button", "names": ["BTN_START", "0x9:c"]},
                    "L1": {"type": "button", "names": ["BTN_TL", "0x9:7"]},
                    "L2": {"type": "button", "names": ["BTN_TL2", "0x9:9"]},
                    "L3": {"type": "button", "names": ["BTN_THUMBL", "0x9:e"]},
                    "R1": {"type": "button", "names": ["BTN_TR", "0x9:8"]},
                    "R2": {"type": "button", "names": ["BTN_TR2", "0x9:a"]},
                    "R3": {"type": "button", "names": ["BTN_THUMBR", "0x9:f"]},
                    "LJ-X": {"type": "axis", "names": ["ABS_X", "0x1:30"]},
                    "LJ-Y": {"type": "axis", "names": ["ABS_Y", "0x1:31"]},
                    "RJ-X": {"type": "axis", "names": ["ABS_Z", "0x1:32"]},
                    "RJ-Y": {"type": "axis", "names": ["ABS_RZ", "0x1:35"]},
                    "L4": {"type": "button", "names": ["BTN_C", "0x9:3"]},
                    "R4": {"type": "button", "names": ["BTN_Z", "0x9:6"]},
                },
            },
        ],
    },
}

REQUIRED_FIELDS = {
    "networking": ("baseIP", "raspIP", "retryDelaySec", "socketTimeout"),
    "autopilot": [
        "port",
        "maxBackwardPWM",
        "maxForwardPWM",
        "neutralPWM",
        "gainLevels",
        "timeoutSec",
        "rollIncDecAmount",
    ],
    "manfaloty": ["port"],
    "piTelemetry": ["port"],
    "piAdmin": ["port"],
    "controller": [
        "joystickDeadZoneFactor",
        "joystickRoundOff",
        "joystickMultiplier",
        "mappings",
        "configs",
        "timeUntilHoldTriggeredSec",
        "timeBetweenHoldTriggerSec",
        "triggerPressThreshold",
    ],
}


class InvalidConfigModule(Exception):
    pass


class InvalidConfigItem(Exception):
    pass


class ConfigManager(LoggerMixin):
    def __init__(self):
        super().__init__()
        self.config: dict[str, Any] = {}
        # if os.environ.get("HYDRANAV_TEST_MODE") is not None:
        #     self.config = TESTING_CONFIG
        #     self._logger.info("Loaded test config")
        #     return

        self.config = DEFAULT_CONFIG

        if not os.path.isfile(CONFIG_FILE_PATH):
            self._logger.info(
                f"'{CONFIG_FILE_PATH}' does not exist, using default config"
            )
        else:
            self._logger.info(f"Reading config from `{CONFIG_FILE_PATH}`")
            try:
                self.config = self.load_from_config()
            except yaml.YAMLError as e:
                self._logger.error(
                    f"Failed to read config from '{CONFIG_FILE_PATH}' with error {e}, falling back to default"
                )
            else:
                if self.__validate_config():
                    self._logger.info("Config file is Valid")
                else:
                    self._logger.error("Invalid config file, falling back to default")
                    self.config = DEFAULT_CONFIG

        self._logger.debug(f"Loaded config: {self.config}")

    def __validate_config(self) -> bool:
        # check that all the required objects exist
        validation_results = {}
        for module, required_fields in REQUIRED_FIELDS.items():
            validation_results[module] = self.config.get(module) is not None and all(
                field in self.config[module] for field in required_fields
            )

        networking_valid = validation_results.get("networking", False)
        notifier_valid = validation_results.get("notifier", False)
        autopilot_valid = validation_results.get("autopilot", False)
        manfaloty_valid = validation_results.get("manfaloty", False)
        piTelemetry_valid = validation_results.get("piTelemetry", False)
        piAdmin_valid = validation_results.get("piAdmin", False)
        controller_valid = validation_results.get("controller", False)

        # validate controller configurations
        # if controller_valid:
        #     for config in self.config["controller"]["configs"]:
        #         try:
        #             jsonschema.validate(config, CONTROLLER_CONFIG_SCHEMA)
        #         except jsonschema.ValidationError as e:
        #             self._logger.error(
        #                 f"Failed to parse controller config {config}; {e}"
        #             )
        #             controller_valid = False
        #             break

        return all(
            [
                bool(networking_valid),
                bool(notifier_valid),
                bool(autopilot_valid),
                bool(manfaloty_valid),
                bool(piTelemetry_valid),
                bool(piAdmin_valid),
                # bool(controller_valid),
            ]
        )

    def write_default_config(self):
        try:
            with open(CONFIG_FILE_PATH, "w") as file:
                yaml.dump(DEFAULT_CONFIG, file)

            self._logger.success(f"Wrote default config to {CONFIG_FILE_PATH}")
        except IOError as e:
            self._logger.error(
                f"Failed to write default config to '{CONFIG_FILE_PATH}', with error {e}"
            )
        except yaml.YAMLError as e:
            self._logger.error(
                f"Failed to serialize default config to yaml with error {e}"
            )

    def get(self, module: str, item: str) -> Any:
        if self.config.get(module) is None:
            raise InvalidConfigModule(module)

        if self.config[module].get(item) is None:
            raise InvalidConfigItem(item)

        return self.config[module][item]

    def __getitem__(self, item: Any) -> Any:
        if not isinstance(item, tuple) or not len(item) == 2:
            raise ValueError(
                "This notation only accepts inputs in the form of [<MODULE>, <ITEM>]"
            )

        return self.get(item[0], item[1])

    def load_from_config(self) -> dict[str, Any]:
        with open(CONFIG_FILE_PATH) as file:
            return dict(yaml.safe_load(file))


config_manager = ConfigManager()

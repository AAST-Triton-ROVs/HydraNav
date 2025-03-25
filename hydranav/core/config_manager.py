import os
from pathlib import Path
from typing import Any
import jsonschema
import yaml
import platformdirs
from core.logger import system_logger

APP_NAME = "HydraNav"
CONFIG_FILE_PATH = Path(platformdirs.user_config_dir(appname=APP_NAME), "config.yaml")


DEFAULT_CONFIG = {
    "networking": {
        "baseIP": "0.0.0.0",
        "raspIP": "192.168.1.100",
        "retryDelaySec": 2,
        "socketTimeout": 1,
    },
    "notifier": {"assetsPath": "./assets/audio"},
    "autopilot": {
        "port": 2000,
        "maxBackwardPWM": 1100,
        "maxForwardPWM": 1900,
        "neutralPWM": 1500,
        "gainLevels": [25, 40, 50, 75, 90],
        "timeoutSec": 2,
    },
    "manfaloty": {"port": 2005},
    "piTelemetry": {"port": 2010},
    "piAdmin": {"port": 2015},
    "controller": {
        "joystickDeadZoneFactor": 2,
        "joystickRoundOff": 1,
        "joystickMultiplier": 100,
        "timeUntilHoldTriggeredSec": 0.5,
        "timeBetweenHoldTriggerSec": 0.2,
        "mappings": [
            {
                "name": "zizo-style",
                "mappings": {
                    "ARM": "R",
                    "DISARM": "L",
                    "GAIN_UP": "3",
                    "GAIN_DOWN": "1",
                    "ROLL_RIGHT": "2",
                    "ROLL_LEFT": "4",
                    "STABILIZATION_MODE": "C",
                    "MANUAL_MODE": "D",
                    "GRIPPER_ROLL_LEFT": "L4",
                    "GRIPPER_ROLL_RIGHT": "R4",
                    "GRIPPER_PITCH_UP": "R2",
                    "GRIPPER_PITCH_DOWN": "L2",
                    "GRIPPER_JAW_OPEN": "R1",
                    "GRIPPER_JAW_CLOSE": "L1",
                    "FORWARD": {"joystick": "L", "axis": "Y"},
                    "LATERAL": {"joystick": "L", "axis": "X"},
                    "THROTTLE": {"joystick": "R", "axis": "Y"},
                    "YAW": {"joystick": "R", "axis": "X"},
                },
            }
        ],
        "configs": [
            {
                "displayName": "8BitDo 2C Ultimate Bluetooth",
                "pygameName": "8BitDo Ultimate 2C Wireless",
                "buttons": 16,
                "axes": 6,
                "hats": 1,
                "mappings": {
                    "1": {"type": "hat", "mapping": [0, -1]},
                    "2": {"type": "hat", "mapping": [1, 0]},
                    "3": {"type": "hat", "mapping": [0, 1]},
                    "4": {"type": "hat", "mapping": [-1, 0]},
                    "A": {"type": "button", "mapping": [0]},
                    "B": {"type": "button", "mapping": [1]},
                    "C": {"type": "button", "mapping": [4]},
                    "D": {"type": "button", "mapping": [3]},
                    "L": {"type": "button", "mapping": [10]},
                    "M": {"type": "button", "mapping": [12]},
                    "R": {"type": "button", "mapping": [11]},
                    "LJ": {"type": "axis", "axis": [0, 1]},
                    "L1": {"type": "button", "mapping": [6]},
                    "L2": {"type": "button", "mapping": [8]},
                    "L3": {"type": "button", "mapping": [13]},
                    "L4": {"type": "button", "mapping": [2]},
                    "RJ": {"type": "axis", "axis": [2, 3]},
                    "R1": {"type": "button", "mapping": [7]},
                    "R2": {"type": "button", "mapping": [9]},
                    "R3": {"type": "button", "mapping": [14]},
                    "R4": {"type": "button", "mapping": [5]},
                },
            },
            {
                "displayName": "8BitDo 2C Ultimate Wired",
                "pygameName": "8BitDo Ultimate 2C Wireless Controller",
                "buttons": 11,
                "axes": 6,
                "hats": 1,
                "mappings": {
                    "1": {"type": "hat", "mapping": [0, -1]},
                    "2": {"type": "hat", "mapping": [1, 0]},
                    "3": {"type": "hat", "mapping": [0, 1]},
                    "4": {"type": "hat", "mapping": [-1, 0]},
                    "A": {"type": "button", "mapping": [0]},
                    "B": {"type": "button", "mapping": [1]},
                    "C": {"type": "button", "mapping": [3]},
                    "D": {"type": "button", "mapping": [2]},
                    "L": {"type": "button", "mapping": [6]},
                    "M": {"type": "button", "mapping": [8]},
                    "R": {"type": "button", "mapping": [7]},
                    "LJ": {"type": "axis", "axis": [0, 1]},
                    "L1": {"type": "button", "mapping": [4]},
                    "L2": {"type": "trigger", "axis": [2]},
                    "L3": {"type": "button", "mapping": [9]},
                    "RJ": {"type": "axis", "axis": [3, 4]},
                    "R1": {"type": "button", "mapping": [5]},
                    "R2": {"type": "trigger", "axis": [5]},
                    "R3": {"type": "button", "mapping": [10]},
                },
            },
            {
                "displayName": "Default",
                "pygameName": "",
                "buttons": 16,
                "axes": 6,
                "hats": 0,
                "mappings": {
                    "1": {"type": "button", "mapping": [12]},
                    "2": {"type": "button", "mapping": [14]},
                    "3": {"type": "button", "mapping": [11]},
                    "4": {"type": "button", "mapping": [13]},
                    "A": {"type": "button", "mapping": [0]},
                    "B": {"type": "button", "mapping": [1]},
                    "C": {"type": "button", "mapping": [3]},
                    "D": {"type": "button", "mapping": [2]},
                    "L": {"type": "button", "mapping": [4]},
                    "M": {"type": "button", "mapping": [5]},
                    "R": {"type": "button", "mapping": [6]},
                    "LJ": {"type": "axis", "axis": [0, 1]},
                    "L1": {"type": "button", "mapping": [9]},
                    "L2": {"type": "trigger", "axis": [4]},
                    "L3": {"type": "button", "mapping": [7]},
                    "L4": {"type": "button", "mapping": [6, 9]},
                    "RJ": {"type": "axis", "axis": [2, 3]},
                    "R1": {"type": "button", "mapping": [10]},
                    "R2": {"type": "trigger", "axis": [5]},
                    "R3": {"type": "button", "mapping": [8]},
                    "R4": {"type": "button", "mapping": [6, 10]},
                },
            },
            {
                "displayName": "DualShock 4 Alternate",
                "pygameName": "PS4 Controller",
                "buttons": 16,
                "axes": 6,
                "hats": 0,
                "mappings": {
                    "1": {"type": "button", "mapping": [12]},
                    "2": {"type": "button", "mapping": [14]},
                    "3": {"type": "button", "mapping": [11]},
                    "4": {"type": "button", "mapping": [13]},
                    "A": {"type": "button", "mapping": [0]},
                    "B": {"type": "button", "mapping": [1]},
                    "C": {"type": "button", "mapping": [3]},
                    "D": {"type": "button", "mapping": [2]},
                    "L": {"type": "button", "mapping": [4]},
                    "M": {"type": "button", "mapping": [5]},
                    "R": {"type": "button", "mapping": [6]},
                    "LJ": {"type": "axis", "axis": [0, 1]},
                    "L1": {"type": "button", "mapping": [9]},
                    "L2": {"type": "trigger", "axis": [4]},
                    "L3": {"type": "button", "mapping": [7]},
                    "RJ": {"type": "axis", "axis": [2, 3]},
                    "R1": {"type": "button", "mapping": [10]},
                    "R2": {"type": "trigger", "axis": [5]},
                    "R3": {"type": "button", "mapping": [8]},
                },
            },
        ],
    },
}

CONTROLLER_CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "displayName": {"type": "string"},
        "pygameName": {"type": "string"},
        "buttons": {"type": "integer"},
        "axes": {"type": "integer"},
        "hats": {"type": "integer"},
        "mappings": {
            "type": "object",
            "patternProperties": {
                "^[A-Z0-9]+$": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["button", "axis", "hat", "trigger"],
                        },
                        "mapping": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "minItems": 0,
                        },
                        "axis": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "minItems": 0,
                        },
                    },
                    "required": ["type"],
                    "additionalProperties": True,
                }
            },
            "additionalProperties": False,
        },
    },
    "required": ["displayName", "pygameName", "buttons", "axes", "hats", "mappings"],
    "additionalProperties": False,
}

REQUIRED_NETWORKING_FIELDS = ("baseIP", "raspIP", "retryDelaySec", "socketTimeout")
REQUIRED_NOTIFIER_FIELDS = ["assetsPath"]
REQUIRED_AUTOPILOT_FIELDS = [
    "port",
    "maxBackwardPWM",
    "maxForwardPWM",
    "neutralPWM",
    "gainLevels",
    "timeoutSec",
]
REQUIRED_MANFALOTY_FIELDS = ["port"]
REQUIRED_PI_TELEMETRY_FIELDS = ["port"]
REQUIRED_PI_ADMIN_FIELDS = ["port"]
REQUIRED_CONTROLLER_FIELDS = [
    "joystickDeadZoneFactor",
    "joystickRoundOff",
    "joystickMultiplier",
    "mappings",
    "configs",
    "timeUntilHoldTriggeredSec",
    "timeBetweenHoldTriggerSec",
]


class InvalidConfigModule(Exception):
    pass


class InvalidConfigItem(Exception):
    pass


class ConfigManager:
    def __init__(self):
        self.config: dict[str, Any] = DEFAULT_CONFIG

    def __validate_config(self) -> bool:
        # check that all the required objects exist
        networking_valid = self.config.get("networking") is not None and all(
            k in self.config["networking"] for k in REQUIRED_NETWORKING_FIELDS
        )
        notifier_valid = self.config.get("notifier") is not None and all(
            k in self.config["notifier"] for k in REQUIRED_NOTIFIER_FIELDS
        )
        autopilot_valid = self.config.get("autopilot") is not None and all(
            k in self.config["autopilot"] for k in REQUIRED_AUTOPILOT_FIELDS
        )
        manfaloty_valid = self.config.get("manfaloty") is not None and all(
            k in self.config["manfaloty"] for k in REQUIRED_MANFALOTY_FIELDS
        )
        piTelemetry_valid = self.config.get("piTelemetry") is not None and all(
            k in self.config["piTelemetry"] for k in REQUIRED_PI_TELEMETRY_FIELDS
        )
        piAdmin_valid = self.config.get("piAdmin") is not None and all(
            k in self.config["piAdmin"] for k in REQUIRED_PI_ADMIN_FIELDS
        )
        controller_valid = self.config.get("controller") is not None and all(
            k in self.config["controller"] for k in REQUIRED_CONTROLLER_FIELDS
        )

        # validate controller configurations
        if controller_valid:
            for config in self.config["controller"]["configs"]:
                try:
                    jsonschema.validate(config, CONTROLLER_CONFIG_SCHEMA)
                except jsonschema.ValidationError as e:
                    system_logger.error(
                        f"Failed to parse controller config {config}; {e}"
                    )
                    controller_valid = False
                    break

        return all(
            [
                bool(networking_valid),
                bool(notifier_valid),
                bool(autopilot_valid),
                bool(manfaloty_valid),
                bool(piTelemetry_valid),
                bool(piAdmin_valid),
                bool(controller_valid),
            ]
        )

    def init(self):
        if not os.path.isfile(CONFIG_FILE_PATH):
            system_logger.info(
                f"'{CONFIG_FILE_PATH}' does not exist, using default config"
            )
        else:
            system_logger.info(f"Reading config from `{CONFIG_FILE_PATH}`")
            try:
                self.config = self.load_from_config()
            except yaml.YAMLError as e:
                system_logger.error(
                    f"Failed to read config from '{CONFIG_FILE_PATH}' with error {e}, falling back to default"
                )
            else:
                if self.__validate_config():
                    system_logger.success("Config file is Valid")
                else:
                    system_logger.error("Invalid config file, falling back to default")
                    self.config = DEFAULT_CONFIG

        system_logger.debug(f"Loaded config: {self.config}")

    def write_default_config(self):
        try:
            with open(CONFIG_FILE_PATH, "w") as file:
                yaml.dump(DEFAULT_CONFIG, file)

            system_logger.success(f"Wrote default config to {CONFIG_FILE_PATH}")
        except IOError as e:
            system_logger.error(
                f"Failed to write default config to '{CONFIG_FILE_PATH}', with error {e}"
            )
        except yaml.YAMLError as e:
            system_logger.error(
                f"Failed to serialize default config to yaml with error {e}"
            )

    def get(self, module: str, item: str) -> Any:
        if self.config.get(module) is None:
            raise InvalidConfigModule()

        if self.config[module].get(item) is None:
            raise InvalidConfigItem()

        return self.config[module][item]

    def load_from_config(self) -> dict[str, Any]:
        with open(CONFIG_FILE_PATH) as file:
            return dict(yaml.safe_load(file))


config_manager = ConfigManager()

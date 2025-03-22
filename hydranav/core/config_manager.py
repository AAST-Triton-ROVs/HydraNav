import os
from pathlib import Path
from typing import Any
import yaml
import platformdirs
from core.logger import system_logger
from core import request_manager

APP_NAME = "HydraNav"
CONFIG_FILE_PATH = Path(platformdirs.user_config_dir(appname=APP_NAME), "config.yaml")


class InvalidConfigModule(Exception):
    pass


class InvalidConfigItem(Exception):
    pass


class ConfigManager:
    def __init__(self):
        self.config: dict[str, dict] = {}

        if not os.path.isfile(CONFIG_FILE_PATH):
            system_logger.info(
                f"'{CONFIG_FILE_PATH}' does not exist, using default config"
            )

            self.load_default()
        else:
            system_logger.info(f"Reading config from `{CONFIG_FILE_PATH}`")
            try:
                self.config = self.load_from_config()
            except yaml.YAMLError as e:
                system_logger.error(
                    f"Failed to read config from '{CONFIG_FILE_PATH}' with error {e}, falling back to default"
                )
                self.config = self.load_default()

        request_manager.register_handler("core/config_manager", self.get)

    def get(self, module: str, item: str) -> Any:
        if self.config.get(module) is None:
            raise InvalidConfigModule()

        if self.config[module].get(item) is None:
            raise InvalidConfigItem()

        return self.config[module][item]

    def load_default(self) -> dict:
        with open("assets/config.yaml") as file:
            return yaml.safe_load(file)

    def load_from_config(self) -> dict:
        with open(CONFIG_FILE_PATH) as file:
            return yaml.safe_load(file)


config_manager = ConfigManager()

from typing import Optional
from core import config_manager, event_dispatcher, system_logger, request_manager


class InputMapper:
    def __init__(self):
        self.__mappings: list[dict[str, str]] = config_manager.get(
            "userInput", "mappings"
        )
        system_logger.debug(f"Controller mappings: {self.__mappings}")

        self.__current_mapping: Optional[dict[str, str]] = None

        try:
            self.__current_mapping = self.__mappings[0]
        except IndexError:
            system_logger.warning("No input mapping, no mapping will be done.")

    def button_down(self, button: str):
        if self.__current_mapping is None:
            return

        if self.__current_mapping.get(button) is None:
            return

        event_dispatcher.dispatch(f"mapper/{self.__current_mapping[button]}")
        request_manager.request(f"mapper/{self.__current_mapping[button]}")

    def button_hold(self, button: str):
        if self.__current_mapping is None or self.__current_mapping is None:
            return

        if self.__current_mapping.get(button) is None:
            return

        event_dispatcher.dispatch(f"mapper/hold/{self.__current_mapping[button]}")
        request_manager.request(f"mapper/{self.__current_mapping[button]}")

    def set_mapping(self, name: str):
        for mapping in self.__mappings:
            if mapping["name"] == name:
                self.__current_mapping = mapping
                return

        raise ValueError(f"'{name}' is not a valid mapping name")

    @property
    def current_mapping_name(self) -> Optional[str]:
        if self.__current_mapping:
            return self.__current_mapping["name"]
        return None

    @property
    def mapping_names(self) -> list[str]:
        return [config["name"] for config in self.__mappings]


input_mapper = InputMapper()

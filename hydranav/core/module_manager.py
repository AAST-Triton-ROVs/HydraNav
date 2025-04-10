import multiprocessing
import time
from typing import Any, Optional
import pygame
import signal
import sys
from core.logger import system_logger
from core import GCSModule
from core import Updatable

# time in seconds before forcefully exiting
QUIT_TIMEOUT = 5


class TimeoutError(Exception):
    pass


class ModuleManager:
    def __init__(self):
        self.__modules: dict[str, GCSModule] = {}
        self.__shutdown_lock = multiprocessing.Lock()

        signal.signal(signal.SIGINT, lambda a, b: self.shutdown())

    def __getattr__(self, name: str) -> Any:
        if not self.__modules.get(name):
            raise AttributeError

        return self.__modules[name]

    def register_module(self, module: GCSModule):
        self.__modules[type(module).__name__] = module

        system_logger.debug(f"Loaded {type(module).__name__}: {module}")

    def register_modules(self, modules: list[GCSModule]):
        for module in modules:
            self.register_module(module)

    def init_module(self, module_class: type):
        self.register_module(module_class())

    def init_modules(self, module_classes: list[type]):
        for module_class in module_classes:
            self.init_module(module_class)

    def deregister_module(self, module: str):
        if self.__modules.get(module):
            del self.__modules[module]

            system_logger.debug(f"{module} is unregistered")

    def quit_module(self, module: str):
        if self.__modules.get(module):
            try:
                self.__modules[module].quit()
            except AssertionError as e:
                system_logger.error(str(e))
            del self.__modules[module]
            system_logger.success(f"{module} has been quit")

    def shutdown(self):
        system_logger.info("Starting shutdown sequence")
        start_time = time.monotonic()
        for module in list(self.__modules.keys()):
            if time.monotonic() - start_time >= QUIT_TIMEOUT:
                break

            self.quit_module(module)

        pygame.quit()
        system_logger.info("Goodbye!")
        for proc in multiprocessing.active_children():
            proc.terminate()
            proc.join()
        sys.exit(0)

    def get_instance(self, module: str) -> Optional[GCSModule]:
        if self.__modules.get(module):
            return self.__modules[module]

        return None

    def update_all(self):
        for module in self.__modules.values():
            if isinstance(module, Updatable):
                module.update()

    def get_module_status(self, module: str) -> Optional[bool]:
        if self.__modules.get(module) is None:
            return None

        return self.__modules[module].status_ok()

    def get_all_module_statuses(self) -> dict[str, bool]:
        data: dict[str, bool] = {}
        for name in self.__modules.keys():
            status = self.get_module_status(name)
            if status is None:
                continue

            data[name] = status

        return data

    @property
    def exit_complete(self) -> bool:
        return len(self.__modules) == 0

    @property
    def loaded_modules(self) -> list[str]:
        return list(self.__modules.keys())


module_manager = ModuleManager()

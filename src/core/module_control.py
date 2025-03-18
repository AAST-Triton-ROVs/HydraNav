import pygame
from core.event_dispatcher import EventDispatcher
from core.logger import system_logger
from core.gcs_module import GCSModule
import time
import signal
import sys

# time in seconds before forcefully exiting
QUIT_TIMEOUT = 5


class TimeoutError(Exception):
    pass


class ModuleControl:
    def __init__(self, dispatcher: EventDispatcher):
        self.__modules: dict[str, GCSModule] = {}
        self.__dispatcher = dispatcher

        signal.signal(signal.SIGINT, lambda a, b: self.shutdown())
        signal.signal(signal.SIGALRM, ModuleControl.__timeout_handler)
        self.__dispatcher.subscribe("module_quit", self.__module_quit_successful)

    @staticmethod
    def __timeout_handler(signum, frame):
        raise TimeoutError()

    def __module_quit_successful(self, module: str):
        system_logger.success(f"{module} has been quit.")
        self.deregister_module(module)

    def register_module(self, module: GCSModule):
        self.__modules[type(module).__name__] = module

        system_logger.debug(f"Loaded {type(module).__name__}: {module}")

    def deregister_module(self, module: str):
        if self.__modules.get(module):
            del self.__modules[module]

            system_logger.debug(f"{module} is unregistered")

    def quit_module(self, module: str):
        if self.__modules.get(module):
            self.__modules[module].quit()

    def quit_all(self):
        module_names = list(self.__modules.keys())
        signal.alarm(QUIT_TIMEOUT)
        try:
            for module in module_names:
                self.quit_module(module)
        except TimeoutError:
            system_logger.warning(
                f"Failed to stop all modules in {QUIT_TIMEOUT}s."
            )
            
    def shutdown(self):
        system_logger.info("Starting shutdown sequence")
        self.quit_all()
        pygame.quit()
        system_logger.info("Done!")
        sys.exit(0)

    @property
    def exit_complete(self) -> bool:
        return len(self.__modules) == 0

    @property
    def loaded_modules(self) -> list[str]:
        return list(self.__modules.keys())

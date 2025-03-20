from typing import Optional
import pygame
import signal
import sys
from core.logger import system_logger
from core import GCSModule

# time in seconds before forcefully exiting
QUIT_TIMEOUT = 5


class TimeoutError(Exception):
    pass


class ModuleManager:
    def __init__(self):
        self.__modules: dict[str, GCSModule] = {}

        signal.signal(signal.SIGINT, lambda a, b: self.shutdown())
        signal.signal(signal.SIGALRM, self.__timeout_handler)

    @staticmethod
    def __timeout_handler(signum, frame):
        raise TimeoutError()

    def register_module(self, module: GCSModule):
        self.__modules[type(module).__name__] = module

        system_logger.debug(f"Loaded {type(module).__name__}: {module}")
        
    def register_modules(self, modules: list[GCSModule]):
        for module in modules:
            self.register_module(module)

    def deregister_module(self, module: str):
        if self.__modules.get(module):
            del self.__modules[module]

            system_logger.debug(f"{module} is unregistered")

    def quit_module(self, module: str):
        if self.__modules.get(module):
            self.__modules[module].quit()
            system_logger.success(f"{module} has been quit")

    def quit_all(self):
        module_names = list(self.__modules.keys())
        signal.alarm(QUIT_TIMEOUT)
        try:
            for module in module_names:
                self.quit_module(module)
        except TimeoutError:
            system_logger.warning(f"Failed to stop all modules in {QUIT_TIMEOUT}s.")

    def shutdown(self):
        system_logger.info("Starting shutdown sequence")
        self.quit_all()
        pygame.quit()
        system_logger.info("Goodbye!")
        sys.exit(0)
        
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

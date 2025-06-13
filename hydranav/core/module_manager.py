from enum import IntEnum
import multiprocessing
import os
import signal
from typing import Any, Optional
from hydranav.core.event_dispatcher import event_dispatcher
from hydranav.core.tts import TTS
from hydranav.core.updatable import Updatable
from hydranav.core.gcs_module import GCSModule
from hydranav.core.logger import LoggerMixin

# time in seconds before forcefully exiting
QUIT_TIMEOUT = 3


class TimeoutError(Exception):
    pass


SHUTTING_DOWN_LINE = TTS.register_line("Shutting Down")
MODULE_DOWN_LINE = TTS.register_line("Module Down")


class ModuleManager(LoggerMixin):
    def __init__(self):
        super().__init__()
        self.__modules: dict[str, GCSModule] = {}

        signal.signal(signal.SIGINT, lambda a, b: self.__handle_sigint())

        event_dispatcher.subscribe("mapper/QUIT", lambda _: self.shutdown())
        TTS.attach_to_event(SHUTTING_DOWN_LINE, "module-manager/shutdown-begin")
        TTS.attach_to_event(MODULE_DOWN_LINE, "module-manager/module-down")

    def __getattr__(self, name: str) -> Any:
        if not self.__modules.get(name):
            raise AttributeError

        return self.__modules[name]

    def __handle_sigint(self):
        if multiprocessing.current_process().name == "MainProcess":
            self.shutdown()

    def register_module(self, module: GCSModule):
        self.__modules[module.module_name()] = module

        self._logger.debug(f"Loaded {module.module_name()}: {module}")

    def register_modules(self, modules: list[GCSModule]):
        for module in modules:
            self.register_module(module)

    def init_module(self, module_class: type[GCSModule]):
        try:
            self.register_module(module_class())
        except Exception as e:
            self._logger.error(
                f"Failed to start module {module_class.__name__}, {type(e).__name__}: {e}"
            )
        else:
            event_dispatcher.dispatch(
                "module-manager/module-init", module_class.__name__
            )

    def init_modules(self, module_classes: list[type[GCSModule]]):
        module_classes.sort(key=lambda x: x.init_order())
        for module_class in module_classes:
            self.init_module(module_class)

    def unregister_module(self, module: str):
        if self.__modules.get(module):
            del self.__modules[module]

            self._logger.debug(f"{module} is unregistered")

    def quit_module(self, module: str):
        if self.__modules.get(module):
            self.__modules[module].quit()
            del self.__modules[module]
            self._logger.success(f"{module} has been quit")

    def shutdown(self):
        self._logger.info("Starting shutdown sequence")
        event_dispatcher.dispatch("module-manager/shutdown-begin")

        for module in list(self.__modules.keys()):
            try:
                self.quit_module(module)
            except Exception as e:
                self._logger.error(f"{module} error while calling quit: {e}")

        self._logger.info("Goodbye!")
        for proc in multiprocessing.active_children():
            proc.terminate()
            proc.join()
        os._exit(0)

    def get_instance(self, module: str) -> Optional[GCSModule]:
        if self.__modules.get(module):
            return self.__modules[module]

        return None

    def update_all(self):
        broken_modules: list[str] = []
        for module in self.__modules.values():
            if not self.get_module_status_ok(module.module_name()):
                broken_modules.append(module.module_name())
                continue
            if isinstance(module, Updatable):
                try:
                    module.update()
                except Exception as e:
                    self._logger.error(
                        f"Error while updating {module.module_name()}: {type(e).__name__} {e}"
                    )

        for mod_name in broken_modules:
            self._logger.error(f"{mod_name} has stopped working; Unloading module")
            event_dispatcher.dispatch("module-manager/module-down", mod_name)
            self.unregister_module(mod_name)

    def filter_modules_by_parent(self, parent: type) -> list:
        result = []
        for module in self.__modules.values():
            if isinstance(module, parent):
                result.append(module)

        return result

    def get_module_status_ok(self, module: str) -> Optional[bool]:
        if self.__modules.get(module) is None:
            return None

        return self.__modules[module].status_ok()

    def get_all_module_statuses(self) -> dict[str, bool]:
        data: dict[str, bool] = {}
        for name in self.__modules.keys():
            status = self.get_module_status_ok(name)
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

import logging
from typing import Any, Callable, Optional, cast
from hydranav.core import (
    GCSModule,
    Updatable,
    event_dispatcher,
    module_manager,
    request_manager,
)
from nicegui import ui
import multiprocessing
import uvicorn
from fastapi import FastAPI
import re
from hydranav.core.has_webgui import HasWebGUI
import netifaces


SERVER_PROCESS_NAME = "WebGUI"
SERVER_IP = "0.0.0.0"
SERVER_PORT = 4000
WEBPAGE_TITLE = "HydraNav"
Icon = str
DEFAULT_WIRELESS_INTERFACE = "wlo1"


class WebGUI(GCSModule, Updatable):
    def __init__(self):
        super().__init__()

        self.__daemon = multiprocessing.Process(
            target=self.__run_server,
            daemon=True,
            name=SERVER_PROCESS_NAME,
        )
        self.__daemon.start()

    def __run_server(self):
        app = FastAPI()
        ui.run_with(
            app,
            title="HydraNav",
            dark=True,
        )
        uvicorn.run(
            app,
            port=SERVER_PORT,
            host=SERVER_IP,
        )

    def quit(self):
        """Quits module"""
        self.__daemon.terminate()
        self.__daemon.join()

    def status_ok(self) -> bool:
        return self.__daemon.is_alive()

    def update(self):
        return


@ui.page("/")
def _index():
    _build()


def _build():
    contents_container = ui.column().classes("w-full")
    with contents_container:
        with ui.column(align_items="center").classes(
            "w-full items-center justify-center"
        ):
            ui.label("HydraNav").classes("text-5xl font-extrabold dark:text-white")
            ui.label("Choose a module from the footer to load.").classes(
                "text-lg font-normal text-gray-500 dark:text-gray-400"
            )
            local_ip = _get_ip_address(DEFAULT_WIRELESS_INTERFACE)
            if local_ip:
                ui.label(f"Also available at {local_ip}:{SERVER_PORT}").classes(
                    "text-lg font-normal text-gray-500 dark:text-gray-400"
                )

    with ui.footer().classes("mt-auto justify-center"):
        _generate_footer_buttons(contents_container)


@ui.refreshable
def _generate_footer_buttons(contents_container: ui.element):
    modules = module_manager.filter_modules_by_parent(HasWebGUI)
    for module in modules:
        ui.button(
            _class_name_to_words(module.module_name()),
            icon=module.webgui_icon_name(),
            on_click=lambda m=module: _update_contents(
                contents_container, m.webgui_contents
            ),
        )


@ui.refreshable
def _update_contents(contents_container: ui.element, factory: Callable[[], ui.element]):
    contents_container.clear()
    with contents_container:
        factory()


def _class_name_to_words(name: str) -> str:
    return re.sub(r"(?<=[a-z])(?=[A-Z0-9])|(?<=[A-Z])(?=[A-Z][a-z])", " ", name)


def _get_ip_address(interface) -> Optional[str]:
    try:
        # Get the addresses associated with the interface
        addresses = netifaces.ifaddresses(interface)
        # Get the IPv4 address
        ip_address = addresses[netifaces.AF_INET][0]["addr"]
        return ip_address
    except ValueError:
        return None
    except KeyError:
        return None

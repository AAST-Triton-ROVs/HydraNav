from functools import partial
import logging
import pickle
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

        self.__server_process = multiprocessing.Process(target=self.__run_server)
        self.__server_process.start()

    def __run_server(self):
        _generate_ui()

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

    @classmethod
    def init_order(cls):
        return 99

    def quit(self):
        """Quits module"""
        self.__server_process.terminate()
        self.__server_process.join()

    def status_ok(self) -> bool:
        return self.__server_process.is_alive()

    def update(self):
        return


def _generate_footer_button(module):
    ui.button(
        _camel_to_normal_case(module.module_name()),
        icon=module.webgui_icon_name(),
        on_click=lambda: ui.navigate.to(
            f"/{_camel_to_dash_case(module.module_name())}"
        ),
    )


def _generate_ui():
    from hydranav.core import module_manager

    ui.page("/")(_home_page_content)

    modules = module_manager.filter_modules_by_parent(HasWebGUI)
    for module in modules:
        _create_module_page(module)


def _create_module_page(module):
    path = f"/{_camel_to_dash_case(module.module_name())}"
    title = _camel_to_normal_case(module.module_name())

    @ui.page(path, title=title)
    def page():
        with ui.column().classes("w-full"):
            module.webgui_contents()

        with ui.footer().classes("mt-auto justify-center"):
            ui.button("Home", icon="home", on_click=lambda: ui.navigate.to("/"))

            modules = module_manager.filter_modules_by_parent(HasWebGUI)
            for m in modules:
                _generate_footer_button(m)


def _generate_page(contents_factory: Callable[[], ui.element]):
    def generate_footer_button(module):
        ui.button(
            _camel_to_normal_case(module.module_name()),
            icon=module.webgui_icon_name(),
            on_click=lambda: ui.navigate.to(
                f"/{_camel_to_dash_case(module.module_name())}"
            ),
        )

    container = ui.column().classes("w-full")
    with container:
        contents_factory()

    with ui.footer().classes("mt-auto justify-center"):
        ui.button(
            "Home",
            icon="home",
            on_click=lambda: ui.navigate.to("/"),
        )

        modules = module_manager.filter_modules_by_parent(HasWebGUI)
        for module in modules:
            generate_footer_button(module)


def _home_page_content():
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
    return _generate_page(lambda: contents_container)


def _camel_to_normal_case(name: str) -> str:
    return re.sub(r"(?<=[a-z])(?=[A-Z0-9])|(?<=[A-Z])(?=[A-Z][a-z])", " ", name)


def _camel_to_dash_case(text: str) -> str:
    dashed = re.sub(r"(?<!^)(?=[A-Z])", "-", text)
    return dashed.lower()


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

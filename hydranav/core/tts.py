import os
from pathlib import Path
import platformdirs
from playsound3 import playsound
from hydranav.core.event_dispatcher import event_dispatcher
from hydranav.core.config_manager import config_manager, APP_NAME
from hydranav.core.logger import LoggerMixin
from dimits import Dimits  # type: ignore
from xxhash import xxh3_128_hexdigest
import multiprocessing

LineID = str
TTS_MODEL = config_manager["tts", "piperModel"]
TTS_LINE_GEN_TIMEOUT = config_manager["tts", "genTimeout"]
DATA_DIR_PATH = platformdirs.user_data_dir(appname=APP_NAME)
TTS_RECORDINGS_DIR_PATH = Path(DATA_DIR_PATH, "tts", "recordings")
MODEL_PATH = Path(DATA_DIR_PATH, "tts")


class TextToSpeech(LoggerMixin):
    def __init__(self):
        super().__init__()

        self.__lines_on_disk: list[LineID] = []
        self.__lines_to_generate: dict[LineID, str] = {}
        self.__lines: dict[LineID, str] = {}

        self.__dt = None
        self.__enabled = True

        os.makedirs(TTS_RECORDINGS_DIR_PATH, exist_ok=True)
        os.makedirs(MODEL_PATH, exist_ok=True)

        try:
            self.__lines_on_disk = [
                x.split(".")[0] for x in os.listdir(TTS_RECORDINGS_DIR_PATH)
            ]
        except IOError as e:
            self._logger.error(f"Failed tp read lines: {e}")

    def init(self):
        self.__dt = Dimits(TTS_MODEL, modelDirectory=str(MODEL_PATH))

    def register_line(self, line: str) -> LineID:
        line_id = xxh3_128_hexdigest(line)
        if line_id not in self.__lines_on_disk:
            self.__lines_to_generate[line_id] = line
            self._logger.info(f"'{line}' is an unregistered line")
        else:
            self.__lines[line_id] = str(Path(TTS_RECORDINGS_DIR_PATH, f"{line_id}.wav"))
            self._logger.debug(f"'{line}' is registered line")

        return line_id

    def play_line(self, line_id: LineID):
        if not self.__enabled:
            return

        if line_id not in self.__lines:
            return

        playsound(self.__lines[line_id], block=False)

    def attach_to_event(self, line_id: LineID, event: str):
        event_dispatcher.subscribe(event, lambda _: self.play_line(line_id))

    def __generate_line(self, line: str, line_id: LineID):
        if self.__dt is None:
            self._logger.error("TTS is not initialized")
            return

        try:
            self.__dt.text_2_audio_file(
                f"{line}..",
                f"{line_id}",
                str(TTS_RECORDINGS_DIR_PATH),
                format="wav",
            )
        except OSError as e:
            self._logger.error(f"Failed to generate TTS line, with error: {e}")

    def update_and_generate_lines(self):
        unexpected_lines = [
            line_id for line_id in self.__lines_on_disk if line_id not in self.__lines.keys()
        ]
        self._logger.debug(f"{self.__lines_on_disk = }")
        self._logger.debug(f"{self.__lines.keys() = }")
        if unexpected_lines:
            self._logger.warning(f"Found unexpected lines on disk: {unexpected_lines}")

        if len(self.__lines_to_generate) == 0:
            return

        for line_id, line in self.__lines_to_generate.items():
            self._logger.info(f"Generating '{line}'")
            process = multiprocessing.Process(
                target=self.__generate_line,
                args=(line, line_id),
                daemon=True,
            )
            process.start()
            process.join(timeout=TTS_LINE_GEN_TIMEOUT)
            if process.is_alive():
                self._logger.warning(
                    f"Failed to generate '{line}' in {TTS_LINE_GEN_TIMEOUT}s, skipping"
                )
                process.terminate()
                process.join()
            elif process.exitcode == 0:
                self._logger.success(f"Generated '{line}'")

            try:
                self.__lines[line_id] = str(
                    Path(TTS_RECORDINGS_DIR_PATH, f"{line_id}.wav")
                )
                self._logger.success(f"Registered '{line}' with '{line_id}'")
            except FileNotFoundError:
                self._logger.error(f"Failed to generate file for '{line}'.")

    def enable(self):
        self.__enabled = True

    def disable(self):
        self.__enabled = False


TTS = TextToSpeech()

import multiprocessing
from multiprocessing.connection import Connection
from typing import Any, Dict, List


class StreamDispatcher:
    def __init__(self) -> None:
        self._stream_connections: Dict[str, List[Connection]] = {}

    def dispatch(self, stream_name: str, data: Any, raw_bytes: bool = False) -> None:
        connections = self._stream_connections.get(stream_name)
        if not connections:
            return

        for conn in connections[:]:
            try:
                if raw_bytes:
                    conn.send_bytes(data)
                else:
                    conn.send(data)
            except (BrokenPipeError, EOFError):
                connections.remove(conn)

    def request_stream(self, stream_name: str) -> Connection:
        sender, receiver = multiprocessing.Pipe()

        self._stream_connections.setdefault(stream_name, []).append(sender)
        return receiver

    def remove_connection(self, stream_name: str, connection: Connection) -> None:
        if stream_name in self._stream_connections:
            self._stream_connections[stream_name] = [
                conn
                for conn in self._stream_connections[stream_name]
                if conn != connection
            ]
            if not self._stream_connections[stream_name]:
                del self._stream_connections[stream_name]


stream_dispatcher = StreamDispatcher()

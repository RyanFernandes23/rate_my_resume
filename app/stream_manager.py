"""Background job manager for resume analysis — handles long-running LLM work off HTTP connection."""

import asyncio
import uuid
import logging
import threading
from queue import Queue, Empty
from typing import Any, Optional
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class StreamJob:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.queue: Queue = Queue()
        self._done = threading.Event()
        self.result: Optional[dict] = None

    def emit(self, stage: str, progress: int, message: str) -> None:
        self.queue.put_nowait({"stage": stage, "progress": progress, "message": message})

    def complete(self, result: dict) -> None:
        self.queue.put_nowait({"stage": "complete", "progress": 100, "message": "Analysis complete!", "status": "complete", "result": result})
        self._done.set()

    def error(self, message: str) -> None:
        self.queue.put_nowait({"stage": "error", "progress": 0, "message": message, "status": "error"})
        self._done.set()

    def get_event(self, timeout: float = 0.5) -> Optional[dict]:
        try:
            return self.queue.get(timeout=timeout)
        except Empty:
            return None

    def wait_done(self, timeout: float = 300) -> bool:
        return self._done.wait(timeout=timeout)

    def is_done(self) -> bool:
        return self._done.is_set()


class StreamManager:
    _instance: Optional["StreamManager"] = None
    _lock = threading.Lock()
    _jobs: dict[str, StreamJob] = {}
    _ws_connections: dict[str, set[WebSocket]] = {}

    def __new__(cls) -> "StreamManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def create_job(self) -> str:
        job_id = str(uuid.uuid4())
        with self._lock:
            self._jobs[job_id] = StreamJob(job_id)
            self._ws_connections[job_id] = set()
        return job_id

    def get_job(self, job_id: str) -> Optional[StreamJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def register_websocket(self, job_id: str, ws: WebSocket) -> bool:
        with self._lock:
            if job_id not in self._ws_connections:
                return False
            self._ws_connections[job_id].add(ws)
            return True

    def unregister_websocket(self, job_id: str, ws: WebSocket) -> None:
        with self._lock:
            if job_id in self._ws_connections:
                self._ws_connections[job_id].discard(ws)

    def broadcast(self, job_id: str, event: dict) -> None:
        with self._lock:
            connections = list(self._ws_connections.get(job_id, []))

        for ws in connections:
            try:
                asyncio.run_coroutine_threadsafe(ws.send_json(event), _get_loop())
            except Exception as e:
                logger.warning(f"Failed to broadcast to WS: {e}")

    def cleanup(self, job_id: str) -> None:
        with self._lock:
            self._jobs.pop(job_id, None)
            self._ws_connections.pop(job_id, None)


def _get_loop() -> asyncio.AbstractEventLoop:
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


_stream_manager: StreamManager = StreamManager()


def get_stream_manager() -> StreamManager:
    return _stream_manager
"""DropZone ファイル監視"""

import logging
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from app.usecase.dto.ingest_file_input import IngestFileInput
from app.usecase.ports.input.ingest_file_usecase import IngestFileUseCase

logger = logging.getLogger(__name__)

_SUPPORTED = {".csv", ".json", ".jsonl", ".ndjson", ".parquet"}


class _IngestionHandler(FileSystemEventHandler):
    def __init__(self, usecase: IngestFileUseCase, dropzone: Path):
        self._usecase = usecase
        self._dropzone = dropzone

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in _SUPPORTED:
            return

        try:
            relative = path.relative_to(self._dropzone)
            dataset_name = relative.parts[0] if len(relative.parts) > 1 else "unknown"
        except ValueError:
            dataset_name = "unknown"

        try:
            output = self._usecase.run(
                IngestFileInput(file_path=str(path), dataset_name=dataset_name)
            )
            if output.skipped:
                logger.info("Skipped (duplicate): %s", path.name)
            elif output.success:
                logger.info("Ingested: %s → %s", path.name, output.raw_path)
            else:
                logger.error("Failed: %s — %s", path.name, output.message)
        except Exception:
            logger.exception("Unexpected error ingesting %s", path)


class DropzoneWatcher:
    """DropZone ディレクトリを監視して新着ファイルを自動取り込みする"""

    def __init__(self, usecase: IngestFileUseCase, dropzone_path: str):
        self._observer = Observer()
        self._dropzone = Path(dropzone_path)
        self._handler = _IngestionHandler(usecase, self._dropzone)

    def start(self) -> None:
        self._dropzone.mkdir(parents=True, exist_ok=True)
        self._observer.schedule(self._handler, str(self._dropzone), recursive=True)
        self._observer.start()
        logger.info("DropzoneWatcher started: %s", self._dropzone)

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join()
        logger.info("DropzoneWatcher stopped")

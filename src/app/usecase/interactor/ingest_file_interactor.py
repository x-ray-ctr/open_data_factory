"""ファイル取り込みインタラクター"""

import hashlib
import json
import logging
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from app.domain.model.ingestion_record import IngestionRecord
from app.usecase.dto.ingest_file_input import IngestFileInput
from app.usecase.dto.ingest_file_output import IngestFileOutput
from app.usecase.ports.input.ingest_file_usecase import IngestFileUseCase
from app.usecase.ports.output.ingestion_registry import IngestionRegistry
from app.usecase.ports.output.raw_storage import RawStorage

logger = logging.getLogger(__name__)


def _compute_checksum(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class IngestFileInteractor(IngestFileUseCase):
    def __init__(
        self,
        loader,
        registry: IngestionRegistry,
        raw_storage: RawStorage,
        view_manager,
    ):
        self._loader = loader
        self._registry = registry
        self._raw_storage = raw_storage
        self._view_manager = view_manager

    def run(self, input: IngestFileInput) -> IngestFileOutput:
        file_path = input.file_path
        dataset_name = input.dataset_name

        checksum = _compute_checksum(file_path)

        existing = self._registry.find_by_checksum(checksum)
        if existing:
            logger.info("Skipped duplicate: %s (%s)", Path(file_path).name, existing.file_id)
            return IngestFileOutput(
                file_id=existing.file_id,
                success=True,
                skipped=True,
                message=f"Already ingested: {existing.file_id}",
            )

        file_id = str(uuid4())
        record = IngestionRecord(
            file_id=file_id,
            dataset_name=dataset_name,
            file_name=Path(file_path).name,
            file_path=file_path,
            checksum=checksum,
            detected_at=datetime.utcnow(),
            status="processing",
        )
        self._registry.save(record)

        try:
            df = self._loader.load(file_path)
            raw_path = self._raw_storage.save(df, dataset_name, date.today())
            schema_json = json.dumps({col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)})
            self._registry.update_status(
                file_id=file_id,
                status="completed",
                processed_at=datetime.utcnow(),
                schema_json=schema_json,
                row_count=len(df),
            )
            self._view_manager.ensure_view(dataset_name)
            logger.info("Ingested: %s → %s (%d rows)", Path(file_path).name, raw_path, len(df))
            return IngestFileOutput(
                file_id=file_id,
                success=True,
                raw_path=raw_path,
                message="Ingested successfully",
            )
        except Exception as exc:
            self._registry.update_status(
                file_id=file_id,
                status="failed",
                processed_at=datetime.utcnow(),
            )
            logger.error("Ingestion failed: %s — %s", Path(file_path).name, exc)
            return IngestFileOutput(file_id=file_id, success=False, message=str(exc))

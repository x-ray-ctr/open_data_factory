"""IngestFileInteractor の統合テスト"""

import tempfile
from pathlib import Path

import polars as pl
import pytest

from app.infrastructure.duckdb.connection import DuckDBConnection
from app.infrastructure.loader.local_file_loader import LocalFileLoader
from app.infrastructure.registry.duckdb_ingestion_registry import DuckDBIngestionRegistry
from app.infrastructure.storage.local_raw_storage import LocalRawStorage
from app.infrastructure.view.duckdb_view_manager import DuckDBViewManager
from app.usecase.dto.ingest_file_input import IngestFileInput
from app.usecase.interactor.ingest_file_interactor import IngestFileInteractor


@pytest.fixture()
def tmp_dirs(tmp_path):
    return {
        "db": str(tmp_path / "analytics.duckdb"),
        "raw": str(tmp_path / "raw"),
    }


@pytest.fixture()
def interactor(tmp_dirs):
    conn = DuckDBConnection(tmp_dirs["db"])
    registry = DuckDBIngestionRegistry(conn)
    raw_storage = LocalRawStorage(tmp_dirs["raw"])
    view_manager = DuckDBViewManager(conn, tmp_dirs["raw"])
    loader = LocalFileLoader()
    return IngestFileInteractor(
        loader=loader,
        registry=registry,
        raw_storage=raw_storage,
        view_manager=view_manager,
    ), registry, view_manager


def _write_csv(path: Path, content: str) -> str:
    f = path / "test.csv"
    f.write_text(content)
    return str(f)


class TestIngestFileInteractor:
    def test_csv_ingestion_success(self, interactor, tmp_path):
        sut, registry, _ = interactor
        csv = _write_csv(tmp_path, "id,name,amount\n1,Alice,100\n2,Bob,200\n")

        out = sut.run(IngestFileInput(file_path=csv, dataset_name="sales"))

        assert out.success is True
        assert out.skipped is False
        assert out.raw_path != ""
        assert Path(out.raw_path).exists()

    def test_duplicate_file_is_skipped(self, interactor, tmp_path):
        sut, _, _ = interactor
        csv = _write_csv(tmp_path, "id,val\n1,10\n")

        out1 = sut.run(IngestFileInput(file_path=csv, dataset_name="sales"))
        out2 = sut.run(IngestFileInput(file_path=csv, dataset_name="sales"))

        assert out1.success is True and out1.skipped is False
        assert out2.success is True and out2.skipped is True
        assert out2.file_id == out1.file_id

    def test_registry_records_completed_status(self, interactor, tmp_path):
        sut, registry, _ = interactor
        csv = _write_csv(tmp_path, "x,y\n1,2\n3,4\n5,6\n")

        sut.run(IngestFileInput(file_path=csv, dataset_name="metrics"))

        records = registry.list_records()
        assert len(records) == 1
        assert records[0].status == "completed"
        assert records[0].row_count == 3
        assert records[0].dataset_name == "metrics"

    def test_duckdb_view_created_after_ingestion(self, interactor, tmp_path):
        sut, _, view_manager = interactor
        csv = _write_csv(tmp_path, "a,b\n1,2\n")

        sut.run(IngestFileInput(file_path=csv, dataset_name="events"))

        views = view_manager.list_views()
        assert "raw_events" in views

    def test_raw_parquet_partitioned_by_date(self, interactor, tmp_path):
        sut, _, _ = interactor
        csv = _write_csv(tmp_path, "col\nval\n")

        out = sut.run(IngestFileInput(file_path=csv, dataset_name="logs"))

        raw_path = Path(out.raw_path)
        # path format: raw/logs/{year}/{month}/{day}/{uuid}.parquet
        assert raw_path.suffix == ".parquet"
        parts = raw_path.parts
        assert "logs" in parts

    def test_jsonl_ingestion(self, interactor, tmp_path):
        sut, registry, _ = interactor
        jsonl = tmp_path / "data.jsonl"
        jsonl.write_text('{"id":1,"val":10}\n{"id":2,"val":20}\n')

        out = sut.run(IngestFileInput(file_path=str(jsonl), dataset_name="stream"))

        assert out.success is True
        records = registry.list_records()
        assert records[0].row_count == 2

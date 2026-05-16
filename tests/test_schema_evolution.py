"""スキーマが異なるCSVファイルの統合（スキーマ進化）のテスト"""

from pathlib import Path

import pytest

from app.infrastructure.duckdb.connection import DuckDBConnection
from app.infrastructure.loader.local_file_loader import LocalFileLoader
from app.infrastructure.registry.duckdb_ingestion_registry import DuckDBIngestionRegistry
from app.infrastructure.storage.local_raw_storage import LocalRawStorage
from app.infrastructure.view.duckdb_view_manager import DuckDBViewManager
from app.usecase.dto.ingest_file_input import IngestFileInput
from app.usecase.interactor.ingest_file_interactor import IngestFileInteractor


@pytest.fixture()
def pipeline(tmp_path):
    conn = DuckDBConnection(str(tmp_path / "analytics.duckdb"))
    registry = DuckDBIngestionRegistry(conn)
    raw_storage = LocalRawStorage(str(tmp_path / "raw"))
    view_manager = DuckDBViewManager(conn, str(tmp_path / "raw"))
    loader = LocalFileLoader()
    interactor = IngestFileInteractor(
        loader=loader,
        registry=registry,
        raw_storage=raw_storage,
        view_manager=view_manager,
    )
    return interactor, conn, view_manager


class TestSchemaEvolution:
    def test_different_schema_csvs_are_unioned_by_name(self, pipeline, tmp_path):
        """カラムが異なるCSVでもDuckDBビューで列名ベースに統合されること"""
        interactor, conn, _ = pipeline

        # 1月: id, name, amount
        csv1 = tmp_path / "sales_jan.csv"
        csv1.write_text("id,name,amount\n1,Alice,100\n2,Bob,200\n")

        # 2月: id, name, amount, region (カラム追加)
        csv2 = tmp_path / "sales_feb.csv"
        csv2.write_text("id,name,amount,region\n3,Carol,300,Tokyo\n4,Dave,400,Osaka\n")

        # 3月: id, name, amount, discount (別カラム追加)
        csv3 = tmp_path / "sales_mar.csv"
        csv3.write_text("id,name,amount,discount\n5,Eve,500,10\n6,Frank,600,20\n")

        for f in [csv1, csv2, csv3]:
            out = interactor.run(IngestFileInput(file_path=str(f), dataset_name="sales"))
            assert out.success is True

        # ビューで全行・全カラムが取得できる
        rel = conn.execute("SELECT * FROM raw_sales ORDER BY id")
        cols = [d[0] for d in rel.description]
        rows = rel.fetchall()

        assert len(rows) == 6
        assert "id" in cols
        assert "name" in cols
        assert "amount" in cols
        assert "region" in cols
        assert "discount" in cols

    def test_missing_columns_are_null(self, pipeline, tmp_path):
        """後から追加されたカラムは、古いファイル由来の行ではNULLになること"""
        interactor, conn, _ = pipeline

        (tmp_path / "v1.csv").write_text("id,val\n1,A\n")
        (tmp_path / "v2.csv").write_text("id,val,extra\n2,B,hello\n")

        for f in ["v1.csv", "v2.csv"]:
            interactor.run(
                IngestFileInput(file_path=str(tmp_path / f), dataset_name="dataset")
            )

        rows = conn.execute(
            "SELECT id, extra FROM raw_dataset ORDER BY id"
        ).fetchall()

        assert rows[0] == (1, None)   # v1.csv には extra がないので NULL
        assert rows[1] == (2, "hello")

    def test_column_order_does_not_matter(self, pipeline, tmp_path):
        """カラムの順番が違っても正しく名前で統合されること"""
        interactor, conn, _ = pipeline

        (tmp_path / "a.csv").write_text("x,y\n1,2\n")
        (tmp_path / "b.csv").write_text("y,x\n4,3\n")  # カラム順が逆

        for f in ["a.csv", "b.csv"]:
            interactor.run(
                IngestFileInput(file_path=str(tmp_path / f), dataset_name="coords")
            )

        rows = conn.execute(
            "SELECT x, y FROM raw_coords ORDER BY x"
        ).fetchall()

        assert rows[0] == (1, 2)
        assert rows[1] == (3, 4)  # 逆順でも正しく x=3, y=4 になる

    def test_all_csv_files_ingested_independently(self, pipeline, tmp_path):
        """各CSVは独立してレジストリに記録されること"""
        interactor, _, view_manager = pipeline
        registry = interactor._registry

        for i in range(3):
            f = tmp_path / f"file_{i}.csv"
            f.write_text(f"col\nvalue_{i}\n")
            interactor.run(IngestFileInput(file_path=str(f), dataset_name="multi"))

        records = registry.list_records()
        assert len(records) == 3
        assert all(r.status == "completed" for r in records)
        assert "raw_multi" in view_manager.list_views()

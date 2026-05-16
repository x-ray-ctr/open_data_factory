"""DuckDB External View マネージャー"""

import re
from pathlib import Path

from app.infrastructure.duckdb.connection import DuckDBConnection

_SAFE_NAME = re.compile(r"^[a-zA-Z0-9_]+$")


class DuckDBViewManager:
    """Rawレイヤーの Parquet ファイルに対する DuckDB ビューを管理する"""

    def __init__(self, connection: DuckDBConnection, raw_base_path: str):
        self._db = connection
        self._raw_base = Path(raw_base_path).resolve()

    def ensure_view(self, dataset_name: str) -> None:
        """dataset_name に対応する raw_{dataset_name} ビューを作成/更新する"""
        if not _SAFE_NAME.match(dataset_name):
            raise ValueError(f"Invalid dataset name for SQL view: {dataset_name!r}")
        dataset_path = self._raw_base / dataset_name
        if not dataset_path.exists():
            return
        # グロブパスを文字列で埋め込む（dataset_nameは検証済み）
        glob_path = str(dataset_path / "**" / "*.parquet")
        self._db.execute(
            f"CREATE OR REPLACE VIEW raw_{dataset_name} AS "
            f"SELECT * FROM read_parquet('{glob_path}', union_by_name = true)"
        )

    def list_views(self) -> list[str]:
        rows = self._db.execute(
            "SELECT table_name FROM information_schema.views "
            "WHERE table_schema = 'main' AND table_name LIKE 'raw_%'"
        ).fetchall()
        return [row[0] for row in rows]

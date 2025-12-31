"""HTTP経由でデータセットを読み込む実装"""

import polars as pl

from app.domain.value_object.dataset import Dataset
from app.usecase.ports.output.dataset_loader import DatasetLoader


class HttpDatasetLoader(DatasetLoader):
    """HTTP経由でデータセットを読み込む実装"""

    def load(self, dataset: Dataset) -> pl.DataFrame:
        """
        データセットをHTTP経由で読み込む

        Args:
            dataset: データセットの値オブジェクト

        Returns:
            読み込んだデータフレーム
        """
        # HTTP経由でCSVを読み込む
        # 実際の実装では、認証やリトライロジックを追加
        df = pl.read_csv(dataset.url)
        return df

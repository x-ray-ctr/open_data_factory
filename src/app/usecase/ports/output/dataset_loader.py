"""データセットローダーのポート（出力）"""

from abc import ABC, abstractmethod
import polars as pl
from app.domain.value_object.dataset import Dataset


class DatasetLoader(ABC):
    """データセットを読み込むポート"""

    @abstractmethod
    def load(self, dataset: Dataset) -> pl.DataFrame:
        """
        データセットを読み込む

        Args:
            dataset: データセットの値オブジェクト

        Returns:
            読み込んだデータフレーム
        """
        pass

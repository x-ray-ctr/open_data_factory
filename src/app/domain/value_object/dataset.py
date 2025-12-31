"""データセットの値オブジェクト"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Dataset:
    """データセットを表す値オブジェクト"""
    url: str

    def __post_init__(self):
        if not self.url:
            raise ValueError("Dataset URL must not be empty")


"""分析実行の出力DTO"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RunAnalysisOutput:
    """分析実行の出力データ"""

    result_path: str
    success: bool
    message: str = ""

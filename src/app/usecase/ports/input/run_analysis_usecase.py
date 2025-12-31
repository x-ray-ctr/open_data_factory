"""分析実行ユースケースのポート（入力）"""

from abc import ABC, abstractmethod

from app.usecase.dto.run_analysis_input import RunAnalysisInput
from app.usecase.dto.run_analysis_output import RunAnalysisOutput


class RunAnalysisUseCase(ABC):
    """分析実行ユースケースのポート"""

    @abstractmethod
    def run(self, input: RunAnalysisInput) -> RunAnalysisOutput:
        """
        分析を実行する

        Args:
            input: 分析実行の入力

        Returns:
            分析実行の出力
        """
        pass

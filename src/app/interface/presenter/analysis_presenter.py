"""分析結果のプレゼンター"""

from app.usecase.dto.run_analysis_output import RunAnalysisOutput
from typing import Dict, Any


class AnalysisPresenter:
    """分析結果をAPIレスポンス形式に変換するプレゼンター"""

    @staticmethod
    def present(output: RunAnalysisOutput) -> Dict[str, Any]:
        """
        分析結果をAPIレスポンス形式に変換する

        Args:
            output: 分析実行の出力

        Returns:
            APIレスポンス形式の辞書
        """
        return {
            "success": output.success,
            "result_path": output.result_path if output.success else None,
            "message": output.message,
        }

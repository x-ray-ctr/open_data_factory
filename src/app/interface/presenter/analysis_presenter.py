"""分析結果のプレゼンター"""

from typing import Any

from app.usecase.dto.run_analysis_output import RunAnalysisOutput


class AnalysisPresenter:
    """分析結果をAPIレスポンス形式に変換するプレゼンター"""

    @staticmethod
    def present(output: RunAnalysisOutput) -> dict[str, Any]:
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

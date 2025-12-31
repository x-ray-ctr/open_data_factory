"""結果リポジトリのポート（出力）"""
from abc import ABC, abstractmethod
from app.domain.model.analysis_result import AnalysisResult
from app.domain.value_object.target_date import TargetDate


class ResultRepository(ABC):
    """分析結果を保存するポート"""
    
    @abstractmethod
    def save(self, result: AnalysisResult, target_date: TargetDate) -> str:
        """
        分析結果を保存する
        
        Args:
            result: 分析結果
            target_date: 対象日付
            
        Returns:
            保存先のパス
        """
        pass


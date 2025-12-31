"""分析サービスのドメインロジック"""
import polars as pl
from app.domain.model.analysis_result import AnalysisResult


def analyze(df: pl.DataFrame) -> AnalysisResult:
    """
    データフレームを分析して結果を返す純粋関数
    
    Args:
        df: 入力データフレーム
        
    Returns:
        分析結果
    """
    # 例: カテゴリごとの合計値を計算
    result_df = (
        df.group_by("category")
        .agg(pl.sum("value").alias("total"))
        if "category" in df.columns and "value" in df.columns
        else df
    )
    
    return AnalysisResult(data=result_df)


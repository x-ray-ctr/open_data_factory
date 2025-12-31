"""分析実行のインタラクター"""
from app.usecase.ports.input.run_analysis_usecase import RunAnalysisUseCase
from app.usecase.ports.output.dataset_loader import DatasetLoader
from app.usecase.ports.output.result_repository import ResultRepository
from app.usecase.dto.run_analysis_input import RunAnalysisInput
from app.usecase.dto.run_analysis_output import RunAnalysisOutput
from app.domain.service.analyze_service import analyze


class RunAnalysisInteractor(RunAnalysisUseCase):
    """分析実行のインタラクター実装"""
    
    def __init__(
        self,
        loader: DatasetLoader,
        repository: ResultRepository,
    ):
        """
        初期化
        
        Args:
            loader: データセットローダー
            repository: 結果リポジトリ
        """
        self.loader = loader
        self.repository = repository
    
    def run(self, input: RunAnalysisInput) -> RunAnalysisOutput:
        """
        分析を実行する
        
        Args:
            input: 分析実行の入力
            
        Returns:
            分析実行の出力
        """
        try:
            # データセットを読み込む
            df = self.loader.load(input.dataset)
            
            # 分析を実行
            result = analyze(df)
            
            # 結果を保存
            result_path = self.repository.save(result, input.target_date)
            
            return RunAnalysisOutput(
                result_path=result_path,
                success=True,
                message="Analysis completed successfully"
            )
        except Exception as e:
            return RunAnalysisOutput(
                result_path="",
                success=False,
                message=f"Analysis failed: {str(e)}"
            )


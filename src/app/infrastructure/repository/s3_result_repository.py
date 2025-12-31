"""S3に結果を保存する実装"""

from app.usecase.ports.output.result_repository import ResultRepository
from app.domain.model.analysis_result import AnalysisResult
from app.domain.value_object.target_date import TargetDate
from app.infrastructure.config.settings import Settings


class S3ResultRepository(ResultRepository):
    """S3に結果を保存する実装"""

    def __init__(self, settings: Settings):
        """
        初期化

        Args:
            settings: アプリケーション設定
        """
        self.settings = settings

    def save(self, result: AnalysisResult, target_date: TargetDate) -> str:
        """
        分析結果をS3に保存する

        Args:
            result: 分析結果
            target_date: 対象日付

        Returns:
            保存先のパス
        """
        # S3パスを構築
        s3_path = (
            f"s3://{self.settings.s3_bucket}/{self.settings.s3_prefix}/{target_date}/result.parquet"
        )

        # Parquet形式で保存
        # 実際の実装では、boto3やs3fsを使用
        # ここでは例として、ローカルファイルシステムに保存する想定
        local_path = f"/tmp/{target_date}/result.parquet"
        result.data.write_parquet(local_path)

        # TODO: 実際のS3へのアップロード処理を実装
        # import boto3
        # s3_client = boto3.client('s3')
        # s3_client.upload_file(local_path, self.settings.s3_bucket, ...)

        return s3_path

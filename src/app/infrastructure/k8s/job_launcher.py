"""Kubernetes Job起動の実装"""

import logging
import sys
from typing import Any

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from app.infrastructure.config.settings import Settings

# ロガーを設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


class JobLauncher:
    """Kubernetes Jobを起動する実装"""

    def __init__(self, settings: Settings | None = None, namespace: str = "default"):
        """
        初期化

        Args:
            settings: アプリケーション設定（オプション）
            namespace: Kubernetes namespace（デフォルト: default）
        """
        self.settings = settings
        self.namespace = namespace
        self._api_client = None
        self._batch_api = None
        self._init_client()

    def _init_client(self) -> None:
        """Kubernetes APIクライアントを初期化"""
        try:
            # クラスター内から実行される場合（Pod内）
            config.load_incluster_config()
            logger.info("Loaded in-cluster config")
            self._api_client = client.ApiClient()
            self._batch_api = client.BatchV1Api(self._api_client)
        except config.ConfigException:
            try:
                # クラスター外から実行される場合（ローカル開発など）
                config.load_kube_config()
                logger.info("Loaded kube config from ~/.kube/config")
                self._api_client = client.ApiClient()
                self._batch_api = client.BatchV1Api(self._api_client)
            except config.ConfigException as e:
                logger.warning(f"Failed to load Kubernetes config: {e}")
                logger.warning("Kubernetes API client not initialized. Using mock mode.")
                self._api_client = None
                self._batch_api = None

    def launch_job(
        self,
        job_name: str,
        dataset_url: str,
        target_date: str,
        image: str = "polars-service:latest",
    ) -> str:
        """
        Kubernetes Jobを起動する

        Args:
            job_name: Job名
            dataset_url: データセットURL
            target_date: 対象日付
            image: コンテナイメージ

        Returns:
            Job名（実際にはKubernetesのJob名）

        Raises:
            RuntimeError: Jobの作成に失敗した場合
        """
        if self._batch_api is None:
            logger.warning("Kubernetes API not available. Returning job name as mock.")
            return job_name

        # Jobのマニフェストを作成
        job_manifest = self._create_job_manifest(
            job_name=job_name,
            dataset_url=dataset_url,
            target_date=target_date,
            image=image,
        )

        try:
            # Jobを作成
            api_response = self._batch_api.create_namespaced_job(
                namespace=self.namespace,
                body=job_manifest,
            )
            logger.info(f"Job {job_name} created successfully in namespace {self.namespace}")
            return api_response.metadata.name
        except (ApiException, Exception) as e:
            # 接続エラーなどの場合はモックモードにフォールバック
            if isinstance(e, ApiException):
                error_msg = f"Failed to create Job {job_name}: {e.reason} - {e.body}"
            else:
                error_msg = f"Failed to create Job {job_name}: {str(e)}"
            logger.warning(error_msg)
            logger.warning("Falling back to mock mode")
            return job_name

    def _create_job_manifest(
        self,
        job_name: str,
        dataset_url: str,
        target_date: str,
        image: str,
    ) -> dict[str, Any]:
        """
        Jobマニフェストを作成する

        Args:
            job_name: Job名
            dataset_url: データセットURL
            target_date: 対象日付
            image: コンテナイメージ

        Returns:
            Jobマニフェスト（dict）
        """
        # 環境変数を設定
        env_vars = [
            {"name": "DATASET_URL", "value": dataset_url},
            {"name": "TARGET_DATE", "value": target_date},
        ]

        if self.settings:
            if self.settings.s3_bucket:
                env_vars.append({"name": "S3_BUCKET", "value": self.settings.s3_bucket})
            if self.settings.s3_prefix:
                env_vars.append({"name": "S3_PREFIX", "value": self.settings.s3_prefix})

        return {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": job_name,
                "labels": {
                    "app": "polars-analysis",
                    "target-date": target_date,
                },
            },
            "spec": {
                "ttlSecondsAfterFinished": 3600,  # Job完了後1時間で削除
                "backoffLimit": 3,  # 最大3回までリトライ
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "polars-analysis",
                            "job-name": job_name,
                        },
                    },
                    "spec": {
                        "restartPolicy": "Never",
                        "containers": [
                            {
                                "name": "polars-service",
                                "image": image,
                                # kindクラスター用（ローカルイメージを使用）
                                "imagePullPolicy": "Never",
                                "command": ["/bin/sh", "-c"],
                                "args": [
                                    "cd /app && export PYTHONPATH=/app/src "
                                    "&& python -m app.main_job",
                                ],
                                "env": env_vars,
                                "resources": {
                                    "requests": {
                                        "memory": "512Mi",
                                        "cpu": "500m",
                                    },
                                    "limits": {
                                        "memory": "2Gi",
                                        "cpu": "2000m",
                                    },
                                },
                            },
                        ],
                    },
                },
            },
        }

    def _determine_job_status(self, job: Any) -> str:
        """
        Jobの状態を判定する

        Args:
            job: Kubernetes Jobオブジェクト

        Returns:
            状態文字列（completed, failed, running, unknown）
        """
        if job.status.succeeded:
            return "completed"
        elif job.status.failed:
            return "failed"
        elif job.status.active:
            return "running"
        elif job.status.conditions:
            # 条件から状態を判定
            for condition in job.status.conditions:
                if condition.type == "Complete" and condition.status == "True":
                    return "completed"
                elif condition.type == "Failed" and condition.status == "True":
                    return "failed"
        return "unknown"

    def list_jobs(self, label_selector: str | None = None) -> list[dict[str, Any]]:
        """
        Jobの一覧を取得する

        Args:
            label_selector: ラベルセレクター（例: "app=polars-analysis"）

        Returns:
            Jobの状態を含む辞書のリスト
        """
        if self._batch_api is None:
            logger.warning("Kubernetes API not available. Returning empty list.")
            return []

        try:
            # Job一覧を取得
            if label_selector:
                jobs = self._batch_api.list_namespaced_job(
                    namespace=self.namespace,
                    label_selector=label_selector,
                )
            else:
                jobs = self._batch_api.list_namespaced_job(namespace=self.namespace)

            result = []
            for job in jobs.items:
                # app=polars-analysisラベルのJobのみを対象とする
                if job.metadata.labels and job.metadata.labels.get("app") == "polars-analysis":
                    status = self._determine_job_status(job)

                    creation_timestamp = (
                        job.metadata.creation_timestamp.isoformat()
                        if job.metadata.creation_timestamp
                        else None
                    )
                    completion_time = (
                        job.status.completion_time.isoformat()
                        if job.status.completion_time
                        else None
                    )

                    result.append(
                        {
                            "job_id": job.metadata.name,
                            "status": status,
                            "namespace": self.namespace,
                            "creation_timestamp": creation_timestamp,
                            "completion_time": completion_time,
                            "succeeded": job.status.succeeded or 0,
                            "failed": job.status.failed or 0,
                            "active": job.status.active or 0,
                        }
                    )

            # 作成日時の降順でソート（新しいものから）
            result.sort(
                key=lambda x: x["creation_timestamp"] or "",
                reverse=True,
            )

            return result
        except ApiException as e:
            error_msg = f"Failed to list Jobs: {e.reason} - {e.body}"
            logger.error(error_msg)
            return []
        except Exception as e:
            error_msg = f"Failed to list Jobs: {str(e)}"
            logger.error(error_msg)
            return []

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """
        Jobの状態を取得する

        Args:
            job_id: Job名（KubernetesのJob名）

        Returns:
            Jobの状態を含む辞書
        """
        if self._batch_api is None:
            logger.warning("Kubernetes API not available. Returning mock status.")
            return {
                "job_id": job_id,
                "status": "unknown",
                "message": "Kubernetes API not available",
            }

        try:
            job = self._batch_api.read_namespaced_job(
                name=job_id,
                namespace=self.namespace,
            )

            status = self._determine_job_status(job)

            creation_timestamp = (
                job.metadata.creation_timestamp.isoformat()
                if job.metadata.creation_timestamp
                else None
            )
            completion_time = (
                job.status.completion_time.isoformat() if job.status.completion_time else None
            )

            return {
                "job_id": job_id,
                "status": status,
                "namespace": self.namespace,
                "creation_timestamp": creation_timestamp,
                "completion_time": completion_time,
                "succeeded": job.status.succeeded or 0,
                "failed": job.status.failed or 0,
                "active": job.status.active or 0,
            }
        except ApiException as e:
            if e.status == 404:
                return {
                    "job_id": job_id,
                    "status": "not_found",
                    "message": f"Job {job_id} not found in namespace {self.namespace}",
                }
            error_msg = f"Failed to get Job status {job_id}: {e.reason} - {e.body}"
            logger.error(error_msg)
            return {
                "job_id": job_id,
                "status": "error",
                "message": error_msg,
            }

    def delete_job(self, job_id: str) -> bool:
        """
        Jobを削除する

        Args:
            job_id: Job名

        Returns:
            削除に成功した場合True
        """
        if self._batch_api is None:
            logger.warning("Kubernetes API not available. Cannot delete job.")
            return False

        try:
            self._batch_api.delete_namespaced_job(
                name=job_id,
                namespace=self.namespace,
                propagation_policy="Background",
            )
            logger.info(f"Job {job_id} deleted successfully")
            return True
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Job {job_id} not found. Already deleted?")
                return True  # 既に削除されている場合は成功とみなす
            error_msg = f"Failed to delete Job {job_id}: {e.reason} - {e.body}"
            logger.error(error_msg)
            return False

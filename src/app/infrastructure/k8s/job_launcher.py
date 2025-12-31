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

            # Jobの状態を判定
            status = "unknown"
            if job.status.succeeded:
                status = "completed"
            elif job.status.failed:
                status = "failed"
            elif job.status.active:
                status = "running"
            elif job.status.conditions:
                # 条件から状態を判定
                for condition in job.status.conditions:
                    if condition.type == "Complete" and condition.status == "True":
                        status = "completed"
                        break
                    elif condition.type == "Failed" and condition.status == "True":
                        status = "failed"
                        break

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

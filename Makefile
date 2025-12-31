.PHONY: dev job install test lint fmt notebook setup-k8s build-image load-image clean-k8s reset-k8s clean-image

# 開発用: APIサーバーを起動
dev:
	uv run python -m app.main_api

# K8s Jobを実行
job:
	uv run python -m app.main_job

# 依存関係をインストール
install:
	uv sync

# テストを実行
test:
	uv run pytest

# リンターを実行
lint:
	uv run ruff check src/

# コードフォーマット
fmt:
	uv run ruff format src/

# リンターとフォーマットを同時に実行
check: lint fmt

# Jupyter Notebookを起動
notebook:
	uv run jupyter notebook notebooks/

# Kubernetesクラスターのセットアップ
setup-k8s:
	@echo "Setting up Kubernetes cluster with kind..."
	@if ! command -v kind >/dev/null 2>&1; then \
		echo "kind is not installed. Installing..."; \
		brew install kind; \
	fi
	@if kind get clusters | grep -q polars-analysis; then \
		echo "Cluster 'polars-analysis' already exists"; \
	else \
		kind create cluster --name polars-analysis; \
	fi
	@echo "Kubernetes cluster is ready!"

# Dockerイメージをビルド
build-image:
	docker build -t polars-service:latest .

# Dockerイメージをkindクラスターにロード
load-image: build-image
	kind load docker-image polars-service:latest --name polars-analysis

# Kubernetesクラスターを削除
clean-k8s:
	@echo "Deleting Kubernetes cluster..."
	@if kind get clusters | grep -q polars-analysis; then \
		kind delete cluster --name polars-analysis; \
		echo "Cluster 'polars-analysis' deleted"; \
	else \
		echo "Cluster 'polars-analysis' does not exist"; \
	fi

# Kubernetesクラスターをリセット（削除して再作成）
reset-k8s: clean-k8s setup-k8s
	@echo "Kubernetes cluster has been reset!"

# Dockerイメージを削除
clean-image:
	@echo "Deleting Docker image..."
	@if docker images | grep -q polars-service; then \
		docker rmi polars-service:latest || true; \
		echo "Docker image deleted"; \
	else \
		echo "Docker image does not exist"; \
	fi
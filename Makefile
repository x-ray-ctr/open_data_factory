.PHONY: dev job install test lint fmt notebook

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
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

# テストを実行（今後追加予定）
test:
	@echo "Tests not implemented yet"

# リンターを実行（今後追加予定）
lint:
	@echo "Linter not implemented yet"

# コードフォーマット（今後追加予定）
fmt:
	@echo "Formatter not implemented yet"

# Jupyter Notebookを起動
notebook:
	uv run jupyter notebook notebooks/
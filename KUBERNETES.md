# Kubernetes コマンドリファレンス

このプロジェクトで使用するKubernetes関連のコマンド一覧です。

## クラスター管理

### kindクラスターの作成

```bash
# クラスターを作成
kind create cluster --name polars-analysis

# クラスターの状態を確認
kubectl cluster-info --context kind-polars-analysis

# ノードの状態を確認
kubectl get nodes
```

### クラスターの削除

```bash
# クラスターを削除
kind delete cluster --name polars-analysis
```

## Dockerイメージ管理

### イメージのビルド

```bash
# Dockerイメージをビルド
docker build -t polars-service:latest .

# イメージをkindクラスターにロード
kind load docker-image polars-service:latest --name polars-analysis
```

### イメージの確認

```bash
# ローカルのDockerイメージを確認
docker images | grep polars-service

# kindクラスター内のイメージを確認
kind get nodes --name polars-analysis | xargs -I {} docker exec {} crictl images | grep polars
```

## Job管理

### Jobの作成（API経由）

```bash
# Jobを作成
curl -X POST "http://localhost:8000/analysis/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_url": "https://raw.githubusercontent.com/pola-rs/polars/main/examples/datasets/foods1.csv",
    "target_date": "2024-01-06"
  }'
```

### Jobの状態確認

```bash
# すべてのJobを確認
kubectl get jobs

# 特定のJobの詳細を確認
kubectl describe job analysis-2024-01-06

# API経由でJobの状態を確認
curl "http://localhost:8000/analysis/jobs/analysis-2024-01-06"
```

### Jobの削除

```bash
# 特定のJobを削除
kubectl delete job analysis-2024-01-06

# すべての完了したJobを削除
kubectl delete jobs --field-selector status.successful=1

# すべての失敗したJobを削除
kubectl delete jobs --field-selector status.failed=1
```

## Pod管理

### Podの確認

```bash
# すべてのPodを確認
kubectl get pods

# 特定のJobに関連するPodを確認
kubectl get pods -l job-name=analysis-2024-01-06

# Podの詳細を確認
kubectl describe pod <pod-name>
```

### Podのログ

```bash
# Jobのログを確認
kubectl logs job/analysis-2024-01-06

# 特定のPodのログを確認
kubectl logs <pod-name>

# ログをリアルタイムで確認（フォロー）
kubectl logs -f job/analysis-2024-01-06

# 最新のN行を確認
kubectl logs job/analysis-2024-01-06 --tail=50
```

### Podの削除

```bash
# 特定のPodを削除
kubectl delete pod <pod-name>

# すべての完了したPodを削除
kubectl delete pods --field-selector status.phase=Succeeded
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. ImagePullBackOffエラー

```bash
# Podの詳細を確認
kubectl describe pod <pod-name>

# イメージが正しくロードされているか確認
kind get nodes --name polars-analysis | xargs -I {} docker exec {} crictl images | grep polars

# イメージを再ロード
kind load docker-image polars-service:latest --name polars-analysis
```

#### 2. Podが起動しない

```bash
# Podのイベントを確認
kubectl describe pod <pod-name> | grep -A 10 "Events:"

# Podのログを確認
kubectl logs <pod-name>

# コンテナ内でコマンドを実行（デバッグ用）
kubectl exec -it <pod-name> -- /bin/sh
```

#### 3. Jobが失敗する

```bash
# 失敗したJobのログを確認
kubectl logs job/<job-name>

# Jobの詳細を確認
kubectl describe job <job-name>

# 失敗したPodのログを確認
kubectl get pods -l job-name=<job-name>
kubectl logs <failed-pod-name>
```

## 便利なコマンド

### リソースの一括確認

```bash
# すべてのリソースを確認
kubectl get all

# JobとPodを同時に確認
kubectl get jobs,pods
```

### リソースのクリーンアップ

```bash
# すべてのJobを削除
kubectl delete jobs --all

# すべてのPodを削除
kubectl delete pods --all

# 完了したリソースを一括削除
kubectl delete jobs --field-selector status.successful=1
kubectl delete pods --field-selector status.phase=Succeeded
```

### ログの確認

```bash
# 複数のPodのログを確認
kubectl logs -l job-name=analysis-2024-01-06

# すべてのコンテナのログを確認
kubectl logs job/analysis-2024-01-06 --all-containers=true
```

## 環境変数の確認

```bash
# Podの環境変数を確認
kubectl exec <pod-name> -- env

# 特定の環境変数を確認
kubectl exec <pod-name> -- printenv DATASET_URL
```

## クラスター情報

```bash
# クラスター情報を表示
kubectl cluster-info

# クラスターのバージョンを確認
kubectl version

# 利用可能なリソースを確認
kubectl api-resources
```

## よく使うコマンドのエイリアス（オプション）

`.zshrc`や`.bashrc`に追加すると便利です：

```bash
# エイリアスの設定例
alias kgj='kubectl get jobs'
alias kgp='kubectl get pods'
alias klj='kubectl logs job/'
alias kdj='kubectl describe job'
alias kdp='kubectl describe pod'
```

## 参考リンク

- [Kubernetes公式ドキュメント](https://kubernetes.io/docs/)
- [kind公式ドキュメント](https://kind.sigs.k8s.io/)
- [kubectlチートシート](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)


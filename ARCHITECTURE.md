# open_data_factory

以下は、これまでの議論を **ブレない最終形**として固定した
**「分析サービス（Polars × uv × Kubernetes Job）」の最終設計書**です。
このまま社内共有・レビュー・実装着手に使えるレベルで書いています。

---

# 分析サービス 最終設計書

**Polars × uv × Kubernetes Job ベース**

---

## 1. 目的・スコープ

### 目的

* オープンデータ等を用いた **再現可能・スケーラブルな分析を「サービス」として提供**する
* Notebook 依存を排除し、**計算をソフトウェア資産**として扱う

### 非目的

* 対話的探索環境の提供（Jupyter は開発補助に限定）
* 単発・手動実行前提の分析

---

## 2. 全体アーキテクチャ

```
[ Client / UI / 他サービス ]
            |
            v
        (REST API)
            |
     Job Trigger / Status
            |
            v
     ┌─────────────────┐
     │ Kubernetes Job  │  ← 計算責務
     │ (Polars + uv)   │
     └─────────────────┘
            |
            v
[ Object Storage (Parquet) ]
            |
            v
        (REST API)
            |
            v
[ 結果取得 / 可視化 / 二次利用 ]
```

---

## 3. 設計原則（非交渉）

1. **Notebook は本番構成要素に含めない**
2. **分析ロジックは純関数・副作用ゼロ**
3. **計算は Job、応答は API**
4. **状態は Storage にのみ存在**
5. **同一入力 → 同一出力（冪等性）**

---

## 4. コンポーネント責務

### 4.1 API（FastAPI）

**責務**

* Job の起動
* Job 状態の照会
* 結果パスの返却

**やらないこと**

* 分析計算
* 重いデータ処理

---

### 4.2 Kubernetes Job

**責務**

* 入力を受け取り分析を実行
* 結果を永続ストレージに保存
* 成功 or 失敗を Kubernetes に報告

**特徴**

* 一度きりの実行
* 自動リトライ
* 実行後 Pod は破棄

---

### 4.3 分析コア（Polars）

**責務**

* DataFrame → DataFrame の変換
* ビジネスルールの実装

**制約**

* I/O を持たない
* グローバル状態を持たない

---

### 4.4 ストレージ

**役割**

* Job の成果物を永続化
* API / 他サービスから再利用

**形式**

* 分析結果：Parquet
* メタ情報：必要に応じて DB

---

## 5. ディレクトリ構成（最終）

```
polars-service/
├── pyproject.toml
├── uv.lock
├── src/
│   └── app/
│       ├── core/          # 純粋分析ロジック
│       │   └── analyze.py
│       │
│       ├── infra/         # I/O 実装
│       │   └── http_loader.py
│       │
│       ├── jobs/          # K8s Job エントリ
│       │   └── daily.py
│       │
│       └── api/           # FastAPI
│           └── main.py
│
└── notebooks/             # 開発補助（最終削除対象）
    └── integration.ipynb
```

---

## 6. 処理フロー

### 6.1 Job 実行フロー

1. API が Job を作成
2. Kubernetes が Pod を起動
3. Job が入力パラメータを取得
4. 分析実行（Polars）
5. Parquet を Object Storage に保存
6. Job 完了

---

### 6.2 API フロー

* **Job 起動**

  ```
  POST /analysis/jobs
  ```
* **Job 状態確認**

  ```
  GET /analysis/jobs/{job_id}
  ```
* **結果取得**

  ```
  GET /analysis/results/{job_id}
  ```

---

## 7. Job 入出力設計

### 入力（Environment Variables）

* `DATASET_URL`
* `TARGET_DATE`
* その他分析パラメータ

### 出力（Parquet）

```
s3://analysis-results/
  └── daily/
      └── {date}/
          ├── summary.parquet
          └── stats.parquet
```

---

## 8. Kubernetes Job マニフェスト（例）

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: daily-analysis-20250101
spec:
  backoffLimit: 3
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: analysis
          image: polars-service:latest
          command: ["uv", "run", "python", "-m", "app.jobs.daily"]
          env:
            - name: DATASET_URL
              value: "https://example.com/open-data.csv"
            - name: TARGET_DATE
              value: "2025-01-01"
```

---

## 9. uv 採用理由

* 依存解決が高速・決定的
* Docker / CI / K8s で完全一致
* Notebook 非依存

---

## 10. Notebook の位置付け（明文化）

| 項目   | 扱い       |
| ---- | -------- |
| 本番   | 使用しない    |
| CI   | 使用しない    |
| 設計検証 | 一時的に使用   |
| 成果物  | `.py` のみ |

Notebook は **削除可能であることが設計完成の条件**。

---

## 11. 非機能要件

* 再実行可能性：◎
* スケーラビリティ：◎
* 障害耐性：K8s に委譲
* コスト制御：事前計算による最適化

---

## 12. 設計の要点（要約）

* **Job = 計算**
* **API = 制御**
* **Storage = 状態**
* **Notebook = 仮設足場**

---

## 13. 次フェーズ（実装ロードマップ）

1. Job 作成 API 実装
2. S3 / IRSA 設定
3. 結果取得 API
4. CronJob 化（定期実行）
5. Notebook 削除 (要検討)


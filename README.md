# 宅建10年ドリル

Python 3.11 + Streamlit で動作する宅建（宅地建物取引士）受験対策アプリです。過去10年分の問題を管理し、SM-2アルゴリズムを使った復習、成績ダッシュボード、模擬試験などを提供します。

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate  # Windows は .venv\\Scripts\\activate
pip install -r requirements.txt
```

### 初回データベース初期化

```bash
python -m db.seed
```

### Streamlit アプリの起動

```bash
python -m streamlit run app.py
```

ブラウザで <http://localhost:8501> を開きます。

## Docker での起動

```bash
docker-compose up --build
```

ホットリロードが有効で、ローカルの変更が即時反映されます。

## テスト

```bash
pytest
```

カバレッジレポートはターミナルに表示されます (80% 以上を維持してください)。

## Lint / Format

```bash
ruff check .
black .
```

## サンプルデータの取り込み

`data/sample_questions.csv` もしくは `data/sample_questions.json` を問題管理ページからアップロードできます。CLI で一括投入する場合は `python -m db.seed` を利用してください。

## トラブルシューティング

- **SQLite のロックエラー**: 実行中のアプリや他プロセスが DB を使用している場合に発生します。アプリを停止してから再実行してください。
- **pandas の dtype 警告**: CSV 取り込み時に型を明示的に指定することで回避できます。
- **Windows の文字コード問題**: CSV を UTF-8 (BOM なし) で保存してください。

## 注意事項

本リポジトリに含まれる問題データはダミーです。実データを利用する際は著作権に留意し、権利上問題のない範囲で管理してください。

# Python 3.11 slim イメージを使用
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージの更新と必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルをコピー
COPY requirements.txt .

# Python依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY main_clean.py .
COPY src/ ./src/

# 非rootユーザーを作成
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ポート8000を公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# アプリケーションを起動（開発時はホットリロード有効）
CMD ["uvicorn", "main_clean:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
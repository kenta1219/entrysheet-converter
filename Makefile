# ファイル変換Webアプリ - Makefile
# クリーンアーキテクチャ版

.PHONY: help init up down restart logs test test-clean build clean install dev status

# デフォルトターゲット
help: ## ヘルプを表示
	@echo "ファイル変換Webアプリ - 利用可能なコマンド:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# セットアップ
init: ## 初期セットアップ（Dockerイメージビルド）
	@echo "🚀 初期セットアップを開始します..."
	@if [ ! -f .env ]; then \
		echo "📋 環境変数ファイルを作成します..."; \
		cp .env.example .env; \
	fi
	@docker-compose build --no-cache
	@echo "✅ セットアップが完了しました"

# アプリケーション起動
up: ## Docker Composeでアプリケーションを起動
	@echo "🔄 アプリケーションを起動します..."
	@docker-compose up -d
	@echo "✅ アプリケーションが起動しました"
	@echo "🌐 アクセス: http://localhost:8080"

# アプリケーション停止
down: ## Docker Composeでアプリケーションを停止
	@echo "🛑 アプリケーションを停止します..."
	@docker-compose down
	@echo "✅ アプリケーションが停止しました"

# アプリケーション再起動
restart: down up ## アプリケーションを再起動

# ログ表示
logs: ## アプリケーションのログを表示
	@docker-compose logs -f file-converter-app

# ビルド
build: ## Dockerイメージをビルド
	@echo "🔨 Dockerイメージをビルドします..."
	@docker-compose build
	@echo "✅ ビルドが完了しました"

# ローカル開発環境
install: ## Python依存関係をインストール（ローカル開発用）
	@echo "📦 Python依存関係をインストールします..."
	@pip install -r requirements.txt
	@echo "✅ インストールが完了しました"

dev: install ## ローカル開発サーバーを起動
	@echo "🔧 開発サーバーを起動します..."
	@python main_clean.py

# テスト実行
test: ## 旧版テストを実行
	@echo "🧪 旧版テストを実行します..."
	@python test_app.py

test-clean: ## クリーンアーキテクチャ版テストを実行
	@echo "🧪 クリーンアーキテクチャ版テストを実行します..."
	@python test_clean_app.py

# ステータス確認
status: ## アプリケーションの状態を確認
	@echo "📊 アプリケーションの状態:"
	@docker-compose ps
	@echo ""
	@echo "🌐 ヘルスチェック:"
	@curl -s http://localhost:8080/health | python -m json.tool 2>/dev/null || echo "アプリケーションが起動していません"

# クリーンアップ
clean: ## 不要なDockerリソースを削除
	@echo "🧹 クリーンアップを実行します..."
	@docker-compose down --volumes --remove-orphans
	@docker system prune -f
	@echo "✅ クリーンアップが完了しました"

# 開発用コマンド
shell: ## アプリケーションコンテナにシェルでアクセス
	@docker-compose exec file-converter-app /bin/bash

# 設定確認
config: ## 現在の設定を表示
	@echo "⚙️  現在の設定:"
	@curl -s http://localhost:8080/config | python -m json.tool 2>/dev/null || echo "アプリケーションが起動していません"

# 本番用デプロイ
deploy: init up ## 本番環境にデプロイ（init + up）
	@echo "🚀 本番環境へのデプロイが完了しました"
	@echo "🌐 アクセス: http://localhost:8080"

# 全体テスト（両方のテストを実行）
test-all: test test-clean ## 全てのテストを実行

# ログディレクトリ作成
logs-dir: ## ログディレクトリを作成
	@mkdir -p logs
	@echo "📁 ログディレクトリを作成しました"

# 完全リセット
reset: clean init ## 完全リセット（全削除 + 再セットアップ）
	@echo "🔄 完全リセットが完了しました"
import os
import logging
from dataclasses import dataclass
from typing import Optional


# 定数定義
OUTPUT_FILENAME = "【電子マネー】包括代理加盟店店子申請フォーマット（割賦販売法対象外）.xlsx"


@dataclass
class AppConfig:
    """アプリケーション設定"""
    # ファイル処理設定
    max_file_size: int = 10485760  # 10MB
    
    # シート名設定
    source_sheet_name: str = "加盟店申込書_施設名"
    target_sheet_name: str = "店子申請一覧"
    
    # サーバー設定
    host: str = "0.0.0.0"
    port: int = 8000
    
    # ロギング設定
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 環境設定
    environment: str = "development"
    debug: bool = False
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """環境変数から設定を読み込み"""
        return cls(
            max_file_size=int(os.getenv("MAX_FILE_SIZE", "10485760")),
            source_sheet_name=os.getenv("SOURCE_SHEET_NAME", "加盟店申込書_施設名"),
            target_sheet_name=os.getenv("TARGET_SHEET_NAME", "店子申請一覧"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true"
        )
    
    def setup_logging(self):
        """ロギング設定を適用"""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format=self.log_format,
            force=True
        )


class ConfigManager:
    """設定管理クラス"""
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[AppConfig] = None
    
    def __new__(cls) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_config(self) -> AppConfig:
        """設定を取得（シングルトン）"""
        if self._config is None:
            self._config = AppConfig.from_env()
        return self._config
    
    def reload_config(self) -> AppConfig:
        """設定を再読み込み"""
        self._config = AppConfig.from_env()
        return self._config
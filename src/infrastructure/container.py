from ..application.batch_use_cases import BatchProcessingUseCase
from ..presentation.controllers.health_controller import HealthController
from ..presentation.controllers.web_controller import WebController
from ..presentation.controllers.batch_controller import BatchProcessingController
from .repositories import StructuredLoggerRepository
from .template_repository import TemplateRepository
from .config import AppConfig, ConfigManager


class HealthCheckUseCase:
    """ヘルスチェックユースケース"""
    
    def __init__(self, logger_repository: StructuredLoggerRepository):
        self._logger = logger_repository
    
    def check_health(self) -> dict:
        """ヘルスチェックを実行"""
        try:
            self._logger.log_info("ヘルスチェック実行")
            return {
                "status": "healthy",
                "timestamp": "2025-01-01T00:00:00Z",
                "version": "2.0.0"
            }
        except Exception as e:
            self._logger.log_error(f"ヘルスチェックエラー: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class DIContainer:
    """依存性注入コンテナ"""
    
    def __init__(self):
        self._config = ConfigManager().get_config()
        self._instances = {}
    
    def get_config(self) -> AppConfig:
        """設定を取得"""
        return self._config
    
    def get_logger_repository(self) -> StructuredLoggerRepository:
        """ログリポジトリを取得"""
        if 'logger_repository' not in self._instances:
            self._instances['logger_repository'] = StructuredLoggerRepository()
        return self._instances['logger_repository']
    
    def get_health_check_use_case(self) -> HealthCheckUseCase:
        """ヘルスチェックユースケースを取得"""
        if 'health_check_use_case' not in self._instances:
            self._instances['health_check_use_case'] = HealthCheckUseCase(
                self.get_logger_repository()
            )
        return self._instances['health_check_use_case']
    
    def get_health_controller(self) -> HealthController:
        """ヘルスコントローラーを取得"""
        if 'health_controller' not in self._instances:
            self._instances['health_controller'] = HealthController(
                self.get_health_check_use_case()
            )
        return self._instances['health_controller']
    
    def get_web_controller(self) -> WebController:
        """Webコントローラーを取得"""
        if 'web_controller' not in self._instances:
            self._instances['web_controller'] = WebController()
        return self._instances['web_controller']
    
    def get_template_repository(self) -> TemplateRepository:
        """テンプレートリポジトリを取得"""
        if 'template_repository' not in self._instances:
            self._instances['template_repository'] = TemplateRepository()
        return self._instances['template_repository']
    
    def get_batch_processing_use_case(self) -> BatchProcessingUseCase:
        """一括処理ユースケースを取得"""
        if 'batch_processing_use_case' not in self._instances:
            self._instances['batch_processing_use_case'] = BatchProcessingUseCase(
                self.get_template_repository()
            )
        return self._instances['batch_processing_use_case']
    
    def get_batch_processing_controller(self) -> BatchProcessingController:
        """一括処理コントローラーを取得"""
        if 'batch_processing_controller' not in self._instances:
            self._instances['batch_processing_controller'] = BatchProcessingController(
                self.get_batch_processing_use_case(),
                self.get_template_repository()
            )
        return self._instances['batch_processing_controller']
    


# グローバルコンテナインスタンス
container = DIContainer()
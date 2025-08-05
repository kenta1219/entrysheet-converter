from ..domain.services import (
    FileValidationService, DataExtractionService, DataWriteService
)
from ..application.use_cases import (
    FileProcessingUseCase, ConfigurationUseCase, HealthCheckUseCase
)
from ..presentation.controllers.file_controller import FileProcessingController
from ..presentation.controllers.health_controller import HealthController
from ..presentation.controllers.web_controller import WebController
from .repositories import (
    PandasXlsbReaderRepository, OpenpyxlXlsxWriterRepository,
    BasicFileValidatorRepository, StructuredLoggerRepository
)
from .config import AppConfig, ConfigManager


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
    
    def get_xlsb_reader_repository(self) -> PandasXlsbReaderRepository:
        """xlsb読み込みリポジトリを取得"""
        if 'xlsb_reader_repository' not in self._instances:
            self._instances['xlsb_reader_repository'] = PandasXlsbReaderRepository()
        return self._instances['xlsb_reader_repository']
    
    def get_xlsx_writer_repository(self) -> OpenpyxlXlsxWriterRepository:
        """xlsx書き込みリポジトリを取得"""
        if 'xlsx_writer_repository' not in self._instances:
            self._instances['xlsx_writer_repository'] = OpenpyxlXlsxWriterRepository()
        return self._instances['xlsx_writer_repository']
    
    def get_file_validator_repository(self) -> BasicFileValidatorRepository:
        """ファイルバリデーションリポジトリを取得"""
        if 'file_validator_repository' not in self._instances:
            self._instances['file_validator_repository'] = BasicFileValidatorRepository()
        return self._instances['file_validator_repository']
    
    def get_file_validation_service(self) -> FileValidationService:
        """ファイルバリデーションサービスを取得"""
        if 'file_validation_service' not in self._instances:
            self._instances['file_validation_service'] = FileValidationService(
                self.get_file_validator_repository(),
                self.get_logger_repository()
            )
        return self._instances['file_validation_service']
    
    def get_data_extraction_service(self) -> DataExtractionService:
        """データ抽出サービスを取得"""
        if 'data_extraction_service' not in self._instances:
            self._instances['data_extraction_service'] = DataExtractionService(
                self.get_xlsb_reader_repository(),
                self.get_logger_repository()
            )
        return self._instances['data_extraction_service']
    
    def get_data_write_service(self) -> DataWriteService:
        """データ書き込みサービスを取得"""
        if 'data_write_service' not in self._instances:
            self._instances['data_write_service'] = DataWriteService(
                self.get_xlsx_writer_repository(),
                self.get_logger_repository()
            )
        return self._instances['data_write_service']
    
    def get_file_processing_use_case(self) -> FileProcessingUseCase:
        """ファイル処理ユースケースを取得"""
        if 'file_processing_use_case' not in self._instances:
            self._instances['file_processing_use_case'] = FileProcessingUseCase(
                self.get_file_validation_service(),
                self.get_data_extraction_service(),
                self.get_data_write_service(),
                self.get_logger_repository(),
                self._config.max_file_size
            )
        return self._instances['file_processing_use_case']
    
    def get_configuration_use_case(self) -> ConfigurationUseCase:
        """設定ユースケースを取得"""
        if 'configuration_use_case' not in self._instances:
            self._instances['configuration_use_case'] = ConfigurationUseCase()
        return self._instances['configuration_use_case']
    
    def get_health_check_use_case(self) -> HealthCheckUseCase:
        """ヘルスチェックユースケースを取得"""
        if 'health_check_use_case' not in self._instances:
            self._instances['health_check_use_case'] = HealthCheckUseCase(
                self.get_logger_repository()
            )
        return self._instances['health_check_use_case']
    
    def get_file_processing_controller(self) -> FileProcessingController:
        """ファイル処理コントローラーを取得"""
        if 'file_processing_controller' not in self._instances:
            self._instances['file_processing_controller'] = FileProcessingController(
                self.get_file_processing_use_case(),
                self.get_configuration_use_case(),
                self._config
            )
        return self._instances['file_processing_controller']
    
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


# グローバルコンテナインスタンス
container = DIContainer()
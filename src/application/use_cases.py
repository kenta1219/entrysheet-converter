from typing import Tuple
from ..domain.entities import (
    FileInfo, ProcessingResult, ExtractionConfig, WriteConfig
)
from ..domain.services import (
    FileValidationService, DataExtractionService, DataWriteService
)
from ..domain.repositories import LoggerRepository
from ..infrastructure.config import OUTPUT_FILENAME


class FileProcessingUseCase:
    """ファイル処理ユースケース"""
    
    def __init__(
        self,
        validation_service: FileValidationService,
        extraction_service: DataExtractionService,
        write_service: DataWriteService,
        logger: LoggerRepository,
        max_file_size: int = 10485760  # 10MB
    ):
        self._validation_service = validation_service
        self._extraction_service = extraction_service
        self._write_service = write_service
        self._logger = logger
        self._max_file_size = max_file_size
    
    def process_files(
        self,
        xlsb_file: FileInfo,
        template_file: FileInfo,
        extraction_config: ExtractionConfig,
        write_config: WriteConfig
    ) -> ProcessingResult:
        """ファイル処理のメインユースケース"""
        
        self._logger.log_info("ファイル処理開始", 
                            xlsb_filename=xlsb_file.filename,
                            template_filename=template_file.filename)
        
        try:
            # 1. ファイルバリデーション
            validation_result = self._validate_files(xlsb_file, template_file)
            if not validation_result.success:
                return validation_result
            
            # 2. データ抽出
            extracted_data = self._extraction_service.extract_data(xlsb_file, extraction_config)
            
            # 3. 抽出データの検証
            if extracted_data.is_empty:
                error_msg = "xlsbファイルから指定されたセルにデータが見つかりません"
                self._logger.log_warning("抽出データなし",
                                       xlsb_filename=xlsb_file.filename)
                return ProcessingResult.error_result(error_msg)
            
            # 4. データ書き込み
            output_content = self._write_service.write_data(
                template_file, extracted_data, write_config
            )
            
            # 5. 成功結果を返す
            output_filename = OUTPUT_FILENAME
            
            self._logger.log_info("ファイル処理完了", 
                                output_filename=output_filename,
                                extracted_count=extracted_data.count)
            
            return ProcessingResult.success_result(
                output_filename, output_content, extracted_data.count
            )
            
        except Exception as e:
            error_msg = f"ファイル処理中にエラーが発生しました: {str(e)}"
            self._logger.log_error("予期しないエラー", 
                                 xlsb_filename=xlsb_file.filename,
                                 template_filename=template_file.filename,
                                 error=str(e))
            return ProcessingResult.error_result(error_msg)
    
    def _validate_files(self, xlsb_file: FileInfo, template_file: FileInfo) -> ProcessingResult:
        """ファイルバリデーション"""
        # xlsbファイルのバリデーション
        xlsb_validation = self._validation_service.validate_xlsb_file(
            xlsb_file, self._max_file_size
        )
        if not xlsb_validation.is_valid:
            return ProcessingResult.error_result(xlsb_validation.error_message)
        
        # テンプレートファイルのバリデーション
        template_validation = self._validation_service.validate_xlsx_file(
            template_file, self._max_file_size
        )
        if not template_validation.is_valid:
            return ProcessingResult.error_result(template_validation.error_message)
        
        return ProcessingResult.success_result("", b"", 0)


class ConfigurationUseCase:
    """設定管理ユースケース"""
    
    @staticmethod
    def create_extraction_config(
        target_sheet: str = "加盟店申込書_施設名"
    ) -> ExtractionConfig:
        """抽出設定を作成"""
        return ExtractionConfig(
            target_sheet=target_sheet
        )
    
    @staticmethod
    def create_write_config(
        target_sheet: str = "店子申請一覧",
        target_row: int = 14
    ) -> WriteConfig:
        """書き込み設定を作成"""
        return WriteConfig(
            target_sheet=target_sheet,
            target_row=target_row
        )


class HealthCheckUseCase:
    """ヘルスチェックユースケース"""
    
    def __init__(self, logger: LoggerRepository):
        self._logger = logger
    
    def check_health(self) -> dict:
        """アプリケーションの健康状態をチェック"""
        try:
            from datetime import datetime
            
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
            self._logger.log_info("ヘルスチェック実行", status="healthy")
            return health_status
            
        except Exception as e:
            self._logger.log_error("ヘルスチェックエラー", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }
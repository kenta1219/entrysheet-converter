from typing import List
from .entities import (
    FileInfo, ExtractedData, ProcessingResult, ValidationResult,
    ExtractionConfig, WriteConfig
)
from .repositories import (
    XlsbReaderRepository, XlsxWriterRepository, 
    FileValidatorRepository, LoggerRepository
)


class FileValidationService:
    """ファイルバリデーションドメインサービス"""
    
    def __init__(self, validator: FileValidatorRepository, logger: LoggerRepository):
        self._validator = validator
        self._logger = logger
    
    def validate_xlsb_file(self, file_info: FileInfo, max_size: int) -> ValidationResult:
        """xlsbファイルの総合バリデーション"""
        # 拡張子チェック
        if file_info.extension != '.xlsb':
            error_msg = f"xlsbファイルは.xlsb拡張子である必要があります: {file_info.filename}"
            self._logger.log_error("無効なxlsb拡張子", filename=file_info.filename)
            return ValidationResult.invalid(error_msg)
        
        # サイズチェック
        if not self._validator.validate_file_size(file_info, max_size):
            error_msg = f"xlsbファイルのサイズが制限を超えています: {file_info.size} bytes"
            self._logger.log_error("xlsbファイルサイズ超過", 
                                 filename=file_info.filename, size=file_info.size)
            return ValidationResult.invalid(error_msg)
        
        # ファイル形式チェック
        if not self._validator.validate_xlsb_file(file_info):
            error_msg = f"xlsbファイルの形式が無効です: {file_info.filename}"
            self._logger.log_error("無効なxlsb形式", filename=file_info.filename)
            return ValidationResult.invalid(error_msg)
        
        self._logger.log_info("xlsbファイルバリデーション成功", filename=file_info.filename)
        return ValidationResult.valid()
    
    def validate_xlsx_file(self, file_info: FileInfo, max_size: int) -> ValidationResult:
        """xlsxファイルの総合バリデーション"""
        # 拡張子チェック
        if file_info.extension not in ['.xlsx', '.xlsm']:
            error_msg = f"テンプレートファイルは.xlsxまたは.xlsm拡張子である必要があります: {file_info.filename}"
            self._logger.log_error("無効なテンプレート拡張子", filename=file_info.filename)
            return ValidationResult.invalid(error_msg)
        
        # サイズチェック
        if not self._validator.validate_file_size(file_info, max_size):
            error_msg = f"テンプレートファイルのサイズが制限を超えています: {file_info.size} bytes"
            self._logger.log_error("テンプレートファイルサイズ超過", 
                                 filename=file_info.filename, size=file_info.size)
            return ValidationResult.invalid(error_msg)
        
        # ファイル形式チェック
        if not self._validator.validate_xlsx_file(file_info):
            error_msg = f"テンプレートファイルの形式が無効です: {file_info.filename}"
            self._logger.log_error("無効なテンプレート形式", filename=file_info.filename)
            return ValidationResult.invalid(error_msg)
        
        self._logger.log_info("テンプレートファイルバリデーション成功", filename=file_info.filename)
        return ValidationResult.valid()


class DataExtractionService:
    """データ抽出ドメインサービス"""
    
    def __init__(self, reader: XlsbReaderRepository, logger: LoggerRepository):
        self._reader = reader
        self._logger = logger
    
    def extract_data(self, file_info: FileInfo, config: ExtractionConfig) -> ExtractedData:
        """xlsbファイルからデータを抽出"""
        try:
            self._logger.log_info("データ抽出開始",
                                filename=file_info.filename,
                                target_sheet=config.target_sheet,
                                cell_count=len(config.cell_references))
            
            extracted_data = self._reader.extract_data(file_info, config)
            
            if extracted_data.is_empty:
                self._logger.log_warning("抽出データなし",
                                       filename=file_info.filename,
                                       sheet=config.target_sheet)
            else:
                self._logger.log_info("データ抽出完了",
                                    filename=file_info.filename,
                                    extracted_count=extracted_data.count)
            
            return extracted_data
            
        except Exception as e:
            self._logger.log_error("データ抽出エラー", 
                                 filename=file_info.filename, 
                                 error=str(e))
            raise


class DataWriteService:
    """データ書き込みドメインサービス"""
    
    def __init__(self, writer: XlsxWriterRepository, logger: LoggerRepository):
        self._writer = writer
        self._logger = logger
    
    def write_data(self, template_file: FileInfo, data: ExtractedData, 
                   config: WriteConfig) -> bytes:
        """テンプレートファイルにデータを書き込み"""
        try:
            self._logger.log_info("データ書き込み開始", 
                                template_filename=template_file.filename,
                                data_count=data.count,
                                target_sheet=config.target_sheet,
                                target_row=config.target_row)
            
            result_content = self._writer.write_data(template_file, data, config)
            
            self._logger.log_info("データ書き込み完了", 
                                template_filename=template_file.filename,
                                written_count=data.count)
            
            return result_content
            
        except Exception as e:
            self._logger.log_error("データ書き込みエラー", 
                                 template_filename=template_file.filename, 
                                 error=str(e))
            raise
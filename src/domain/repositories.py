from abc import ABC, abstractmethod
from typing import List
from .entities import FileInfo, ExtractedData, ExtractionConfig, WriteConfig


class XlsbReaderRepository(ABC):
    """xlsbファイル読み込みリポジトリインターフェース"""
    
    @abstractmethod
    def extract_data(self, file_info: FileInfo, config: ExtractionConfig) -> ExtractedData:
        """xlsbファイルからデータを抽出"""
        pass


class XlsxWriterRepository(ABC):
    """xlsxファイル書き込みリポジトリインターフェース"""
    
    @abstractmethod
    def write_data(self, template_file: FileInfo, data: ExtractedData, 
                   config: WriteConfig) -> bytes:
        """テンプレートファイルにデータを書き込み、結果を返す"""
        pass


class FileValidatorRepository(ABC):
    """ファイルバリデーションリポジトリインターフェース"""
    
    @abstractmethod
    def validate_xlsb_file(self, file_info: FileInfo) -> bool:
        """xlsbファイルの妥当性を検証"""
        pass
    
    @abstractmethod
    def validate_xlsx_file(self, file_info: FileInfo) -> bool:
        """xlsxファイルの妥当性を検証"""
        pass
    
    @abstractmethod
    def validate_file_size(self, file_info: FileInfo, max_size: int) -> bool:
        """ファイルサイズを検証"""
        pass


class LoggerRepository(ABC):
    """ログ出力リポジトリインターフェース"""
    
    @abstractmethod
    def log_info(self, message: str, **kwargs):
        """情報ログを出力"""
        pass
    
    @abstractmethod
    def log_error(self, message: str, **kwargs):
        """エラーログを出力"""
        pass
    
    @abstractmethod
    def log_warning(self, message: str, **kwargs):
        """警告ログを出力"""
        pass
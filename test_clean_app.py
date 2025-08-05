import unittest
from unittest.mock import Mock, patch
import tempfile
import os
from fastapi.testclient import TestClient

from src.domain.entities import (
    FileInfo, ExtractedData, ProcessingResult, ValidationResult,
    ExtractionConfig, WriteConfig
)
from src.domain.services import (
    FileValidationService, DataExtractionService, DataWriteService
)
from src.application.use_cases import (
    FileProcessingUseCase, ConfigurationUseCase, HealthCheckUseCase
)
from src.infrastructure.repositories import (
    PandasXlsbReaderRepository, OpenpyxlXlsxWriterRepository,
    BasicFileValidatorRepository, StructuredLoggerRepository
)
from src.infrastructure.config import AppConfig
from main_clean import create_app


class TestDomainEntities(unittest.TestCase):
    """ドメインエンティティのテスト"""
    
    def test_file_info_extension(self):
        """FileInfoの拡張子取得テスト"""
        file_info = FileInfo("test.xlsb", b"content", 100)
        self.assertEqual(file_info.extension, ".xlsb")
    
    def test_extracted_data_properties(self):
        """ExtractedDataのプロパティテスト"""
        data = ExtractedData(["data1", "data2"], "sheet1", "F")
        self.assertEqual(data.count, 2)
        self.assertFalse(data.is_empty)
        
        empty_data = ExtractedData([], "sheet1", "F")
        self.assertEqual(empty_data.count, 0)
        self.assertTrue(empty_data.is_empty)
    
    def test_processing_result_factory_methods(self):
        """ProcessingResultのファクトリメソッドテスト"""
        success_result = ProcessingResult.success_result("output.xlsx", b"content", 5)
        self.assertTrue(success_result.success)
        self.assertEqual(success_result.extracted_count, 5)
        
        error_result = ProcessingResult.error_result("Error message")
        self.assertFalse(error_result.success)
        self.assertEqual(error_result.error_message, "Error message")
    
    def test_validation_result_factory_methods(self):
        """ValidationResultのファクトリメソッドテスト"""
        valid_result = ValidationResult.valid()
        self.assertTrue(valid_result.is_valid)
        self.assertIsNone(valid_result.error_message)
        
        invalid_result = ValidationResult.invalid("Invalid file")
        self.assertFalse(invalid_result.is_valid)
        self.assertEqual(invalid_result.error_message, "Invalid file")


class TestDomainServices(unittest.TestCase):
    """ドメインサービスのテスト"""
    
    def setUp(self):
        self.mock_validator = Mock(spec=BasicFileValidatorRepository)
        self.mock_logger = Mock(spec=StructuredLoggerRepository)
        self.mock_reader = Mock(spec=PandasXlsbReaderRepository)
        self.mock_writer = Mock(spec=OpenpyxlXlsxWriterRepository)
    
    def test_file_validation_service_valid_xlsb(self):
        """ファイルバリデーションサービス（有効なxlsb）のテスト"""
        self.mock_validator.validate_file_size.return_value = True
        self.mock_validator.validate_xlsb_file.return_value = True
        
        service = FileValidationService(self.mock_validator, self.mock_logger)
        file_info = FileInfo("test.xlsb", b"content", 100)
        
        result = service.validate_xlsb_file(file_info, 1000)
        
        self.assertTrue(result.is_valid)
        self.mock_logger.log_info.assert_called()
    
    def test_file_validation_service_invalid_extension(self):
        """ファイルバリデーションサービス（無効な拡張子）のテスト"""
        service = FileValidationService(self.mock_validator, self.mock_logger)
        file_info = FileInfo("test.txt", b"content", 100)
        
        result = service.validate_xlsb_file(file_info, 1000)
        
        self.assertFalse(result.is_valid)
        self.assertIn("xlsb拡張子", result.error_message)
        self.mock_logger.log_error.assert_called()
    
    def test_data_extraction_service(self):
        """データ抽出サービスのテスト"""
        extracted_data = ExtractedData(["data1", "data2"], "sheet1", "F")
        self.mock_reader.extract_data.return_value = extracted_data
        
        service = DataExtractionService(self.mock_reader, self.mock_logger)
        file_info = FileInfo("test.xlsb", b"content", 100)
        config = ExtractionConfig()
        
        result = service.extract_data(file_info, config)
        
        self.assertEqual(result.count, 2)
        self.mock_logger.log_info.assert_called()
    
    def test_data_write_service(self):
        """データ書き込みサービスのテスト"""
        self.mock_writer.write_data.return_value = b"output_content"
        
        service = DataWriteService(self.mock_writer, self.mock_logger)
        template_file = FileInfo("template.xlsx", b"template_content", 200)
        data = ExtractedData(["data1", "data2"], "sheet1", "F")
        config = WriteConfig()
        
        result = service.write_data(template_file, data, config)
        
        self.assertEqual(result, b"output_content")
        self.mock_logger.log_info.assert_called()


class TestApplicationUseCases(unittest.TestCase):
    """アプリケーションユースケースのテスト"""
    
    def setUp(self):
        self.mock_validation_service = Mock(spec=FileValidationService)
        self.mock_extraction_service = Mock(spec=DataExtractionService)
        self.mock_write_service = Mock(spec=DataWriteService)
        self.mock_logger = Mock(spec=StructuredLoggerRepository)
    
    def test_file_processing_use_case_success(self):
        """ファイル処理ユースケース（成功）のテスト"""
        # モックの設定
        self.mock_validation_service.validate_xlsb_file.return_value = ValidationResult.valid()
        self.mock_validation_service.validate_xlsx_file.return_value = ValidationResult.valid()
        
        extracted_data = ExtractedData(["data1", "data2"], "sheet1", "F")
        self.mock_extraction_service.extract_data.return_value = extracted_data
        
        self.mock_write_service.write_data.return_value = b"output_content"
        
        # ユースケースの実行
        use_case = FileProcessingUseCase(
            self.mock_validation_service,
            self.mock_extraction_service,
            self.mock_write_service,
            self.mock_logger
        )
        
        xlsb_file = FileInfo("test.xlsb", b"xlsb_content", 100)
        template_file = FileInfo("template.xlsx", b"template_content", 200)
        extraction_config = ExtractionConfig()
        write_config = WriteConfig()
        
        result = use_case.process_files(xlsb_file, template_file, extraction_config, write_config)
        
        # 結果の検証
        self.assertTrue(result.success)
        self.assertEqual(result.extracted_count, 2)
        self.assertEqual(result.output_content, b"output_content")
    
    def test_file_processing_use_case_validation_error(self):
        """ファイル処理ユースケース（バリデーションエラー）のテスト"""
        self.mock_validation_service.validate_xlsb_file.return_value = ValidationResult.invalid("Invalid file")
        
        use_case = FileProcessingUseCase(
            self.mock_validation_service,
            self.mock_extraction_service,
            self.mock_write_service,
            self.mock_logger
        )
        
        xlsb_file = FileInfo("test.txt", b"content", 100)
        template_file = FileInfo("template.xlsx", b"template_content", 200)
        extraction_config = ExtractionConfig()
        write_config = WriteConfig()
        
        result = use_case.process_files(xlsb_file, template_file, extraction_config, write_config)
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Invalid file")
    
    def test_configuration_use_case(self):
        """設定ユースケースのテスト"""
        extraction_config = ConfigurationUseCase.create_extraction_config(
            start_row=20, max_count=50
        )
        
        self.assertEqual(extraction_config.start_row, 20)
        self.assertEqual(extraction_config.max_count, 50)
        
        write_config = ConfigurationUseCase.create_write_config(
            target_row=15, start_column="B"
        )
        
        self.assertEqual(write_config.target_row, 15)
        self.assertEqual(write_config.start_column, "B")
    
    def test_health_check_use_case(self):
        """ヘルスチェックユースケースのテスト"""
        use_case = HealthCheckUseCase(self.mock_logger)
        
        result = use_case.check_health()
        
        self.assertEqual(result["status"], "healthy")
        self.assertIn("timestamp", result)
        self.mock_logger.log_info.assert_called()


class TestInfrastructureRepositories(unittest.TestCase):
    """インフラストラクチャリポジトリのテスト"""
    
    def test_basic_file_validator_repository(self):
        """基本ファイルバリデーションリポジトリのテスト"""
        validator = BasicFileValidatorRepository()
        
        # 有効なファイル
        valid_file = FileInfo("test.xlsb", b"x" * 200, 200)
        self.assertTrue(validator.validate_xlsb_file(valid_file))
        
        # 小さすぎるファイル
        small_file = FileInfo("test.xlsb", b"x" * 50, 50)
        self.assertFalse(validator.validate_xlsb_file(small_file))
        
        # ファイルサイズテスト
        self.assertTrue(validator.validate_file_size(valid_file, 1000))
        self.assertFalse(validator.validate_file_size(valid_file, 100))
    
    def test_structured_logger_repository(self):
        """構造化ログリポジトリのテスト"""
        logger = StructuredLoggerRepository()
        
        # ログメソッドが例外を発生させないことを確認
        try:
            logger.log_info("Test info", key="value")
            logger.log_error("Test error", error="error_message")
            logger.log_warning("Test warning", warning="warning_message")
        except Exception as e:
            self.fail(f"Logger raised an exception: {e}")


class TestWebAPI(unittest.TestCase):
    """Web APIのテスト"""
    
    def setUp(self):
        self.app = create_app()
        self.client = TestClient(self.app)
    
    def test_get_upload_form(self):
        """アップロードフォーム取得のテスト"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("ファイル変換Webアプリ", response.text)
    
    def test_health_check(self):
        """ヘルスチェックのテスト"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
    
    def test_get_config(self):
        """設定取得のテスト"""
        response = self.client.get("/config")
        self.assertEqual(response.status_code, 200)
        config = response.json()
        self.assertIn("extract_start_row", config)
        self.assertIn("max_extract_count", config)
    
    def test_process_files_invalid_extension(self):
        """無効な拡張子でのファイル処理テスト"""
        with tempfile.NamedTemporaryFile(suffix=".txt") as invalid_file:
            invalid_file.write(b"test content")
            invalid_file.seek(0)
            
            with tempfile.NamedTemporaryFile(suffix=".xlsx") as template_file:
                template_file.write(b"test content")
                template_file.seek(0)
                
                response = self.client.post(
                    "/process",
                    files={
                        "xlsb_file": ("test.txt", invalid_file.read(), "text/plain"),
                        "template_file": ("template.xlsx", template_file.read(), 
                                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    }
                )
                
                self.assertEqual(response.status_code, 400)
                self.assertIn("xlsb拡張子", response.json()["detail"])


def run_clean_tests():
    """クリーンアーキテクチャ版のテストを実行"""
    print("クリーンアーキテクチャ版ファイル変換Webアプリのテストを開始します...")
    
    # テストスイートを作成
    test_classes = [
        TestDomainEntities,
        TestDomainServices,
        TestApplicationUseCases,
        TestInfrastructureRepositories,
        TestWebAPI
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # テストを実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果を表示
    if result.wasSuccessful():
        print(f"\n✅ 全てのテストが成功しました！ ({result.testsRun}件)")
    else:
        print(f"\n❌ テストに失敗しました。失敗: {len(result.failures)}, エラー: {len(result.errors)}")
        
        for failure in result.failures:
            print(f"\n失敗: {failure[0]}")
            print(failure[1])
        
        for error in result.errors:
            print(f"\nエラー: {error[0]}")
            print(error[1])
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_clean_tests()
    exit(0 if success else 1)
"""ファイル処理コントローラー"""
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from ...domain.entities import FileInfo
from ...application.use_cases import (
    FileProcessingUseCase, ConfigurationUseCase
)
from ...infrastructure.config import AppConfig, OUTPUT_FILENAME


class FileProcessingController:
    """ファイル処理コントローラー"""
    
    def __init__(
        self,
        file_processing_use_case: FileProcessingUseCase,
        config_use_case: ConfigurationUseCase,
        config: AppConfig
    ):
        self._file_processing_use_case = file_processing_use_case
        self._config_use_case = config_use_case
        self._config = config
    
    async def process_files(
        self,
        xlsb_file: UploadFile,
        template_file: UploadFile
    ) -> FileResponse:
        """ファイル処理エンドポイント"""
        
        # UploadFileからFileInfoエンティティを作成
        xlsb_content = await xlsb_file.read()
        template_content = await template_file.read()
        
        xlsb_file_info = FileInfo(
            filename=xlsb_file.filename or "unknown.xlsb",
            content=xlsb_content,
            size=len(xlsb_content)
        )
        
        template_file_info = FileInfo(
            filename=template_file.filename or "unknown.xlsx",
            content=template_content,
            size=len(template_content)
        )
        
        # 設定を作成
        extraction_config = self._config_use_case.create_extraction_config(
            target_sheet=self._config.source_sheet_name
        )
        
        write_config = self._config_use_case.create_write_config(
            target_sheet=self._config.target_sheet_name
        )
        
        # ファイル処理を実行
        result = self._file_processing_use_case.process_files(
            xlsb_file_info,
            template_file_info,
            extraction_config,
            write_config
        )
        
        # 結果の処理
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)
        
        # 一時ファイルとして保存してFileResponseで返す
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            temp_file.write(result.output_content)
            temp_file.flush()
            
            return FileResponse(
                path=temp_file.name,
                filename=OUTPUT_FILENAME,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                background=self._cleanup_temp_file(temp_file.name)
            )
    
    def _cleanup_temp_file(self, file_path: str):
        """一時ファイルをクリーンアップするバックグラウンドタスク"""
        import os
        from fastapi import BackgroundTasks
        
        def cleanup():
            try:
                os.unlink(file_path)
            except:
                pass
        
        tasks = BackgroundTasks()
        tasks.add_task(cleanup)
        return tasks
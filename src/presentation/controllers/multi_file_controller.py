"""複数ファイル処理コントローラー"""
from fastapi import HTTPException, UploadFile, Form
from fastapi.responses import FileResponse
from typing import List
from datetime import datetime
from urllib.parse import quote
import logging

from ...domain.entities import FileInfo, MultiFileProcessRequest
from ...application.multi_file_use_cases import MultiFileProcessingUseCase
from ...infrastructure.template_repository import TemplateRepository

logger = logging.getLogger(__name__)


class MultiFileProcessingController:
    """複数ファイル処理コントローラー
    
    複数のxlsbファイルを1つのテンプレートに一括処理し、
    Excelファイルとしてダウンロード可能な形式で返すコントローラー
    """
    
    def __init__(
        self,
        multi_file_use_case: MultiFileProcessingUseCase,
        template_repository: TemplateRepository
    ):
        self._multi_file_use_case = multi_file_use_case
        self._template_repository = template_repository
    
    async def multi_file_process(
        self,
        xlsb_files: List[UploadFile],
        target_template: str = Form(...)
    ) -> FileResponse:
        """複数ファイル一括処理エンドポイント
        
        Args:
            xlsb_files: アップロードされた複数のxlsbファイル
            target_template: 出力先テンプレートID
            
        Returns:
            FileResponse: 処理済みExcelファイル
        """
        logger.info(f"複数ファイル処理開始 - ファイル数: {len(xlsb_files)}, テンプレート: {target_template}")
        
        # 入力バリデーション
        self._validate_multi_file_inputs(xlsb_files, target_template)
        
        # ファイル情報リストの作成
        xlsb_file_infos = await self._create_file_info_list(xlsb_files)
        
        # 処理リクエストの作成
        request = self._create_multi_file_request(xlsb_file_infos, target_template)
        
        # 複数ファイル処理の実行
        result = self._multi_file_use_case.process_multiple_files_to_single_template(request)
        
        # 結果の検証
        self._validate_multi_file_result(result)
        
        return self._create_file_response(result)
    
    def get_available_templates(self) -> dict:
        """複数ファイル処理用テンプレート一覧を取得
        
        Returns:
            dict: テンプレート情報のリスト
        """
        try:
            all_templates = self._template_repository.get_all_templates()
            
            # マッピング情報があるテンプレートのみフィルタ
            compatible_templates = [
                template for template in all_templates 
                if template.mapping is not None and template.is_active
            ]
            
            return {
                "templates": [
                    {
                        "id": template.id,
                        "name": template.name,
                        "description": template.description,
                        "output_filename": template.output_filename,
                        "max_rows": 1000  # 最大処理可能行数
                    }
                    for template in compatible_templates
                ]
            }
        except Exception as e:
            logger.error(f"複数ファイル用テンプレート一覧取得エラー: {str(e)}")
            raise HTTPException(status_code=500, detail=f"テンプレート情報の取得に失敗しました: {str(e)}")
    
    def _validate_multi_file_inputs(
        self,
        xlsb_files: List[UploadFile],
        target_template: str
    ) -> None:
        """複数ファイル処理の入力バリデーション"""
        
        # ファイル数チェック
        if not xlsb_files or len(xlsb_files) == 0:
            raise HTTPException(status_code=400, detail="xlsbファイルを選択してください")
        
        if len(xlsb_files) > 20:  # 最大20ファイル制限
            raise HTTPException(status_code=400, detail="一度に処理できるファイル数は最大20個です")
        
        # テンプレートIDの有効性チェック
        if not target_template.strip():
            raise HTTPException(status_code=400, detail="出力先テンプレートを選択してください")
        
        template = self._template_repository.get_template(target_template)
        if not template or not template.is_active:
            raise HTTPException(status_code=400, detail="指定されたテンプレートが見つかりません")
        
        if not template.mapping:
            raise HTTPException(status_code=400, detail="指定されたテンプレートは複数ファイル処理に対応していません")
        
        # ファイル拡張子チェック
        for xlsb_file in xlsb_files:
            if not xlsb_file.filename or not xlsb_file.filename.lower().endswith('.xlsb'):
                raise HTTPException(
                    status_code=400,
                    detail=f"ファイル '{xlsb_file.filename or 'unknown'}' はxlsb形式ではありません"
                )
    
    async def _create_file_info_list(self, xlsb_files: List[UploadFile]) -> List[FileInfo]:
        """UploadFileリストからFileInfoリストを作成"""
        file_infos = []
        
        for xlsb_file in xlsb_files:
            content = await xlsb_file.read()
            file_info = FileInfo(
                filename=xlsb_file.filename or "unknown.xlsb",
                content=content,
                size=len(content)
            )
            file_infos.append(file_info)
        
        return file_infos
    
    def _create_multi_file_request(
        self,
        xlsb_file_infos: List[FileInfo],
        target_template: str
    ) -> MultiFileProcessRequest:
        """複数ファイル処理リクエストを作成"""
        return MultiFileProcessRequest(
            xlsb_files=xlsb_file_infos,
            target_template_id=target_template,
            process_date=datetime.now()
        )
    
    def _validate_multi_file_result(self, result) -> None:
        """複数ファイル処理結果の検証"""
        if not hasattr(result, 'success') or not result.success:
            error_msg = getattr(result, 'error_message', '不明なエラーが発生しました')
            logger.error(f"複数ファイル処理エラー: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
    
    def _create_file_response(self, result) -> FileResponse:
        """ファイルレスポンスを作成"""
        # 日本語ファイル名をURLエンコード
        encoded_filename = quote(result.output_filename)
        
        # Content-Dispositionヘッダーを設定
        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
        
        return FileResponse(
            path=result.output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=result.output_filename,
            headers=headers
        )
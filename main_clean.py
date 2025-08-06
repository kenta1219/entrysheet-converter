from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn
import logging
from pathlib import Path
import os

from src.infrastructure.container import container
from src.infrastructure.config import OUTPUT_FILENAME

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """FastAPIアプリケーションを作成"""
    
    # 設定を取得してロギングを設定
    config = container.get_config()
    config.setup_logging()
    
    # FastAPIアプリケーションを初期化
    app = FastAPI(
        title="エントリーシート変換アプリ (Clean Architecture)",
        description="xlsbファイル処理用Webアプリケーション - 従来機能 + 一括集約機能",
        version="3.0.0"
    )
    
    # CORS設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 静的ファイル配信を設定
    static_path = Path(__file__).parent / "src" / "web" / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # コントローラーを取得
    health_controller = container.get_health_controller()
    web_controller = container.get_web_controller()
    batch_processing_controller = container.get_batch_processing_controller()
    
    # 機能フラグに基づいて複数ファイル処理コントローラーを取得
    multi_file_controller = None
    if config.feature_flags.enable_multi_file_processing:
        multi_file_controller = container.get_multi_file_processing_controller()
    
    @app.get("/", response_class=HTMLResponse)
    async def get_upload_form():
        """アップロードフォームを返す"""
        try:
            return web_controller.get_upload_form()
        except Exception as e:
            logger.error(f"フォーム表示エラー: {str(e)}")
            raise HTTPException(status_code=500, detail="フォームの表示に失敗しました")
    
    @app.post("/batch-process")
    async def batch_process(
        xlsb_file: UploadFile = File(...),
        facility_name: str = Form(...),
        selected_templates: List[str] = Form(default=[])
    ):
        """一括処理エンドポイント"""
        try:
            logger.info(f"一括処理開始 - ファイル: {xlsb_file.filename}, 施設名: {facility_name}")

            # コントローラーがFileResponseを直接返すので、そのまま返す
            return await batch_processing_controller.batch_process(
                xlsb_file, facility_name, selected_templates
            )

        except Exception as e:
            logger.error(f"一括処理エラー: {str(e)}")
            raise
    
    @app.get("/templates")
    async def get_templates():
        """利用可能なテンプレート一覧を取得"""
        try:
            return batch_processing_controller.get_available_templates()
        except Exception as e:
            logger.error(f"テンプレート一覧取得エラー: {str(e)}")
            raise
    
    @app.get("/health")
    async def health_check():
        """ヘルスチェックエンドポイント"""
        try:
            return health_controller.check_health()
        except Exception as e:
            logger.error(f"ヘルスチェックエラー: {str(e)}")
            raise HTTPException(status_code=500, detail="ヘルスチェックに失敗しました")
    
    # 複数ファイル処理エンドポイント（機能フラグで制御）
    if config.feature_flags.enable_multi_file_processing and multi_file_controller:
        @app.post("/multi-file-process")
        async def multi_file_process(
            xlsb_files: List[UploadFile] = File(...),
            target_template: str = Form(...),
            facility_names: List[str] = Form(...),
            start_row: int = Form(14)
        ):
            """複数ファイル一括処理エンドポイント"""
            try:
                logger.info(f"複数ファイル処理開始 - ファイル数: {len(xlsb_files)}, テンプレート: {target_template}")
                
                return await multi_file_controller.multi_file_process(
                    xlsb_files, target_template, facility_names, start_row
                )
                
            except Exception as e:
                logger.error(f"複数ファイル処理エラー: {str(e)}")
                raise
        
        @app.get("/multi-file-templates")
        async def get_multi_file_templates():
            """複数ファイル処理用テンプレート一覧を取得"""
            try:
                return multi_file_controller.get_available_templates()
            except Exception as e:
                logger.error(f"複数ファイル用テンプレート一覧取得エラー: {str(e)}")
                raise
    
    @app.get("/features")
    async def get_available_features():
        """利用可能な機能一覧を取得"""
        return {
            "batch_processing": {
                "enabled": config.feature_flags.enable_batch_processing,
                "description": "1つのxlsbファイルを複数テンプレートに処理",
                "endpoint": "/batch-process"
            },
            "multi_file_processing": {
                "enabled": config.feature_flags.enable_multi_file_processing,
                "description": "複数のxlsbファイルを1つのテンプレートに集約",
                "endpoint": "/multi-file-process",
                "max_files": config.feature_flags.max_multi_files
            }
        }
    
    @app.get("/config")
    async def get_config():
        """現在の設定を返す（デバッグ用）"""
        return {
            "max_file_size": config.max_file_size,
            "source_sheet_name": config.source_sheet_name,
            "target_sheet_name": config.target_sheet_name,
            "output_filename": OUTPUT_FILENAME,
            "feature_flags": {
                "enable_multi_file_processing": config.feature_flags.enable_multi_file_processing,
                "enable_batch_processing": config.feature_flags.enable_batch_processing,
                "max_multi_files": config.feature_flags.max_multi_files,
                "max_batch_templates": config.feature_flags.max_batch_templates
            }
        }
    
    return app


# アプリケーションインスタンスを作成
app = create_app()


if __name__ == "__main__":
    config = container.get_config()
    uvicorn.run(
        "main_clean:app",
        host=config.host,
        port=config.port,
        reload=True
    )
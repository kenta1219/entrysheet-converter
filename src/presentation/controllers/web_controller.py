"""Webフォームコントローラー - Web UI専用"""
from fastapi.responses import HTMLResponse
from ...web.views.template_renderer import TemplateRenderer


class WebController:
    """Web UI コントローラー"""
    
    def __init__(self):
        self._template_renderer = TemplateRenderer()
    
    def get_upload_form(self) -> HTMLResponse:
        """アップロードフォームHTMLを返す"""
        html_content = self._template_renderer.render_upload_form()
        return HTMLResponse(content=html_content)
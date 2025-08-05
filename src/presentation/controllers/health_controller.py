"""ヘルスチェックコントローラー"""
from ...application.use_cases import HealthCheckUseCase


class HealthController:
    """ヘルスチェックコントローラー"""
    
    def __init__(self, health_use_case: HealthCheckUseCase):
        self._health_use_case = health_use_case
    
    def check_health(self) -> dict:
        """ヘルスチェックエンドポイント"""
        return self._health_use_case.check_health()
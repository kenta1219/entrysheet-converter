"""ヘルスチェックコントローラー"""


class HealthController:
    """ヘルスチェックコントローラー"""
    
    def __init__(self, health_use_case):
        self._health_use_case = health_use_case
    
    def check_health(self) -> dict:
        """ヘルスチェックエンドポイント"""
        return self._health_use_case.check_health()
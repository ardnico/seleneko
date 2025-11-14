from .driver_factory import DriverSettings
from .client_base import SeleniumClient as _BaseClient
from .smart_actions import SmartActionsMixin

class SeleniumClient(SmartActionsMixin, _BaseClient):
    """Driver + BaseOps + SmartActions を統合した最終クライアント"""
    pass

__all__ = ["SeleniumClient", "DriverSettings"]

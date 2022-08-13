from abc import ABC, abstractmethod

from telegram.ext import Application

from ..config import Config
from ..helpers import AppHelper
from ..services import AppService


class BaseHandler(ABC):
    def __init__(
        self,
        app: Application,
        service: AppService,
        helper: AppHelper,
        config: Config,
    ) -> None:
        self.service = service
        self.helper = helper
        self.config = config
        self._init_handler(app)

    @abstractmethod
    def _init_handler(self, app: Application) -> None:
        pass

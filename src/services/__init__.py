from ..config import APP_CONFIG, Config
from .belong import BelongService
from .chat import ChatService
from .interview_pair import InterviewPairService
from .question_record import QuestionRecordService
from .user import UserService


class AppService:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.user_service = UserService(config)
        self.chat_service = ChatService(config)
        self.belong_service = BelongService(config)
        self.question_record_service = QuestionRecordService(config)
        self.pair_service = InterviewPairService(config)


APP_SERVICE = AppService(APP_CONFIG)

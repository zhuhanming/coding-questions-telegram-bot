from .belong import BelongService
from .chat import ChatService
from .interview_pair import InterviewPairService
from .question_record import QuestionRecordService
from .user import UserService


# TODO: Look into dependency injection for this class
class AppService:
    def __init__(self) -> None:
        self.user = UserService()
        self.chat = ChatService()
        self.belong = BelongService()
        self.question_record = QuestionRecordService()
        self.pair = InterviewPairService()

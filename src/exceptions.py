class BotException(Exception):
    message = "Something went wrong!"


class ResourceNotFoundException(BotException):
    message = "I couldn't find the required information!"


class InvalidRequestException(BotException):
    def __init__(
        self,
        message="Uh oh! It seems like something's wrong with the information you've told me!",
    ):
        self.message = message

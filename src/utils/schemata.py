from functools import wraps

from cerberus import Validator  # type: ignore

from .exceptions import InvalidRequestException


def validate_input(schema, **validator_kwargs):
    def decorator(func):
        @wraps(func)
        def decorated_func(*args, **kwargs):
            validator = Validator(schema, require_all=True, **validator_kwargs)
            res = validator.validate(kwargs)
            if not res:
                raise InvalidRequestException(validator.errors)
            return func(*args, **kwargs)

        return decorated_func

    return decorator

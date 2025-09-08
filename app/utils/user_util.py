from app.constants.status import Status
from app.db.models import Users
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode


@staticmethod
def is_valid_user(user: Users) -> bool:
    """Check if the user is valid based on their status and role."""
    try:
        if not user:
            raise CustomException(ErrorCode.AUTH_EMAIL_NOT_FOUND)

        if user.status != Status.ACTIVE:
            raise CustomException(ErrorCode.AUTH_INVALID_ACCOUNT_STATUS)

        return True
    except CustomException as e:
        raise
    except Exception as e:
        raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

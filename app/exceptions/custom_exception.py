from app.exceptions.error_codes import ErrorCode

class CustomException(Exception):
    def __init__(self, error: ErrorCode):
        self.code = error.code
        self.message = error.message
        self.http_code = error.http_code

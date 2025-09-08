from enum import Enum


class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class SemesterStatus(str, Enum):
    HIDDEN = "hidden"
    VISIBLE = "visible"

class UploadSessionStatus(str, Enum):
    HIDDEN = "hidden"
    VISIBLE = "visible"


class UploadSessionTaskStatus(str, Enum):
    COMPLETED = "completed"
    NOT_START = "not_start"
    FAILED = "failed"


class FileUploadType(str, Enum):
    ANSWER_TEMPLATE = "answer"
    GUIDE_TEMPLATE = "guide"
    EXAM = "exam"

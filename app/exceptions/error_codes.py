import enum
from http import HTTPStatus


class ErrorCode(enum.Enum):
    # ======================================================================================================================
    # Common Error Messages
    # ======================================================================================================================
    COM_SUCCESS = ("0", "Operation completed successfully", HTTPStatus.OK)
    COM_UPDATE_FAILED = ("001", "Failed to update.", HTTPStatus.INTERNAL_SERVER_ERROR)
    COM_INTERNAL_SERVER_ERROR = ("002", "An unexpected internal server error occurred",
                                 HTTPStatus.INTERNAL_SERVER_ERROR)
    COM_AI_GENERATE_FAILED = ("003",
                              "I don't have sufficient information in the provided contexts to generate the exam question.",
                              HTTPStatus.BAD_REQUEST)
    COM_GUIDE_CONTENT_MISMATCH = ("004",
                                  "Mismatch between number of guide contents and criteria map.",
                                  HTTPStatus.BAD_REQUEST)

    # ======================================================================================================================
    # Account Management Messages
    # ======================================================================================================================
    ACC_USER_ALREADY_EXISTS = ("100", "A user with this email already exists", HTTPStatus.BAD_REQUEST)
    ACC_USER_NOT_FOUND = ("101", "This user does not exist in the system", HTTPStatus.NOT_FOUND)
    ACC_ROLE_NOT_FOUND = ("102", "This role does not exist in the system", HTTPStatus.NOT_FOUND)
    ACC_USER_NOT_AUTHORIZED = ("103", "The user doesn't have enough privileges", HTTPStatus.UNAUTHORIZED)
    ACC_INVALID_TOKEN = ("104", "The provided token is invalid or expired", HTTPStatus.UNAUTHORIZED)
    ACC_SINGLE_ACTIVE_LEADER_VIOLATION = ("105", "Only one course leader in the system", HTTPStatus.CONFLICT)
    ACC_MULTIPLE_ACTIVE_LEADERS = ("106", "Multiple active course leaders detected", HTTPStatus.BAD_REQUEST)
    ACC_ACTIVE_CANT_DELETE = ("107", "Some account still active can delete", HTTPStatus.BAD_REQUEST)
    ACC_ROLE_INVALID = ("108", "Role not exits", HTTPStatus.INTERNAL_SERVER_ERROR)
    ACC_STATUS_INVALID = ("109", "Account status invalid", HTTPStatus.BAD_REQUEST)

    # ======================================================================================================================
    # Authentication Management Messages
    # ======================================================================================================================
    AUTH_INVALID_ACCOUNT_STATUS = ("201", "The account status is inactive", HTTPStatus.FORBIDDEN)
    AUTH_INVALID_LOGIN_CREDENTIALS = ("202", "Password is incorrect. Please try again.", HTTPStatus.UNAUTHORIZED)
    AUTH_OTP_INVALID = ("203", "OTP code is incorrect. Please check again.", HTTPStatus.BAD_REQUEST)
    AUTH_OTP_EXPIRED = ("204", "OTP code has expired. Please request a new code.", HTTPStatus.BAD_REQUEST)
    AUTH_OTP_STORAGE_FAILED = ("205", "System error while saving OTP code.", HTTPStatus.INTERNAL_SERVER_ERROR)
    AUTH_EMAIL_SEND_FAILED = ("206", "email failed to send. Please try again later.",
                              HTTPStatus.INTERNAL_SERVER_ERROR)
    AUTH_EMAIL_NOT_FOUND = ("207", "This email does not exist in the system", HTTPStatus.NOT_FOUND)
    AUTH_PASSWORD_OLD_INCORRECT = ("208", "Old password is incorrect.", HTTPStatus.BAD_REQUEST)
    AUTH_PASSWORD_POLICY_VIOLATED = ("209", "Password does not meet the required security policy.",
                                     HTTPStatus.BAD_REQUEST)
    AUTH_EMAIL_ALREADY_EXISTS = ("210", "This email already exists in the system", HTTPStatus.NOT_FOUND)
    AUTH_PASSWORD_SAME = ("211", "The new password must be different from the old password.", HTTPStatus.NOT_FOUND)
    AUTH_EMAIL_CHANGE = ("212", "Can't update the email.", HTTPStatus.NOT_FOUND)

    # ======================================================================================================================
    # Exam Management Messages
    # ======================================================================================================================
    EXAM_TEMPLATE_NOT_FOUND = ("300", "The requested answer template was not found", HTTPStatus.NOT_FOUND)
    EXAM_INVALID_FILE_FORMAT = ("301", "The uploaded file format is not supported", HTTPStatus.BAD_REQUEST)
    EXAM_UPLOAD_SESSION_NOT_FOUND = ("302", "The upload session could not be located", HTTPStatus.NOT_FOUND)
    EXAM_EXAM_GENERATION_FAILED = ("303", "Failed to generate the automated exam", HTTPStatus.INTERNAL_SERVER_ERROR)
    EXAM_DELETE_FILE_UPLOAD = ("304", "Failed to delete the uploaded file", HTTPStatus.INTERNAL_SERVER_ERROR)
    EXAM_UPLOAD_FILE_FAILURE = ("305", "Failed to upload the specified file", HTTPStatus.INTERNAL_SERVER_ERROR)
    EXAM_QUESTION_NOT_FOUND = ("306", "The requested exam question was not found", HTTPStatus.NOT_FOUND)
    EXAM_QUESTION_CANT_DELETE = ("306", "The exam question can't be deleted", HTTPStatus.BAD_REQUEST)
    EXAM_DOCUMENT_NOT_EXISTED = ("307", "The exam question material does not exist", HTTPStatus.NOT_FOUND)
    EXAM_QUESTION_NAME_EXITED = ("308", "The exam question name already exists", HTTPStatus.BAD_REQUEST)
    EXAM_NOT_FOUND = ("309", "The requested exam does not exist in the system", HTTPStatus.NOT_FOUND)
    EXAM_DELETE_MATERIAL_FAILED = ("310", "Failed to delete the exam question material",
                                   HTTPStatus.INTERNAL_SERVER_ERROR)
    EXAM_MATERIAL_FILE_NOT_EXISTED = ("311", "The exam question material file does not exist", HTTPStatus.NOT_FOUND)
    EXAM_CONTEXT_NOT_CREATED = ("312", "The exam context need to generate first before generate question",
                                HTTPStatus.NOT_FOUND)
    EXAM_NAME_EXIST = ("320", "The exam name already exists", HTTPStatus.BAD_REQUEST)

    # ======================================================================================================================
    # Grading Management Messages
    # ======================================================================================================================

    # ======================================================================================================================
    # Grading Guide Management Messages
    # ======================================================================================================================
    GUIDE_GRADING_GUIDE_NOT_FOUND = ("500", "The requested grading guide was not found", HTTPStatus.NOT_FOUND)
    GUIDE_AUTOMATED_GRADING_FAILED = ("501", "The automated grading process failed", HTTPStatus.INTERNAL_SERVER_ERROR)
    GUIDE_EXPERT_GRADING_INVALID = ("502", "The expert grading d-original-submission provided is invalid", HTTPStatus.BAD_REQUEST)
    NUMBER_QUESTION_NOT_MATCH = ("503",
                                 "The number of questions in the grading guide does not match the number of questions in the answer template",
                                 HTTPStatus.BAD_REQUEST)
    GUIDE_QUESTION_NOT_FOUND = ("504", "The grading guide question not found", HTTPStatus.NOT_FOUND)
    GUIDE_NAME_EXIST = ("505", "The grading guide name already exists", HTTPStatus.BAD_REQUEST)

    # ======================================================================================================================
    # Plagiarism Management Messages
    # ======================================================================================================================

    # ======================================================================================================================
    # Submission Management Messages
    # ======================================================================================================================
    SUBM_SUBMISSION_NOT_FOUND = ("700", "The requested submission was not found", HTTPStatus.NOT_FOUND)
    SUBM_PLAGIARISM_CHECK_FAILED = ("701", "The plagiarism check process failed", HTTPStatus.INTERNAL_SERVER_ERROR)
    SUBM_SCORE_CONFIRMATION_FAILED = ("702", "Failed to confirm the assigned score", HTTPStatus.INTERNAL_SERVER_ERROR)
    SUBM_FIX_SCORE_FAILED = ("703", "Failed to fix the assigned score", HTTPStatus.INTERNAL_SERVER_ERROR)
    SUBM_QUESTION_NOT_FOUND = ("704", "No submission question not found", HTTPStatus.NOT_FOUND)
    SUBM_SCORE_HISTORY_NOT_FOUND = ("705", "No score history found", HTTPStatus.NOT_FOUND)
    # ======================================================================================================================
    # Similarity Management Messages
    # ======================================================================================================================

    # ======================================================================================================================
    # File Messages
    # ======================================================================================================================
    FILE_INVALID_FORMAT = ("801", "Invalid .docx file format", HTTPStatus.BAD_REQUEST)
    FILE_NOT_DOCX = ("802", "Please upload a .docx file", HTTPStatus.BAD_REQUEST)
    FILE_SIZE_EXCEEDED = ("803", "File size exceeds 5MB limit", HTTPStatus.BAD_REQUEST)
    FILE_EMPTY = ("804", "File is empty", HTTPStatus.BAD_REQUEST)
    FILE_CONTAINS_IMAGES = ("805", "File must not contain images", HTTPStatus.BAD_REQUEST)
    FILE_CONTAINS_SHAPES = ("806", "File must not contain shapes", HTTPStatus.BAD_REQUEST)
    FILE_INVALID_CHARACTERS = ("807", "File contains invalid characters", HTTPStatus.BAD_REQUEST)
    FILE_CONVERSION_FAILED = ("808", "Failed to convert file to markdown", HTTPStatus.BAD_REQUEST)

    # ======================================================================================================================
    # Semester Management Messages
    # ======================================================================================================================
    SEM_SEMESTER_NOT_FOUND = ("900", "The requested semester was not found", HTTPStatus.NOT_FOUND)
    SEM_SEMESTER_NAME_EXIST = ("901", "The semester name must be unique", HTTPStatus.NOT_FOUND)
    SEM_STATUS_INVALID = ("902", "The semester status invalid", HTTPStatus.BAD_REQUEST)

    # ======================================================================================================================
    # Paging Messages
    # ======================================================================================================================
    # ======================================================================================================================
    # Auth Messages
    # ======================================================================================================================
    PERMISSION_ACCESS_DATA = ("1000", "You can not access this resource", HTTPStatus.FORBIDDEN)
    AUTH_WITH_GOOGLE_INVALID = ("1001", "Unable to sign in with Google. Please try again.", HTTPStatus.BAD_REQUEST)
    # ======================================================================================================================
    # Upload session Management Messages
    # ======================================================================================================================
    SESSION_UPLOAD_NOT_FOUND = ("1001", "The upload session was not found", HTTPStatus.NOT_FOUND)
    SESSION_UPLOAD_NAME_HAS_EXITS = ("1002", "The upload session name must be unique", HTTPStatus.NOT_FOUND)
    SESSION_UPLOAD_STATUS_INVALID = ("1003", "The upload session status invalid", HTTPStatus.BAD_REQUEST)
    SESSION_UPLOAD_TASK_STATUS_INVALID = ("1004", "The upload session task status invalid", HTTPStatus.BAD_REQUEST)
    # ======================================================================================================================
    # System error Messages
    # ======================================================================================================================
    INTERNAL_SERVER_ERROR = ("2000", "The server has an error.", HTTPStatus.INTERNAL_SERVER_ERROR)

    # ======================================================================================================================
    # AI-related error codes
    # ======================================================================================================================
    AI_PROVIDER_NOT_FOUND = ("AI_001", "AI provider not found", HTTPStatus.NOT_FOUND)
    AI_API_KEY_MISSING = ("AI_002", "API key missing for provider", HTTPStatus.BAD_REQUEST)
    AI_REQUEST_FAILED = ("AI_003", "Request to AI provider failed", HTTPStatus.INTERNAL_SERVER_ERROR)
    AI_RATE_LIMIT_EXCEEDED = ("AI_004", "Rate limit exceeded", HTTPStatus.TOO_MANY_REQUESTS)
    AI_MODEL_NOT_FOUND = ("AI_005", "Model not found", HTTPStatus.NOT_FOUND)
    AI_INVALID_REQUEST = ("AI_006", "Invalid request format", HTTPStatus.BAD_REQUEST)

    def __init__(self, code, message, http_status):
        self.code = code  # mã lỗi nghiệp vụ của hệ thống (cụ thể)
        self.message = message
        self.http_code = http_status.value  # mã lỗi của request

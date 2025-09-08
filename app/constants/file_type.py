from enum import Enum


class FileType(str, Enum):
    Word = ".docx"
    Excel = ".xlsx"

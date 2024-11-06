import enum

CUSTOM_SEP = "---###---"


class ContentType(str, enum.Enum):
    TEXT = "text"
    TABLE = "table"

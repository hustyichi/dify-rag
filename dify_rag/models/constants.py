import enum

CUSTOM_SEP = "---###---"
CHOICES_RETURN_FULL_TEXT_MARKER = "<!-- CHOICES_RETURN_FULL_TEXT -->"

class ContentType(str, enum.Enum):
    TEXT = "text"
    TABLE = "table"

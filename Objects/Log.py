from datetime import datetime
from enum import Enum


class LogStatus(Enum):
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4

    def __repr__(self):
        return str(self.name)

    def toEmoji(self):
        if self.DEBUG: return "🪳"
        if self.INFO: return "ℹ️"
        if self.WARN: return "⚠️"
        if self.ERROR: return "❌"
        return None


class Log:
    def __init__(self, task=None, status=LogStatus.DEBUG, message=""):
        self.task = task
        self.status = status
        self.message = message
        self.start = datetime.now()
        self.end = None

    def toJSON(self):
        return {
            "task": self.task,
            "status": self.status.name,
            "message": self.message,
            "start": self.start.timestamp() if self.start else None,
            "end": self.end.timestamp() if self.end else None
        }
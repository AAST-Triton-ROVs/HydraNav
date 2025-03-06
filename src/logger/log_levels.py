from enum import Enum


class LogLevels(Enum):
    """
    This enum defines common log levels for consistent logging throughout the application.
    
    * TRACE
        Provides highly detailed logs, used for debugging or tracing the code flow.
    * DEBUG
        Used for diagnostic information that can help pinpoint issues.
    * INFO
        General information about the application's operation or state changes.
    * SUCCESS
        Indicates successful completion of an operation.
    * WARNING
        Highlights potential issues or situations that might require attention.
    * ERROR
        Signifies an error or unexpected behavior in the application.
    * CRITICAL
        Denotes a serious problem that requires immediate attention or action.
    """

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

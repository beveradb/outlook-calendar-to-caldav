import logging
import os


def setup_logging(log_level: str = "INFO", log_file: str = "calendar_sync.log"):
    """
    Configure logging for the application.
    Args:
        log_level: Logging level as a string (e.g., 'INFO', 'DEBUG')
        log_file: Name of the log file (in logs/ directory)
    Returns:
        Configured logger instance
    Raises:
        ValueError if log_level is invalid
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    filepath = os.path.join(log_directory, log_file)

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(filepath),
            logging.StreamHandler()
        ]
    )
    # Disable requests library logging to avoid verbosity
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logging.getLogger(__name__)

# Initialize a default logger for modules that might import it directly
logger = setup_logging()

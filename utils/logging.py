import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Configures application-wide logging output.
    Logs trace, debug, info to stdout, and records warning/errors
    to rotating log files in the 'logs/' folder.
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure main logger
    logger = logging.getLogger("visioninspect")
    logger.setLevel(logging.DEBUG)
    
    # Check if handlers already exist to prevent duplicate logging
    if logger.handlers:
        return logger
        
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] - %(message)s'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Info File Handler (Rotating)
    info_file_path = os.path.join(log_dir, "app.log")
    info_handler = RotatingFileHandler(
        info_file_path, 
        maxBytes=5*1024*1024, # 5MB
        backupCount=3
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    logger.addHandler(info_handler)
    
    # Error File Handler (Rotating)
    error_file_path = os.path.join(log_dir, "error.log")
    error_handler = RotatingFileHandler(
        error_file_path,
        maxBytes=5*1024*1024, # 5MB
        backupCount=5
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # Disable propagation to root logger to avoid double logging
    logger.propagate = False
    
    logger.info("Logging infrastructure initialized successfully.")
    return logger

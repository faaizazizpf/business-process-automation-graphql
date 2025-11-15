import logging
import sys
import os

def setup_python_logging(log_name: str):
    """
    Set up a logger that writes to both terminal and file.
    If log file already exists, delete it.
    """
    log_file = "buxfer_automation.log"

    # Delete the log file if it exists
    if os.path.exists(log_file):
        os.remove(log_file)

    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:  # prevent duplicate handlers
        formatter = logging.Formatter('%(asctime)s :%(filename)s :%(lineno)d :%(levelname)s:-----%(message)s')

        # Console handler
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Initialize logger
logger = setup_python_logging(__name__)

def stopper(point="",debug_value=""):
    logger.info("\n\n\n")
    logger.info("========[stopper in session]======== "*3)
    logger.info(f"Reach point {str(point)}\n")
    logger.info(f"{str(debug_value)}")
    input_=input("Do you want to continue? ")
    logger.info("========[stopper ended]======== "*3)
    logger.info("\n\n\n") 



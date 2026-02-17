"""Logging configuration for ONVIF-RTSP Bridge."""

import logging
import os
import sys
from datetime import datetime


def setup_logging(log_level: str = None):
    """Configure application logging."""
    
    # Determine log level
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # File handler (if logs directory exists)
    file_handler = None
    log_dir = '/app/logs'
    if os.path.exists(log_dir):
        log_file = os.path.join(log_dir, f'onvif-bridge-{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    if file_handler:
        root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    logging.info(f"Logging configured at level: {log_level}")

#!/usr/bin/env python3
"""
Test script to verify that the logging configuration works correctly.
This script simulates the application startup and logging initialization.
"""

import os
import logging
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the logging setup function
from app.core.logging import setup_logging
from app.core.config import settings


def test_logging_setup() -> None:
    """Test the logging setup with different configurations."""
    print("\n=== Testing Logging Setup ===")

    # Test with default settings
    print("\n1. Testing with default settings:")
    setup_logging()
    logger = logging.getLogger()
    logger.info("This is a test log message with default settings")

    # Test with non-existent directory
    print("\n2. Testing with non-existent directory:")
    original_path = settings.log_file_path
    settings.log_file_path = "nonexistent_dir/test.log"
    setup_logging()
    logger.info("This is a test log message with non-existent directory")

    # Test with permission issues (simulate by using /root directory)
    print("\n3. Testing with permission issues (simulated):")
    settings.log_file_path = "/root/test.log"  # This should fail due to permissions
    setup_logging()
    logger.info("This is a test log message with permission issues")

    # Test with disabled file logging
    print("\n4. Testing with disabled file logging:")
    settings.enable_file_logging = False
    setup_logging()
    logger.info("This is a test log message with disabled file logging")

    # Restore original settings
    settings.log_file_path = original_path
    settings.enable_file_logging = True

    print("\n=== Logging Test Complete ===")


if __name__ == "__main__":
    test_logging_setup()

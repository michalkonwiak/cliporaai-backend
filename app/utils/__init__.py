"""
Utility functions for the CliporaAI backend.
"""

try:
    from app.utils.file_validation import (
        validate_file,
        validate_audio_file,
        validate_video_file,
        validate_file_path,
    )
    
    __all__ = [
        "validate_file",
        "validate_audio_file",
        "validate_video_file",
        "validate_file_path",
    ]
except ImportError:
    # Handle the case where python-magic is not installed
    import logging
    logging.getLogger(__name__).warning(
        "File validation utilities could not be imported. "
        "Make sure python-magic is installed."
    )
    __all__ = []
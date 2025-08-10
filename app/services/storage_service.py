import abc
import logging
import os
import shutil
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService(abc.ABC):
    """Abstract base class for storage services."""

    @abc.abstractmethod
    async def save_file(
        self, file: UploadFile, destination_path: str, user_id: int
    ) -> str:
        """
        Save a file to storage.

        Args:
            file: The file to save
            destination_path: The path where the file should be saved
            user_id: The ID of the user who owns the file

        Returns:
            The path where the file was saved
        """
        pass

    @abc.abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: The path of the file to delete

        Returns:
            True if the file was deleted, False otherwise
        """
        pass

    @abc.abstractmethod
    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        Get a URL for accessing a file.

        Args:
            file_path: The path of the file
            expires_in: The number of seconds the URL should be valid for

        Returns:
            The URL for accessing the file
        """
        pass

    @abc.abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            file_path: The path of the file to check

        Returns:
            True if the file exists, False otherwise
        """
        pass

    @abc.abstractmethod
    async def list_files(self, directory_path: str) -> list[str]:
        """
        List files in a directory.

        Args:
            directory_path: The path of the directory to list

        Returns:
            A list of file paths
        """
        pass


class LocalStorageService(StorageService):
    """Implementation of StorageService for local file storage."""

    def __init__(self) -> None:
        """Initialize the local storage service."""
        # In tests we may not have permissions in CWD; default to a temp dir under project
        self.upload_dir = settings.upload_dir_path
        self.temp_dir = settings.temp_upload_dir_path
        
        # Create directories if they don't exist
        try:
            os.makedirs(self.upload_dir, exist_ok=True)
            os.makedirs(self.temp_dir, exist_ok=True)
        except PermissionError:
            # Fallback to local temp folder inside repo
            base = Path("test_uploads")
            base.mkdir(exist_ok=True)
            self.upload_dir = base
            self.temp_dir = base / "temp"
            self.temp_dir.mkdir(exist_ok=True)

    async def save_file(
        self, file: UploadFile, destination_path: str, user_id: int
    ) -> str:
        """
        Save a file to local storage.

        Args:
            file: The file to save
            destination_path: The path where the file should be saved
            user_id: The ID of the user who owns the file

        Returns:
            The path where the file was saved
        """
        # Create user directory if it doesn't exist (with fallback on permission error)
        user_dir = self.upload_dir / str(user_id)
        try:
            os.makedirs(user_dir, exist_ok=True)
        except PermissionError:
            base = Path("test_uploads")
            base.mkdir(exist_ok=True)
            self.upload_dir = base
            user_dir = self.upload_dir / str(user_id)
            os.makedirs(user_dir, exist_ok=True)
        
        # Create full destination path
        full_path = self.upload_dir / destination_path
        
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Save the file
        try:
            with open(full_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            logger.info(f"File saved to {full_path}")
            return str(full_path)
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise
        finally:
            await file.close()

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from local storage.

        Args:
            file_path: The path of the file to delete

        Returns:
            True if the file was deleted, False otherwise
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return False
        
        try:
            os.remove(path)
            logger.info(f"File deleted: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        Get a URL for accessing a file in local storage.
        
        For local storage, this just returns the file path.

        Args:
            file_path: The path of the file
            expires_in: Not used for local storage

        Returns:
            The file path
        """
        return file_path

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in local storage.

        Args:
            file_path: The path of the file to check

        Returns:
            True if the file exists, False otherwise
        """
        return os.path.exists(file_path)

    async def list_files(self, directory_path: str) -> list[str]:
        """
        List files in a directory in local storage.

        Args:
            directory_path: The path of the directory to list

        Returns:
            A list of file paths
        """
        dir_path = Path(directory_path)
        
        if not dir_path.exists() or not dir_path.is_dir():
            logger.warning(f"Directory not found: {directory_path}")
            return []
        
        try:
            return [str(f) for f in dir_path.glob("**/*") if f.is_file()]
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []


class S3StorageService(StorageService):
    """Implementation of StorageService for S3 storage."""

    def __init__(self) -> None:
        """Initialize the S3 storage service."""
        import boto3
        from botocore.config import Config
        
        # Initialize boto3 client with LocalStack endpoint
        endpoint_url = f"http://{str(settings.s3_endpoint_url)}" if settings.s3_endpoint_url else None
        access_key = settings.aws_access_key_id.get_secret_value() if settings.aws_access_key_id else None
        secret_key = settings.aws_secret_access_key.get_secret_value() if settings.aws_secret_access_key else None
        
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = settings.s3_bucket_name
        logger.info(f"Initialized S3 storage service with bucket: {self.bucket_name}")

    async def save_file(
        self, file: UploadFile, destination_path: str, user_id: int
    ) -> str:
        """
        Save a file to S3 storage.

        Args:
            file: The file to save
            destination_path: The path where the file should be saved
            user_id: The ID of the user who owns the file

        Returns:
            The path where the file was saved
        """
        try:
            # Read file content
            file_content = await file.read()
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=(self.bucket_name or ""),
                Key=destination_path,
                Body=file_content,
                ContentType=(file.content_type or "application/octet-stream")
            )
            
            logger.info(f"File saved to S3: {destination_path}")
            return destination_path
        except Exception as e:
            logger.error(f"Error saving file to S3: {e}")
            raise
        finally:
            await file.close()

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from S3 storage.

        Args:
            file_path: The path of the file to delete

        Returns:
            True if the file was deleted, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=(self.bucket_name or ""),
                Key=file_path
            )
            logger.info(f"File deleted from S3: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False

    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        Get a URL for accessing a file in S3 storage.

        Args:
            file_path: The path of the file
            expires_in: The number of seconds the URL should be valid for

        Returns:
            The URL for accessing the file
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_path
                },
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in S3 storage.

        Args:
            file_path: The path of the file to check

        Returns:
            True if the file exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=(self.bucket_name or ""),
                Key=file_path
            )
            return True
        except Exception:
            return False

    async def list_files(self, directory_path: str) -> list[str]:
        """
        List files in a directory in S3 storage.

        Args:
            directory_path: The path of the directory to list

        Returns:
            A list of file paths
        """
        try:
            # Ensure directory path ends with a slash
            if not directory_path.endswith('/'):
                directory_path += '/'
                
            response = self.s3_client.list_objects_v2(
                Bucket=(self.bucket_name or ""),
                Prefix=directory_path
            )
            
            if 'Contents' not in response:
                return []
                
            return [obj['Key'] for obj in response['Contents']]
        except Exception as e:
            logger.error(f"Error listing files in S3: {e}")
            return []


def get_storage_service() -> StorageService:
    """
    Factory function to get the appropriate storage service based on configuration.

    Returns:
        An instance of a StorageService implementation
    """
    storage_type = settings.storage_type.lower()
    
    if storage_type == "local":
        return LocalStorageService()
    if storage_type == "s3":
        return S3StorageService()
    logger.warning(f"Unknown storage type: {storage_type}, using local storage")
    return LocalStorageService()
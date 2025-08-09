import os
import uuid
from typing import List

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audio import Audio
from app.domain.enums import AudioStatus
from app.repositories.audio_repository import AudioRepository
from app.schemas.file import AudioCreate, FileUpdate
from app.services.storage_service import get_storage_service


class AudioService:
    """
    Service for audio operations
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.audio_repository = AudioRepository(db)
        self.storage_service = get_storage_service()

    async def get_audio(self, audio_id: int, user_id: int) -> Audio:
        """
        Get an audio file by ID
        """
        audio = await self.audio_repository.get(audio_id)
        if not audio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audio with ID {audio_id} not found",
            )
        
        if audio.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this audio file",
            )
        
        return audio

    async def get_audios_by_project(self, project_id: int, user_id: int) -> List[Audio]:
        """
        Get all audio files for a project
        """
        audios = await self.audio_repository.get_by_project(project_id)
        # Filter audios by user_id for security
        return [audio for audio in audios if audio.user_id == user_id]

    async def get_audios_by_user(self, user_id: int) -> List[Audio]:
        """
        Get all audio files for a user
        """
        return await self.audio_repository.get_by_user(user_id)

    async def create_audio(self, audio_in: AudioCreate, user_id: int, file: UploadFile) -> Audio:
        """
        Create a new audio file
        """
        # Generate a unique filename
        filename = file.filename or ""
        file_extension = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create the destination path
        destination_path = f"{user_id}/audios/{unique_filename}"
        
        # Save the file using the storage service
        file_path = await self.storage_service.save_file(file, destination_path, user_id)
        
        # Create the audio in the database with the filename set
        obj_data = audio_in.model_dump()
        obj_data["filename"] = unique_filename
        audio_create = AudioCreate(**obj_data)
        
        return await self.audio_repository.create_with_owner(audio_create, user_id, file_path)

    async def update_audio(self, audio_id: int, update_data: FileUpdate, user_id: int) -> Audio:
        """
        Update an audio file
        """
        audio = await self.get_audio(audio_id, user_id)
        return await self.audio_repository.update(audio, update_data)

    async def update_audio_status(self, audio_id: int, status: AudioStatus, user_id: int) -> Audio:
        """
        Update an audio file's status
        """
        audio = await self.get_audio(audio_id, user_id)
        return await self.audio_repository.update_status(audio, status)

    async def delete_audio(self, audio_id: int, user_id: int) -> None:
        """
        Delete an audio file
        """
        audio = await self.get_audio(audio_id, user_id)
        
        # Delete the file
        await self.storage_service.delete_file(audio.file_path)
        
        # Delete the database record
        await self.audio_repository.delete(audio_id)
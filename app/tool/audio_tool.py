from typing import Optional

from pydantic import Field, PrivateAttr

from app.audio.audio_processor import AudioProcessor
from app.audio.whisper_service import WhisperService
from app.logger import logger
from app.tools import BaseTool


class AudioTool(BaseTool):
    """Tool for transcribing audio files using OpenAI Whisper."""

    name: str = "transcribe_audio"
    description: str = """Transcribe audio files to text using Whisper AI.

This tool can:
- Transcribe audio files in various formats (mp3, wav, m4a, etc.)
- Handle long audio files through automatic compression and chunking
- Support multiple languages (Portuguese, English, etc.)

Args:
    file_path: Path to the audio file to transcribe
    language: Optional language code (e.g., 'pt' for Portuguese, 'en' for English)

Returns:
    The transcribed text from the audio file

Example:
    transcribe_audio(file_path="workspace/audio/meeting.mp3", language="pt")
"""

    _processor: AudioProcessor = PrivateAttr()
    _whisper: WhisperService = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._processor = AudioProcessor()
        self._whisper = WhisperService()

    async def execute(self, file_path: str, language: Optional[str] = None) -> str:
        """
        Execute audio transcription.

        Args:
            file_path: Path to audio file
            language: Optional language code

        Returns:
            Transcription text
        """
        try:
            # 1. Validate file
            is_valid, error_msg = self._processor.validate_audio(file_path)
            if not is_valid:
                return f"Error: {error_msg}"

            logger.info(f"🎙️ Transcribing audio: {file_path}")

            # 2. Check file size
            file_size_mb = self._processor.get_file_size_mb(file_path)
            logger.info(f"📊 File size: {file_size_mb:.2f} MB")

            processed_path = file_path

            # 3. Compress if too large
            if file_size_mb > AudioProcessor.MAX_FILE_SIZE_MB:
                logger.info("🗜️ File too large, compressing...")

                # Determine bitrate based on duration
                duration = self._processor.get_duration(file_path)
                if duration > 3600:  # > 1 hour
                    bitrate = "32k"
                elif duration > 1800:  # > 30 min
                    bitrate = "48k"
                else:
                    bitrate = "64k"

                compressed_path = self._processor.compress_audio(
                    file_path, target_bitrate=bitrate
                )
                compressed_size = self._processor.get_file_size_mb(compressed_path)
                logger.info(f"✅ Compressed to {compressed_size:.2f} MB")

                processed_path = compressed_path

            # 4. Check if still too large (need chunking)
            final_size = self._processor.get_file_size_mb(processed_path)

            if final_size > AudioProcessor.MAX_FILE_SIZE_MB:
                logger.info("✂️ Still too large, splitting into chunks...")
                chunks = self._processor.split_audio(processed_path, chunk_duration=600)
                logger.info(f"📦 Created {len(chunks)} chunks")

                # Transcribe chunks
                transcript = await self._whisper.transcribe_chunked(
                    chunks, language=language
                )
            else:
                # Direct transcription
                result = await self._whisper.transcribe(
                    processed_path, language=language
                )
                transcript = result["text"]

            # 5. Cleanup temp files
            self._processor.cleanup_temp_files()

            logger.info(f"✅ Transcription complete ({len(transcript)} characters)")
            return transcript

        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            self._processor.cleanup_temp_files()
            return f"Error during transcription: {str(e)}"

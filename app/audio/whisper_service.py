from typing import Dict, List, Optional

from app.llm import LLM


class WhisperService:
    """
    Interface with OpenAI Whisper API for audio transcription.
    """

    def __init__(self):
        self.llm = LLM()
        self.client = self.llm.client

    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        response_format: str = "text",
    ) -> Dict:
        """
        Transcribe audio file using Whisper API.

        Args:
            audio_path: Path to audio file
            language: Optional language code (e.g., 'pt', 'en')
            response_format: 'text', 'json', or 'verbose_json'

        Returns:
            Transcription result
        """
        with open(audio_path, "rb") as audio_file:
            params = {
                "model": "whisper-1",
                "file": audio_file,
                "response_format": response_format,
            }

            if language:
                params["language"] = language

            response = await self.client.audio.transcriptions.create(**params)

            # Handle different response formats
            if response_format == "text":
                return {"text": response}
            else:
                return (
                    response.model_dump()
                    if hasattr(response, "model_dump")
                    else response
                )

    async def transcribe_chunked(
        self, audio_chunks: List[str], language: Optional[str] = None
    ) -> str:
        """
        Transcribe multiple audio chunks and merge results.

        Args:
            audio_chunks: List of paths to audio chunk files
            language: Optional language code

        Returns:
            Merged transcription text
        """
        transcripts = []

        for i, chunk_path in enumerate(audio_chunks):
            result = await self.transcribe(
                chunk_path, language=language, response_format="text"
            )
            transcripts.append(result["text"])

        # Merge transcriptions
        return self._merge_transcriptions(transcripts)

    def _merge_transcriptions(self, transcripts: List[str]) -> str:
        """
        Merge multiple transcriptions into a single text.

        Args:
            transcripts: List of transcription texts

        Returns:
            Merged text
        """
        # Simple concatenation with spacing
        return " ".join(transcripts)

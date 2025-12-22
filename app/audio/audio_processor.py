import os
from pathlib import Path
from typing import List, Tuple

try:
    from pydub import AudioSegment

    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


class AudioProcessor:
    """
    Handles audio file validation, compression, and chunking.
    """

    SUPPORTED_FORMATS = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
    MAX_FILE_SIZE_MB = 25  # Whisper API limit

    def __init__(self, temp_dir: str = "workspace/temp/audio"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        self.temp_files = []

    def validate_audio(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate audio file format and existence.

        Returns:
            (is_valid, error_message)
        """
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        ext = Path(file_path).suffix.lower().lstrip(".")
        if ext not in self.SUPPORTED_FORMATS:
            return (
                False,
                f"Unsupported format: {ext}. Supported: {', '.join(self.SUPPORTED_FORMATS)}",
            )

        return True, ""

    def get_file_size_mb(self, file_path: str) -> float:
        """Get file size in MB."""
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)

    def get_duration(self, file_path: str) -> float:
        """
        Get audio duration in seconds.
        Requires pydub.
        """
        if not PYDUB_AVAILABLE:
            return 0.0

        try:
            audio = AudioSegment.from_file(file_path)
            return len(audio) / 1000.0  # Convert ms to seconds
        except Exception:
            return 0.0

    def compress_audio(self, input_path: str, target_bitrate: str = "64k") -> str:
        """
        Compress audio to reduce file size.

        Args:
            input_path: Path to input audio file
            target_bitrate: Target bitrate (e.g., "32k", "64k", "128k")

        Returns:
            Path to compressed file
        """
        if not PYDUB_AVAILABLE:
            raise RuntimeError(
                "pydub is required for audio compression. Install with: pip install pydub"
            )

        # Generate output path
        input_name = Path(input_path).stem
        output_path = os.path.join(self.temp_dir, f"{input_name}_compressed.mp3")

        # Load and compress
        audio = AudioSegment.from_file(input_path)
        audio.export(
            output_path,
            format="mp3",
            bitrate=target_bitrate,
            parameters=["-ac", "1"],  # Convert to mono to save space
        )

        self.temp_files.append(output_path)
        return output_path

    def split_audio(self, input_path: str, chunk_duration: int = 600) -> List[str]:
        """
        Split audio into chunks.

        Args:
            input_path: Path to input audio
            chunk_duration: Duration of each chunk in seconds (default: 10 minutes)

        Returns:
            List of paths to chunk files
        """
        if not PYDUB_AVAILABLE:
            raise RuntimeError("pydub is required for audio splitting")

        audio = AudioSegment.from_file(input_path)
        chunk_duration_ms = chunk_duration * 1000

        chunks = []
        input_name = Path(input_path).stem

        for i, start_ms in enumerate(range(0, len(audio), chunk_duration_ms)):
            chunk = audio[start_ms : start_ms + chunk_duration_ms]
            chunk_path = os.path.join(self.temp_dir, f"{input_name}_chunk_{i}.mp3")
            chunk.export(chunk_path, format="mp3")
            chunks.append(chunk_path)
            self.temp_files.append(chunk_path)

        return chunks

    def cleanup_temp_files(self):
        """Remove all temporary files created during processing."""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
        self.temp_files = []

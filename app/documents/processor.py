"""
Document Processor - File Upload and Text Extraction

Handles file upload, validation, text extraction, and chunking
for document storage and search.

Supported formats: PDF, DOCX, TXT, MD
"""

import hashlib
import io
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Document parsers
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

from app.logger import logger


class DocumentProcessor:
    """Process uploaded files for storage and search"""

    SUPPORTED_TYPES = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "text/plain": ".txt",
        "text/markdown": ".md",
        "text/x-markdown": ".md",
    }

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    CHUNK_SIZE = 1000  # characters
    CHUNK_OVERLAP = 200  # characters

    @staticmethod
    def validate_file(
        filename: str, file_size: int, content_type: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validate uploaded file

        Args:
            filename: Name of the file
            file_size: Size in bytes
            content_type: MIME type

        Returns:
            (is_valid, error_message)
        """
        # Check size
        if file_size > DocumentProcessor.MAX_FILE_SIZE:
            return (
                False,
                f"File too large: {file_size} bytes (max: {DocumentProcessor.MAX_FILE_SIZE})",
            )

        if file_size == 0:
            return False, "File is empty"

        # Check extension
        ext = Path(filename).suffix.lower()
        if ext not in DocumentProcessor.SUPPORTED_TYPES.values():
            return False, f"Unsupported file extension: {ext}"

        # Check content type if provided
        if content_type and content_type not in DocumentProcessor.SUPPORTED_TYPES:
            # Try to guess from filename
            guessed_type, _ = mimetypes.guess_type(filename)
            if guessed_type not in DocumentProcessor.SUPPORTED_TYPES:
                return False, f"Unsupported file type: {content_type}"

        return True, ""

    @staticmethod
    def extract_text_from_bytes(
        file_bytes: bytes, filename: str, content_type: Optional[str] = None
    ) -> str:
        """
        Extract text from file bytes

        Args:
            file_bytes: File content as bytes
            filename: Original filename
            content_type: MIME type

        Returns:
            Extracted text
        """
        try:
            # Determine file type
            ext = Path(filename).suffix.lower()

            if ext == ".pdf":
                if PdfReader is None:
                    raise ImportError("pypdf not installed. Run: pip install pypdf")
                return DocumentProcessor._extract_pdf_from_bytes(file_bytes)

            elif ext == ".docx":
                if DocxDocument is None:
                    raise ImportError(
                        "python-docx not installed. Run: pip install python-docx"
                    )
                return DocumentProcessor._extract_docx_from_bytes(file_bytes)

            elif ext in [".txt", ".md"]:
                return file_bytes.decode("utf-8")

            else:
                raise ValueError(f"Unsupported file extension: {ext}")

        except Exception as e:
            logger.error(f"Text extraction error for {filename}: {e}")
            raise

    @staticmethod
    def _extract_pdf_from_bytes(file_bytes: bytes) -> str:
        """Extract text from PDF bytes"""
        reader = PdfReader(io.BytesIO(file_bytes))
        text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
        return "\n\n".join(text)

    @staticmethod
    def _extract_docx_from_bytes(file_bytes: bytes) -> str:
        """Extract text from DOCX bytes"""
        doc = DocxDocument(io.BytesIO(file_bytes))
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n\n".join(paragraphs)

    @staticmethod
    def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Input text
            chunk_size: Size of each chunk (default: CHUNK_SIZE)
            overlap: Overlap between chunks (default: CHUNK_OVERLAP)

        Returns:
            List of text chunks
        """
        if chunk_size is None:
            chunk_size = DocumentProcessor.CHUNK_SIZE
        if overlap is None:
            overlap = DocumentProcessor.CHUNK_OVERLAP

        chunks = []
        start = 0
        text_length = len(text)

        if text_length <= chunk_size:
            return [text]

        while start < text_length:
            end = start + chunk_size

            # Don't split in the middle of a sentence if possible
            if end < text_length:
                # Try to find sentence boundary
                for char in [". ", "! ", "? ", "\n\n"]:
                    last_boundary = text.rfind(char, start, end)
                    if last_boundary != -1 and last_boundary > start + overlap:
                        end = last_boundary + len(char)
                        break
                else:
                    # Fallback: find last space
                    last_space = text.rfind(" ", start, end)
                    if last_space != -1 and last_space > start:
                        end = last_space

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap

        return chunks

    @staticmethod
    def extract_metadata(
        filename: str,
        file_size: int,
        file_type: str,
        author: Optional[str] = None,
        file_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract file metadata

        Args:
            filename: Filename
            file_size: Size in bytes
            file_type: MIME type
            author: Optional author name
            file_hash: Optional file hash

        Returns:
            Metadata dictionary
        """
        return {
            "filename": filename,
            "file_size": file_size,
            "file_type": file_type,
            "author": author or "Unknown",
            "extension": Path(filename).suffix.lower(),
            "uploaded_at": datetime.now().isoformat(),
            "file_hash": file_hash,
        }

    @staticmethod
    def generate_file_hash(file_bytes: bytes) -> str:
        """
        Generate SHA256 hash of file

        Args:
            file_bytes: File content

        Returns:
            SHA256 hash hex string
        """
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def get_file_info(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Get comprehensive file information

        Args:
            file_bytes: File content
            filename: Filename

        Returns:
            File information dict
        """
        return {
            "size": len(file_bytes),
            "hash": DocumentProcessor.generate_file_hash(file_bytes),
            "extension": Path(filename).suffix.lower(),
            "mime_type": mimetypes.guess_type(filename)[0],
        }

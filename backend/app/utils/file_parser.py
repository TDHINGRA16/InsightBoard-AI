"""
File parser for extracting text from uploaded files.
"""

from typing import Optional

from app.core.exceptions import FileProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)


def extract_text_from_file(
    file_content: bytes,
    file_extension: str,
) -> str:
    """
    Extract text content from a file.

    Args:
        file_content: Raw file bytes
        file_extension: File extension (e.g., '.txt', '.pdf')

    Returns:
        str: Extracted text content

    Raises:
        FileProcessingError: If file cannot be parsed
    """
    ext = file_extension.lower()

    if ext == ".txt":
        return _extract_from_txt(file_content)
    elif ext == ".pdf":
        return _extract_from_pdf(file_content)
    else:
        raise FileProcessingError(f"Unsupported file type: {ext}")


def _extract_from_txt(content: bytes) -> str:
    """
    Extract text from a plain text file.

    Args:
        content: File bytes

    Returns:
        str: Decoded text
    """
    # Try common encodings
    encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]

    for encoding in encodings:
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue

    raise FileProcessingError("Could not decode text file with any supported encoding")


def _extract_from_pdf(content: bytes) -> str:
    """
    Extract text from a PDF file.

    Args:
        content: File bytes

    Returns:
        str: Extracted text

    Note:
        This is a placeholder implementation. For production,
        use pdfplumber or PyPDF2.
    """
    try:
        # Try to import pdfplumber
        import pdfplumber
        import io

        text_parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

        if not text_parts:
            raise FileProcessingError("PDF appears to contain no extractable text")

        return "\n\n".join(text_parts)

    except ImportError:
        logger.warning("pdfplumber not installed, using fallback PDF extraction")
        return _extract_pdf_fallback(content)
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise FileProcessingError(f"Could not extract text from PDF: {str(e)}")


def _extract_pdf_fallback(content: bytes) -> str:
    """
    Fallback PDF extraction when pdfplumber is not available.

    This is a very basic extraction that looks for text streams.
    Not recommended for production use.

    Args:
        content: PDF file bytes

    Returns:
        str: Extracted text (may be incomplete)
    """
    import re

    # Very basic PDF text extraction
    # This will only work for simple PDFs with uncompressed text

    try:
        # Decode as latin-1 to handle binary
        content_str = content.decode("latin-1")

        # Find text objects in PDF
        text_parts = []

        # Look for BT...ET blocks (text objects)
        bt_pattern = re.compile(r"BT\s*(.*?)\s*ET", re.DOTALL)

        for match in bt_pattern.finditer(content_str):
            block = match.group(1)

            # Look for text strings in parentheses or hex
            tj_pattern = re.compile(r"\((.*?)\)|<([0-9A-Fa-f]+)>")

            for tj_match in tj_pattern.finditer(block):
                if tj_match.group(1):
                    # Parentheses string
                    text = tj_match.group(1)
                    # Unescape
                    text = text.replace("\\n", "\n")
                    text = text.replace("\\r", "\r")
                    text = text.replace("\\t", "\t")
                    text = re.sub(r"\\(.)", r"\1", text)
                    text_parts.append(text)
                elif tj_match.group(2):
                    # Hex string
                    hex_str = tj_match.group(2)
                    try:
                        text = bytes.fromhex(hex_str).decode("utf-8", errors="ignore")
                        text_parts.append(text)
                    except ValueError:
                        pass

        if text_parts:
            return " ".join(text_parts)

        # If basic extraction fails, return a message
        return "[PDF content could not be extracted. Please install pdfplumber for full PDF support.]"

    except Exception as e:
        logger.error(f"Fallback PDF extraction failed: {e}")
        raise FileProcessingError("Could not extract text from PDF")


def get_file_info(
    filename: str,
    content: bytes,
) -> dict:
    """
    Get basic file information.

    Args:
        filename: Original filename
        content: File bytes

    Returns:
        dict: File information
    """
    import os
    import hashlib

    _, ext = os.path.splitext(filename)

    return {
        "filename": filename,
        "extension": ext.lower(),
        "size_bytes": len(content),
        "content_hash": hashlib.sha256(content).hexdigest(),
    }

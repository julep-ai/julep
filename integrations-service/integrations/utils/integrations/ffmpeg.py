import asyncio
import base64
import os
import shutil
import tempfile
from functools import lru_cache
from typing import Tuple

from beartype import beartype
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import FfmpegSearchArguments
from ...models import FfmpegSearchOutput


# Cache for format validation
@lru_cache(maxsize=128)
def _sync_validate_format(binary_prefix: bytes) -> Tuple[bool, str]:
    """Cached synchronous implementation of format validation"""
    signatures = {
        # Video formats
        b"\x66\x74\x79\x70\x69\x73\x6f\x6d": "video/mp4",  # MP4
        b"\x66\x74\x79\x70\x4d\x53\x4e\x56": "video/mp4",  # MP4
        b"\x00\x00\x00\x1c\x66\x74\x79\x70": "video/mp4",  # MP4
        b"\x1a\x45\xdf\xa3": "video/webm",  # WebM
        b"\x00\x00\x01\x00": "video/avi",  # AVI
        b"\x30\x26\xb2\x75": "video/wmv",  # WMV
        # Audio formats
        b"\x49\x44\x33": "audio/mpeg",  # MP3
        b"\xff\xfb": "audio/mpeg",  # MP3
        b"\x52\x49\x46\x46": "audio/wav",  # WAV
        b"\x4f\x67\x67\x53": "audio/ogg",  # OGG
        b"\x66\x4c\x61\x43": "audio/flac",  # FLAC
        # Image formats
        b"\xff\xd8\xff": "image/jpeg",  # JPEG
        b"\x89\x50\x4e\x47": "image/png",  # PNG
        b"\x47\x49\x46": "image/gif",  # GIF
        b"\x49\x49\x2a\x00": "image/tiff",  # TIFF
        b"\x42\x4d": "image/bmp",  # BMP
    }

    for signature, mime_type in signatures.items():
        if binary_prefix.startswith(signature):
            return True, mime_type

    return False, "application/octet-stream"


async def validate_format(binary_data: bytes) -> Tuple[bool, str]:
    """Validate file format using file signatures"""
    # Only check first 16 bytes for efficiency
    binary_prefix = binary_data[:16]
    return _sync_validate_format(binary_prefix)


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def bash_cmd(arguments: FfmpegSearchArguments) -> FfmpegSearchOutput:
    """Execute a FFmpeg bash command using base64-encoded input data."""
    try:
        assert isinstance(arguments, FfmpegSearchArguments), "Invalid arguments"

        # Decode base64 input
        try:
            input_data = base64.b64decode(arguments.file)
        except:
            return FfmpegSearchOutput(
                fileoutput="Error: Invalid base64 input", result=False, mime_type=None
            )

        # Validate input format
        is_valid, input_mime = await validate_format(input_data)

        if not is_valid:
            return FfmpegSearchOutput(
                fileoutput="Error: Unsupported input file format",
                result=False,
                mime_type=None,
            )

        # Create temporary directory
        temp_dir = tempfile.mkdtemp()

        # Get the output filename from the last argument of the FFmpeg command
        cmd_parts = arguments.cmd.split()
        output_filename = cmd_parts[-1]  # e.g., "output.mp4"
        output_path = os.path.join(temp_dir, output_filename)

        # Modify FFmpeg command
        for i, part in enumerate(cmd_parts):
            if part == "-i" and i + 1 < len(cmd_parts):
                cmd_parts[i + 1] = "pipe:0"
        cmd_parts[-1] = output_path  # Replace the last argument with full output path
        cmd = " ".join(cmd_parts)

        # Execute FFmpeg
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Process FFmpeg output
        stdout, stderr = await process.communicate(input=input_data)
        success = process.returncode == 0

        if success and os.path.exists(output_path):
            # Read the output file
            with open(output_path, "rb") as f:
                output_data = f.read()
                # Convert to base64
                output_base64 = base64.b64encode(output_data).decode("utf-8")

            _, output_mime = await validate_format(output_data)

            # Clean up
            shutil.rmtree(temp_dir)

            return FfmpegSearchOutput(
                fileoutput=output_base64,
                result=True,
                mime_type=output_mime,
            )

        # Clean up in case of failure
        shutil.rmtree(temp_dir)
        error_msg = stderr.decode() if stderr else "Unknown error occurred"
        return FfmpegSearchOutput(
            fileoutput=f"Error: FFmpeg processing failed - {error_msg}",
            result=False,
            mime_type=None,
        )

    except Exception as e:
        # Clean up in case of exception
        if "temp_dir" in locals():
            shutil.rmtree(temp_dir)
        return FfmpegSearchOutput(
            fileoutput=f"Error: {str(e)}", result=False, mime_type=None
        )

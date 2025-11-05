"""
MODULE: zip_utils.py

RESPONSIBILITY:
    Packages processing outputs into downloadable ZIP archives.

AI NAVIGATION MARKERS:
    Entry: create_zip_archive()
"""

from io import BytesIO
from pathlib import Path
import zipfile
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════
# ═════ ZIP ARCHIVE CREATION ═════
# ═════════════════════════════════════════════════════════════════════════


def create_zip_archive(output_dir: Path, archive_name: Optional[str] = None) -> BytesIO:
    """
    Create ZIP archive of all output files.

    Args:
        output_dir: Directory containing output files to archive
        archive_name: Optional name for the archive (default: "geotechnical_plots")

    Returns:
        BytesIO buffer containing ZIP archive
    """
    if archive_name is None:
        archive_name = "geotechnical_plots"

    zip_buffer = BytesIO()

    try:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Walk through output directory and add all files
            file_count = 0
            for file_path in output_dir.rglob("*"):
                if file_path.is_file():
                    # Calculate relative path for archive
                    arcname = file_path.relative_to(output_dir)
                    zf.write(file_path, arcname=arcname)
                    file_count += 1

            logger.info(f"📦 Created ZIP archive with {file_count} files")

        # Reset buffer position to beginning
        zip_buffer.seek(0)
        return zip_buffer

    except Exception as e:
        logger.error(f"❌ Error creating ZIP archive: {str(e)}")
        raise

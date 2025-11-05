"""
MODULE: validation.py

RESPONSIBILITY:
    Validates CSV files for geotechnical processing.

AI NAVIGATION MARKERS:
    Entry: validate_csv_files()
"""

from typing import Dict, Any, List
from pathlib import Path
import pandas as pd
import io


# ═════════════════════════════════════════════════════════════════════════
# ═════ CSV VALIDATION FUNCTIONS ═════
# ═════════════════════════════════════════════════════════════════════════


def validate_csv_files(files: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate uploaded CSV files for geotechnical processing.

    Args:
        files: Dictionary of uploaded file objects
               {"mapping": UploadedFile, "location": UploadedFile, "classification": UploadedFile}

    Returns:
        Dictionary with validation results
        {"is_valid": bool, "errors": List[str], "warnings": List[str]}
    """
    errors: List[str] = []
    warnings: List[str] = []

    # Check if all required files are present
    required_files = ["mapping", "location", "classification"]
    missing_files = [f for f in required_files if not files.get(f)]

    if missing_files:
        errors.append(f"Missing required files: {', '.join(missing_files)}")
        return {"is_valid": False, "errors": errors, "warnings": warnings}

    # Validate mapping CSV
    try:
        mapping_df = pd.read_csv(io.BytesIO(files["mapping"].getvalue()))
        # Check for parameter column (case insensitive)
        param_col = None
        for col in mapping_df.columns:
            if col.lower() == "parameter":
                param_col = col
                break

        if param_col is None:
            errors.append("Mapping CSV missing 'parameter' column")
        else:
            # Check if LiquidLimit and PlasticityIndex are mapped
            params = mapping_df[param_col].tolist()
            if "LiquidLimit" not in params:
                errors.append("Mapping CSV missing 'LiquidLimit' parameter")
            if "PlasticityIndex" not in params:
                errors.append("Mapping CSV missing 'PlasticityIndex' parameter")

    except Exception as e:
        errors.append(f"Error reading mapping CSV: {str(e)}")

    # Validate location CSV
    try:
        location_df = pd.read_csv(io.BytesIO(files["location"].getvalue()))
        has_location_id = any(
            col in location_df.columns for col in ["LocationID", "Location ID"]
        )
        has_investigation = "Investigation" in location_df.columns

        if not has_location_id:
            errors.append("Location CSV missing 'LocationID' or 'Location ID' column")
        if not has_investigation:
            warnings.append(
                "Location CSV missing 'Investigation' column - will use default investigation name"
            )

    except Exception as e:
        errors.append(f"Error reading location CSV: {str(e)}")

    # Validate classification CSV
    try:
        classification_df = pd.read_csv(io.BytesIO(files["classification"].getvalue()))

        # Check for geology and depth columns
        has_geology = any(
            col in classification_df.columns
            for col in [
                "GeologyCode",
                "Geology Code",
                "GeologyCodeDescription",
                "Geology Code Description",
            ]
        )
        has_depth = any(
            col in classification_df.columns
            for col in ["DepthTop", "SampleTop", "Test Depth", "Top Depth"]
        )

        if not has_geology:
            errors.append("Classification CSV missing geology columns")
        if not has_depth:
            errors.append("Classification CSV missing depth columns")

        # Check for parameter columns (should have at least one of LL or PI)
        has_ll = (
            "LiquidLimit" in classification_df.columns
            or "Liquid Limit" in classification_df.columns
        )
        has_pi = (
            "PlasticityIndex" in classification_df.columns
            or "Plasticity Index" in classification_df.columns
        )

        if not (has_ll or has_pi):
            errors.append(
                "Classification CSV missing both 'LiquidLimit' and 'PlasticityIndex' columns"
            )
        elif not has_ll:
            warnings.append("Classification CSV missing 'LiquidLimit' column")
        elif not has_pi:
            warnings.append("Classification CSV missing 'PlasticityIndex' column")

    except Exception as e:
        errors.append(f"Error reading classification CSV: {str(e)}")

    return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def save_uploaded_files(
    uploaded_files: Dict[str, Any], temp_dir: Path
) -> Dict[str, Path]:
    """
    Save uploaded file objects to temporary directory.

    Args:
        uploaded_files: Dictionary of Streamlit uploaded file objects
        temp_dir: Temporary directory path

    Returns:
        Dictionary mapping file keys to saved file paths
    """
    file_paths: Dict[str, Path] = {}

    for key, file_obj in uploaded_files.items():
        if file_obj is not None:
            # Use original filename to preserve parameter mapping compatibility
            # This ensures the saved filename matches what's in the mapping CSV
            original_name = file_obj.name

            # Save file with original name
            file_path = temp_dir / original_name
            with open(file_path, "wb") as f:
                f.write(file_obj.getvalue())

            file_paths[key] = file_path

    return file_paths

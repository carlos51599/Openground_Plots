"""
MODULE: validation.py

RESPONSIBILITY:
    Validates CSV files for geotechnical processing and determines
    required files dynamically from mapping CSV.

AI NAVIGATION MARKERS:
    Entry: validate_csv_files(), get_required_files_from_mapping()
"""

from typing import Dict, Any, List, Set
from pathlib import Path
import pandas as pd
import io


# ═════════════════════════════════════════════════════════════════════════
# ═════ PLOT TYPE PARAMETER MAPPING ═════
# ═════════════════════════════════════════════════════════════════════════

# Define which parameters are required for each plot type
PLOT_TYPE_PARAMETERS: Dict[str, List[str]] = {
    "aline": ["LiquidLimit", "PlasticityIndex"],
    "strength": ["UndrainedShearStrength"],
}


# ═════════════════════════════════════════════════════════════════════════
# ═════ DYNAMIC FILE REQUIREMENT FUNCTIONS ═════
# ═════════════════════════════════════════════════════════════════════════


def get_required_files_from_mapping(
    mapping_path: Path, plot_types: List[str]
) -> Dict[str, Set[str]]:
    """
    Extract required CSV files from mapping CSV based on plot types.

    Args:
        mapping_path: Path to the mapping CSV file
        plot_types: List of plot types (e.g., ["aline"], ["strength"])

    Returns:
        Dictionary with keys:
        - "required_files": Set of required CSV filenames
        - "required_parameters": Set of required parameter names
    """
    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping CSV not found: {mapping_path}")

    # Read mapping CSV
    mapping_df = pd.read_csv(mapping_path)

    # Collect all required parameters for selected plot types
    required_params: Set[str] = set()
    for plot_type in plot_types:
        if plot_type in PLOT_TYPE_PARAMETERS:
            required_params.update(PLOT_TYPE_PARAMETERS[plot_type])

    # Find all CSV files that contain the required parameters
    required_files: Set[str] = set()
    for param in required_params:
        param_rows = mapping_df[mapping_df["parameter"] == param]
        if not param_rows.empty:
            # Add all CSV files for this parameter
            csv_files = param_rows["csv_file"].dropna().unique()
            required_files.update(csv_files)

    return {
        "required_files": required_files,
        "required_parameters": required_params,
    }


def normalize_filename(filename: str) -> str:
    """
    Normalize CSV filename for comparison (case-insensitive, no extension).

    Args:
        filename: Original filename

    Returns:
        Normalized filename (lowercase, no .csv extension)
    """
    return filename.lower().replace(".csv", "").strip()


def get_file_upload_label(filename: str) -> str:
    """
    Generate user-friendly label for file upload widget.

    Args:
        filename: CSV filename from mapping

    Returns:
        User-friendly label (removes ' by Geology.csv' suffix)
    """
    # Remove common suffixes for cleaner display
    label = filename.replace(" by Geology.csv", "").replace(".csv", "")
    return label


def map_uploaded_files_to_parameters(
    uploaded_files: Dict[str, Path],
    mapping_path: Path,
    plot_types: List[str],
) -> Dict[str, List[Path]]:
    """
    Map uploaded files to parameters based on mapping CSV.

    Reads the mapping CSV to determine which uploaded files contain
    which parameters required for the selected plot types.

    Args:
        uploaded_files: Dict mapping normalized filename keys to file paths
        mapping_path: Path to the mapping CSV file
        plot_types: List of plot types (e.g., ["aline"], ["strength"])

    Returns:
        Dictionary mapping parameter names to list of file paths that contain them.
        Example: {"LiquidLimit": [Path("classification.csv")],
                  "PlasticityIndex": [Path("classification.csv")]}
    """
    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping CSV not found: {mapping_path}")

    # Read mapping CSV
    mapping_df = pd.read_csv(mapping_path)

    # Collect all required parameters for selected plot types
    required_params: Set[str] = set()
    for plot_type in plot_types:
        if plot_type in PLOT_TYPE_PARAMETERS:
            required_params.update(PLOT_TYPE_PARAMETERS[plot_type])

    # Build parameter to files mapping
    param_to_files: Dict[str, List[Path]] = {}

    for param in required_params:
        # Find all CSV files that contain this parameter
        param_rows = mapping_df[mapping_df["parameter"] == param]

        if param_rows.empty:
            continue

        csv_files = param_rows["csv_file"].dropna().unique()

        # Match CSV files to uploaded files
        matching_files: List[Path] = []
        for csv_filename in csv_files:
            normalized_csv = normalize_filename(csv_filename)
            matching_file = _find_matching_uploaded_file(normalized_csv, uploaded_files)
            if matching_file:
                matching_files.append(matching_file)

        if matching_files:
            param_to_files[param] = matching_files

    return param_to_files


def _find_matching_uploaded_file(
    normalized_csv: str, uploaded_files: Dict[str, Path]
) -> Path | None:
    """
    Find uploaded file matching normalized CSV name.

    Args:
        normalized_csv: Normalized CSV filename
        uploaded_files: Dict of uploaded files

    Returns:
        Matching file path or None
    """
    for upload_key, file_path in uploaded_files.items():
        # Skip non-data files
        if upload_key in ["location", "mapping"]:
            continue

        # Check if normalized names match
        if upload_key == normalized_csv:
            return file_path

    return None


# ═════════════════════════════════════════════════════════════════════════
# ═════ CSV VALIDATION FUNCTIONS ═════
# ═════════════════════════════════════════════════════════════════════════


def _validate_mapping_parameters(
    mapping_path: Path, required_parameters: Set[str], plot_types: List[str]
) -> List[str]:
    """
    Validate that required parameters exist in mapping CSV.

    Args:
        mapping_path: Path to mapping CSV
        required_parameters: Set of parameter names to check
        plot_types: List of plot types being validated

    Returns:
        List of error messages (empty if valid)
    """
    errors: List[str] = []

    try:
        mapping_df = pd.read_csv(mapping_path)
        # Check for parameter column (case insensitive)
        param_col = None
        for col in mapping_df.columns:
            if col.lower() == "parameter":
                param_col = col
                break

        if param_col is None:
            errors.append("Mapping CSV missing 'parameter' column")
        else:
            params = mapping_df[param_col].tolist()

            # Check if required parameters exist in mapping
            for required_param in required_parameters:
                if required_param not in params:
                    errors.append(
                        f"Mapping CSV missing '{required_param}' parameter "
                        f"(required for {', '.join(plot_types)} plots)"
                    )

    except Exception as e:
        errors.append(f"Error reading mapping CSV: {str(e)}")

    return errors


def _validate_location_csv(location_file: Any) -> tuple[List[str], List[str]]:
    """
    Validate Location Details CSV structure.

    Args:
        location_file: Uploaded location file object

    Returns:
        Tuple of (errors, warnings) lists
    """
    errors: List[str] = []
    warnings: List[str] = []

    try:
        location_df = pd.read_csv(io.BytesIO(location_file.getvalue()))
        has_location_id = any(
            col in location_df.columns for col in ["LocationID", "Location ID"]
        )
        has_investigation = "Investigation" in location_df.columns

        if not has_location_id:
            errors.append("Location CSV missing 'LocationID' or 'Location ID' column")
        if not has_investigation:
            warnings.append(
                "Location CSV missing 'Investigation' column - "
                "will use default investigation name"
            )

    except Exception as e:
        errors.append(f"Error reading location CSV: {str(e)}")

    return errors, warnings


def _check_uploaded_files(
    files: Dict[str, Any], required_csv_files: Set[str]
) -> tuple[List[str], List[str]]:
    """
    Check if required files are uploaded.

    Args:
        files: Dictionary of uploaded file objects
        required_csv_files: Set of required CSV filenames

    Returns:
        Tuple of (errors, warnings) lists
    """
    errors: List[str] = []
    warnings: List[str] = []

    # Normalize uploaded filenames for comparison
    uploaded_filenames = {
        normalize_filename(f.name): key
        for key, f in files.items()
        if f is not None and key != "location"
    }

    # Check for missing required files
    missing_files = []
    for required_file in required_csv_files:
        normalized_required = normalize_filename(required_file)
        if normalized_required not in uploaded_filenames:
            missing_files.append(required_file)

    if missing_files:
        errors.append(
            f"Missing required CSV files for selected plot types: "
            f"{', '.join(missing_files)}"
        )
        warnings.append(
            "Note: At least one file containing the required parameters "
            "must be uploaded. Multiple files may contain the same parameter "
            "with different priority ranks."
        )

    return errors, warnings


def validate_csv_files(
    files: Dict[str, Any], plot_types: List[str] = None, mapping_path: Path = None
) -> Dict[str, Any]:
    """
    Validate uploaded CSV files for geotechnical processing.

    Args:
        files: Dictionary of uploaded file objects
        plot_types: List of plot types to validate
                   (e.g., ["aline"], ["strength"], or ["aline", "strength"])
                   If None, defaults to ["aline"]
        mapping_path: Path to mapping CSV file (if None, uses default location)

    Returns:
        Dictionary with validation results
        {"is_valid": bool, "errors": List[str], "warnings": List[str]}
    """
    if plot_types is None:
        plot_types = ["aline"]

    errors: List[str] = []
    warnings: List[str] = []

    # Set default mapping path if not provided
    if mapping_path is None:
        mapping_path = (
            Path(__file__).parent
            / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"
        )

    # Location Details is always required (hardcoded)
    if not files.get("location"):
        errors.append("Missing required file: Location Details CSV")
        return {"is_valid": False, "errors": errors, "warnings": warnings}

    # Get required files dynamically from mapping CSV
    try:
        file_requirements = get_required_files_from_mapping(mapping_path, plot_types)
        required_csv_files = file_requirements["required_files"]
        required_parameters = file_requirements["required_parameters"]
    except Exception as e:
        errors.append(f"Error reading mapping CSV: {str(e)}")
        return {"is_valid": False, "errors": errors, "warnings": warnings}

    # Check if required files are uploaded
    upload_errors, upload_warnings = _check_uploaded_files(files, required_csv_files)
    errors.extend(upload_errors)
    warnings.extend(upload_warnings)

    # Validate mapping CSV parameters
    mapping_errors = _validate_mapping_parameters(
        mapping_path, required_parameters, plot_types
    )
    errors.extend(mapping_errors)

    # Validate location CSV
    loc_errors, loc_warnings = _validate_location_csv(files["location"])
    errors.extend(loc_errors)
    warnings.extend(loc_warnings)

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

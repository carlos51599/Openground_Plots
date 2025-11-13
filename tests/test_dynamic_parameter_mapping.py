"""
Test dynamic parameter to file mapping functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validation import map_uploaded_files_to_parameters, normalize_filename


def test_parameter_mapping_for_aline():
    """Test that A-line parameters map to classification file."""
    # Setup
    mapping_path = (
        Path(__file__).parent.parent
        / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"
    )

    # Simulate uploaded files
    uploaded_files = {
        "classification by geology": Path("C:/temp/Classification by Geology.csv"),
        "location": Path("C:/temp/Location Details.csv"),
        "mapping": mapping_path,
    }

    # Execute
    result = map_uploaded_files_to_parameters(uploaded_files, mapping_path, ["aline"])

    # Verify
    print("✅ Test: Parameter mapping for A-line")
    print(f"Parameters found: {list(result.keys())}")

    assert "LiquidLimit" in result, "LiquidLimit parameter should be found"
    assert "PlasticityIndex" in result, "PlasticityIndex parameter should be found"

    for param, files in result.items():
        print(f"  {param}: {[f.name for f in files]}")
        assert len(files) > 0, f"Parameter {param} should have at least one file"

    print("✅ All assertions passed!")


def test_parameter_mapping_for_strength():
    """Test that strength parameters map to correct files."""
    # Setup
    mapping_path = (
        Path(__file__).parent.parent
        / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"
    )

    # Simulate uploaded files (with various test files)
    uploaded_files = {
        "triaxial total stress by geology": Path(
            "C:/temp/Triaxial Total Stress by Geology.csv"
        ),
        "vane tests by geology": Path("C:/temp/Vane Tests by Geology.csv"),
        "location": Path("C:/temp/Location Details.csv"),
        "mapping": mapping_path,
    }

    # Execute
    result = map_uploaded_files_to_parameters(
        uploaded_files, mapping_path, ["strength"]
    )

    # Verify
    print("\n✅ Test: Parameter mapping for Strength")
    print(f"Parameters found: {list(result.keys())}")

    assert (
        "UndrainedShearStrength" in result
    ), "UndrainedShearStrength parameter should be found"

    for param, files in result.items():
        print(f"  {param}: {[f.name for f in files]}")
        assert len(files) > 0, f"Parameter {param} should have at least one file"

    print("✅ All assertions passed!")


def test_normalize_filename():
    """Test filename normalization."""
    print("\n✅ Test: Filename normalization")

    test_cases = [
        ("Classification by Geology.csv", "classification by geology"),
        ("Vane Tests by Geology.csv", "vane tests by geology"),
        ("Location Details.csv", "location details"),
        ("UPPERCASE.CSV", "uppercase"),
    ]

    for input_name, expected in test_cases:
        result = normalize_filename(input_name)
        print(f"  {input_name} → {result}")
        assert result == expected, f"Expected {expected}, got {result}"

    print("✅ All assertions passed!")


if __name__ == "__main__":
    test_normalize_filename()
    test_parameter_mapping_for_aline()
    test_parameter_mapping_for_strength()
    print("\n🎉 All tests passed successfully!")

"""
Test script for dynamic file requirements from mapping CSV.

Verifies that:
1. Required files are correctly extracted from mapping CSV
2. Different plot types request different files
3. Validation works with dynamic file requirements
"""

import sys
from pathlib import Path

# Add parent directory to path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from validation import (
    get_required_files_from_mapping,
    normalize_filename,
    get_file_upload_label,
    PLOT_TYPE_PARAMETERS,
)


def test_plot_type_parameters():
    """Test that plot type parameters are defined correctly."""
    print("=" * 70)
    print("TEST 1: Plot Type Parameters")
    print("=" * 70)

    print("\nDefined plot types and their required parameters:")
    for plot_type, params in PLOT_TYPE_PARAMETERS.items():
        print(f"  {plot_type}: {params}")

    assert "aline" in PLOT_TYPE_PARAMETERS, "Missing 'aline' plot type"
    assert "strength" in PLOT_TYPE_PARAMETERS, "Missing 'strength' plot type"
    assert (
        "LiquidLimit" in PLOT_TYPE_PARAMETERS["aline"]
    ), "Missing LiquidLimit for aline"
    assert (
        "PlasticityIndex" in PLOT_TYPE_PARAMETERS["aline"]
    ), "Missing PlasticityIndex for aline"
    assert (
        "UndrainedShearStrength" in PLOT_TYPE_PARAMETERS["strength"]
    ), "Missing UndrainedShearStrength for strength"

    print("\n✅ Plot type parameters test PASSED")


def test_aline_file_requirements():
    """Test file requirements for A-line plots."""
    print("\n" + "=" * 70)
    print("TEST 2: A-line File Requirements")
    print("=" * 70)

    mapping_path = app_dir / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"

    if not mapping_path.exists():
        print(f"❌ Mapping CSV not found: {mapping_path}")
        return False

    result = get_required_files_from_mapping(mapping_path, ["aline"])

    print(f"\nRequired parameters: {result['required_parameters']}")
    print(f"\nRequired files ({len(result['required_files'])}):")
    for file in sorted(result["required_files"]):
        print(f"  • {file}")

    assert (
        "LiquidLimit" in result["required_parameters"]
    ), "LiquidLimit not in required parameters"
    assert (
        "PlasticityIndex" in result["required_parameters"]
    ), "PlasticityIndex not in required parameters"
    assert len(result["required_files"]) > 0, "No required files found for aline plot"

    # Check that Classification by Geology is in the required files
    has_classification = any(
        "classification" in normalize_filename(f) for f in result["required_files"]
    )
    assert has_classification, "Classification by Geology not in required files"

    print("\n✅ A-line file requirements test PASSED")
    return True


def test_strength_file_requirements():
    """Test file requirements for Strength plots."""
    print("\n" + "=" * 70)
    print("TEST 3: Strength File Requirements")
    print("=" * 70)

    mapping_path = app_dir / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"

    result = get_required_files_from_mapping(mapping_path, ["strength"])

    print(f"\nRequired parameters: {result['required_parameters']}")
    print(f"\nRequired files ({len(result['required_files'])}):")
    for file in sorted(result["required_files"]):
        print(f"  • {file}")

    assert (
        "UndrainedShearStrength" in result["required_parameters"]
    ), "UndrainedShearStrength not in required parameters"
    assert (
        len(result["required_files"]) > 0
    ), "No required files found for strength plot"

    # Check for common strength test files
    normalized_files = {normalize_filename(f) for f in result["required_files"]}
    print("\nNormalized filenames:")
    for nf in sorted(normalized_files):
        print(f"  • {nf}")

    print("\n✅ Strength file requirements test PASSED")
    return True


def test_combined_plot_types():
    """Test file requirements when both plot types are selected."""
    print("\n" + "=" * 70)
    print("TEST 4: Combined Plot Types (aline + strength)")
    print("=" * 70)

    mapping_path = app_dir / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"

    result = get_required_files_from_mapping(mapping_path, ["aline", "strength"])

    print(f"\nRequired parameters: {result['required_parameters']}")
    print(f"\nRequired files ({len(result['required_files'])}):")
    for file in sorted(result["required_files"]):
        print(f"  • {file}")

    assert (
        "LiquidLimit" in result["required_parameters"]
    ), "LiquidLimit not in required parameters"
    assert (
        "UndrainedShearStrength" in result["required_parameters"]
    ), "UndrainedShearStrength not in required parameters"

    print("\n✅ Combined plot types test PASSED")
    return True


def test_filename_normalization():
    """Test filename normalization function."""
    print("\n" + "=" * 70)
    print("TEST 5: Filename Normalization")
    print("=" * 70)

    test_cases = [
        ("Classification by Geology.csv", "classification by geology"),
        ("SPT by Geology.CSV", "spt by geology"),
        ("Triaxial Total Stress by Geology.csv", "triaxial total stress by geology"),
        ("  CPT by Geology.csv  ", "cpt by geology"),
    ]

    print("\nTest cases:")
    for original, expected in test_cases:
        result = normalize_filename(original)
        print(f"  '{original}' → '{result}'")
        assert result == expected, f"Expected '{expected}', got '{result}'"

    print("\n✅ Filename normalization test PASSED")
    return True


def test_file_upload_labels():
    """Test generation of user-friendly upload labels."""
    print("\n" + "=" * 70)
    print("TEST 6: File Upload Labels")
    print("=" * 70)

    test_cases = [
        ("Classification by Geology.csv", "Classification"),
        ("SPT by Geology.csv", "SPT"),
        ("Triaxial Total Stress by Geology.csv", "Triaxial Total Stress"),
        (
            "Pressuremeter Test Results - General.csv",
            "Pressuremeter Test Results - General",
        ),
    ]

    print("\nTest cases:")
    for original, expected in test_cases:
        result = get_file_upload_label(original)
        print(f"  '{original}' → '{result}'")
        assert result == expected, f"Expected '{expected}', got '{result}'"

    print("\n✅ File upload labels test PASSED")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("DYNAMIC FILE REQUIREMENTS TEST SUITE")
    print("=" * 70)

    tests = [
        test_plot_type_parameters,
        test_aline_file_requirements,
        test_strength_file_requirements,
        test_combined_plot_types,
        test_filename_normalization,
        test_file_upload_labels,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            result = test_func()
            if result is None or result is True:
                passed += 1
        except Exception as e:
            print(f"\n❌ Test FAILED with error: {str(e)}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n❌ {failed} TEST(S) FAILED")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

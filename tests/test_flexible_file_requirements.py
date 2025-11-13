"""
Test script to verify flexible file requirements for parameter sources.

This script tests that:
1. Only one source file per parameter is required
2. Multiple source files for the same parameter are optional
3. Validation correctly identifies missing parameters vs missing optional sources
"""

from pathlib import Path
import sys

# Add parent directory to path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from validation import (
    get_parameter_source_files,
    get_required_files_from_mapping,
    validate_csv_files,
)


def test_parameter_source_mapping():
    """Test that parameter source mapping works correctly."""
    print("=" * 80)
    print("TEST 1: Parameter Source Mapping")
    print("=" * 80)
    
    mapping_path = app_dir / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"
    
    # Test for strength plot (has UndrainedShearStrength with 5 sources)
    param_sources = get_parameter_source_files(mapping_path, ["strength"])
    
    print(f"\n📊 Parameters for 'strength' plot:")
    for param, sources in param_sources.items():
        print(f"\n  Parameter: {param}")
        print(f"  Number of sources: {len(sources)}")
        for idx, source in enumerate(sources, 1):
            print(f"    {idx}. {source['csv_file']} (priority {source['priority_rank']})")
    
    # Verify UndrainedShearStrength has multiple sources
    assert "UndrainedShearStrength" in param_sources
    assert len(param_sources["UndrainedShearStrength"]) >= 4, \
        f"Expected at least 4 sources, got {len(param_sources['UndrainedShearStrength'])}"
    
    print("\n✅ Test 1 PASSED: Parameter source mapping works correctly")


def test_all_files_vs_required():
    """Test that all_files includes all possible sources."""
    print("\n" + "=" * 80)
    print("TEST 2: All Files vs Required Parameter Coverage")
    print("=" * 80)
    
    mapping_path = app_dir / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"
    
    # Test for strength plot
    file_reqs = get_required_files_from_mapping(mapping_path, ["strength"])
    
    print(f"\n📋 File requirements for 'strength' plot:")
    print(f"  Total possible source files: {len(file_reqs['all_files'])}")
    print(f"  Required parameters: {file_reqs['required_parameters']}")
    
    print(f"\n  All possible source files:")
    for idx, file in enumerate(sorted(file_reqs['all_files']), 1):
        print(f"    {idx}. {file}")
    
    # Verify we have all_files and parameter_sources
    assert "all_files" in file_reqs
    assert "parameter_sources" in file_reqs
    assert "required_parameters" in file_reqs
    
    print("\n✅ Test 2 PASSED: File requirements structure is correct")


def test_validation_with_one_source():
    """Test that validation passes with only one source per parameter."""
    print("\n" + "=" * 80)
    print("TEST 3: Validation with Minimum Sources")
    print("=" * 80)
    
    mapping_path = app_dir / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"
    
    # Create mock file object
    class MockFile:
        def __init__(self, name):
            self.name = name
            
        def getvalue(self):
            # Return minimal CSV content
            return b"LocationID,Investigation\nBH01,Test Investigation"
    
    # Test with only one source for UndrainedShearStrength
    # (Triaxial Total Stress by Geology.csv is priority 1)
    files = {
        "location": MockFile("Location Details.csv"),
        "triaxial total stress by geology": MockFile("Triaxial Total Stress by Geology.csv"),
    }
    
    print("\n📁 Testing validation with:")
    print("  - Location Details.csv (required)")
    print("  - Triaxial Total Stress by Geology.csv (priority 1 for UndrainedShearStrength)")
    
    result = validate_csv_files(files, ["strength"], mapping_path)
    
    print(f"\n  Validation result: {'✅ VALID' if result['is_valid'] else '❌ INVALID'}")
    
    if result["errors"]:
        print(f"\n  Errors:")
        for error in result["errors"]:
            print(f"    ❌ {error}")
    
    if result["warnings"]:
        print(f"\n  Warnings:")
        for warning in result["warnings"]:
            print(f"    ⚠️ {warning}")
    
    # Should pass validation
    assert result["is_valid"], f"Validation should pass with one source. Errors: {result['errors']}"
    
    print("\n✅ Test 3 PASSED: Validation works with minimum required sources")


def test_validation_with_missing_parameter():
    """Test that validation fails when no source for a parameter is uploaded."""
    print("\n" + "=" * 80)
    print("TEST 4: Validation with Missing Parameter")
    print("=" * 80)
    
    mapping_path = app_dir / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"
    
    # Create mock file object
    class MockFile:
        def __init__(self, name):
            self.name = name
            
        def getvalue(self):
            return b"LocationID,Investigation\nBH01,Test Investigation"
    
    # Test with only location file (no parameter source files)
    files = {
        "location": MockFile("Location Details.csv"),
    }
    
    print("\n📁 Testing validation with:")
    print("  - Location Details.csv (required)")
    print("  - NO parameter source files")
    
    result = validate_csv_files(files, ["strength"], mapping_path)
    
    print(f"\n  Validation result: {'✅ VALID' if result['is_valid'] else '❌ INVALID'}")
    
    if result["errors"]:
        print(f"\n  Errors:")
        for error in result["errors"]:
            print(f"    ❌ {error}")
    
    # Should fail validation
    assert not result["is_valid"], "Validation should fail with no parameter sources"
    assert any("UndrainedShearStrength" in error for error in result["errors"]), \
        "Error message should mention missing UndrainedShearStrength parameter"
    
    print("\n✅ Test 4 PASSED: Validation correctly fails when parameter has no sources")


def test_aline_requirements():
    """Test A-line plot requirements (LiquidLimit and PlasticityIndex)."""
    print("\n" + "=" * 80)
    print("TEST 5: A-line Plot Requirements")
    print("=" * 80)
    
    mapping_path = app_dir / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"
    
    # Get requirements for A-line plot
    param_sources = get_parameter_source_files(mapping_path, ["aline"])
    
    print(f"\n📊 Parameters for 'aline' plot:")
    for param, sources in param_sources.items():
        print(f"\n  Parameter: {param}")
        print(f"  Number of sources: {len(sources)}")
        for idx, source in enumerate(sources, 1):
            print(f"    {idx}. {source['csv_file']} (priority {source['priority_rank']})")
    
    # Both LiquidLimit and PlasticityIndex should come from Classification by Geology.csv
    assert "LiquidLimit" in param_sources
    assert "PlasticityIndex" in param_sources
    
    print("\n✅ Test 5 PASSED: A-line requirements correctly identified")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("🧪 TESTING FLEXIBLE FILE REQUIREMENTS")
    print("=" * 80)
    
    try:
        test_parameter_source_mapping()
        test_all_files_vs_required()
        test_validation_with_one_source()
        test_validation_with_missing_parameter()
        test_aline_requirements()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print("\nSummary:")
        print("  ✅ Parameter source mapping works correctly")
        print("  ✅ File requirements structure is correct")
        print("  ✅ Validation passes with minimum required sources")
        print("  ✅ Validation fails when parameters have no sources")
        print("  ✅ A-line requirements correctly identified")
        print("\n" + "=" * 80)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

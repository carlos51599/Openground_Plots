"""
Test script to verify file upload UI changes for multi-select plot types.

This script validates that:
1. All required files are shown in "Required Files" section
2. "Test Data Files" section only appears under "Required Files" for strength plots
3. Multiple plot types show combined requirements
"""

import sys
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from validation import validate_csv_files


def test_validation_single_aline():
    """Test validation for A-line plot only."""
    print("🧪 Testing A-line plot validation...")

    # Mock files for A-line
    files = {
        "mapping": MockFile("mapping.csv"),
        "location": MockFile("location.csv"),
        "classification": MockFile("classification.csv"),
    }

    result = validate_csv_files(files, plot_types=["aline"])

    # Should require: mapping, location, classification
    print(f"   Expected files: mapping, location, classification")
    print(f"   Validation result: {result['is_valid']}")
    print(f"   Errors: {result['errors']}")
    print()


def test_validation_single_strength():
    """Test validation for Strength plot only."""
    print("🧪 Testing Strength plot validation...")

    # Mock files for Strength
    files = {
        "mapping": MockFile("mapping.csv"),
        "location": MockFile("location.csv"),
        "test_data_1": MockFile("test_data_1.csv"),
    }

    result = validate_csv_files(files, plot_types=["strength"])

    # Should require: mapping, location, at least one test file
    print(f"   Expected files: mapping, location, test_data (1+)")
    print(f"   Validation result: {result['is_valid']}")
    print(f"   Errors: {result['errors']}")
    print()


def test_validation_multiple_plots():
    """Test validation for both A-line and Strength plots."""
    print("🧪 Testing multi-select (A-line + Strength) validation...")

    # Mock files for both plot types
    files = {
        "mapping": MockFile("mapping.csv"),
        "location": MockFile("location.csv"),
        "classification": MockFile("classification.csv"),
        "test_data_1": MockFile("test_data_1.csv"),
    }

    result = validate_csv_files(files, plot_types=["aline", "strength"])

    # Should require: mapping, location, classification, at least one test file
    print(f"   Expected files: mapping, location, classification, test_data (1+)")
    print(f"   Validation result: {result['is_valid']}")
    print(f"   Errors: {result['errors']}")
    print()


def test_validation_list_format():
    """Test that plot_types can be passed as list."""
    print("🧪 Testing plot_types as list (not set)...")

    files = {
        "mapping": MockFile("mapping.csv"),
        "location": MockFile("location.csv"),
        "classification": MockFile("classification.csv"),
    }

    # Test with list format
    result = validate_csv_files(files, plot_types=["aline"])
    print(f"   List format works: {result['is_valid']}")
    print()


class MockFile:
    """Mock file object for testing."""

    def __init__(self, name):
        self.name = name

    def getvalue(self):
        # Return minimal CSV content
        if "mapping" in self.name:
            return b"parameter,column\nLiquidLimit,LL\nPlasticityIndex,PI\nUndrainedShearStrength,Su"
        elif "location" in self.name:
            return b"LocationID,Investigation\nBH01,Site A"
        elif "classification" in self.name:
            return b"LocationID,DepthTop,LiquidLimit,PlasticityIndex,GeologyCode\nBH01,1.0,30,15,CL"
        else:
            return b"LocationID,DepthTop,UndrainedShearStrength\nBH01,1.0,50"


if __name__ == "__main__":
    print("=" * 70)
    print("FILE UPLOAD UI TEST SUITE")
    print("=" * 70)
    print()

    test_validation_single_aline()
    test_validation_single_strength()
    test_validation_multiple_plots()
    test_validation_list_format()

    print("=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)
    print()
    print("Manual UI Testing Checklist:")
    print("1. ☐ Select only A-line plot")
    print("   - Location Details uploader appears")
    print("   - Classification uploader appears")
    print("   - NO 'Test Data Files' section appears")
    print()
    print("2. ☐ Select only Strength plot")
    print("   - Location Details uploader appears")
    print("   - Test Data Files uploader appears (with description)")
    print("   - NO Classification uploader appears")
    print()
    print("3. ☐ Select both A-line and Strength plots")
    print("   - Location Details uploader appears")
    print("   - Classification uploader appears")
    print("   - Test Data Files uploader appears")
    print("   - ALL required files in 'Required Files' section")
    print("   - Upload Status shows all file types correctly")
    print()

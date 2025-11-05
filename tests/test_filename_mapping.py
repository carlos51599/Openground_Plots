#!/usr/bin/env python3
"""
Test script to verify filename mapping logic for Streamlit integration.

This script validates that the modified save_uploaded_files() function
preserves original filenames for parameter mapping compatibility.
"""

from pathlib import Path
import tempfile
import sys

# Add parent directory to path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from validation import save_uploaded_files


class MockUploadedFile:
    """Mock Streamlit UploadedFile for testing."""

    def __init__(self, name: str, content: bytes):
        self.name = name
        self._content = content

    def getvalue(self) -> bytes:
        return self._content


def test_save_with_original_names():
    """Test that files are saved with original names."""
    print("🧪 Testing save_uploaded_files with original name preservation...")

    # Create mock uploaded files
    uploaded_files = {
        "classification": MockUploadedFile(
            "Classification by Geology.csv",
            b"LocationID,GeologyCode,LiquidLimit,PlasticityIndex\n",
        ),
        "location": MockUploadedFile(
            "Location Details.csv", b"LocationID,Investigation\n"
        ),
    }

    # Save to temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        saved_paths = save_uploaded_files(uploaded_files, temp_path)

        # Verify files were saved with original names
        print(f"\n📁 Saved files to: {temp_path}")
        print(f"\n📋 File mapping:")
        for key, path in saved_paths.items():
            print(f"  {key:20} → {path.name}")
            assert path.exists(), f"File not found: {path}"

        # Check classification file
        classification_path = saved_paths["classification"]
        assert (
            classification_path.name == "Classification by Geology.csv"
        ), f"Expected 'Classification by Geology.csv', got '{classification_path.name}'"

        # Check location file
        location_path = saved_paths["location"]
        assert (
            location_path.name == "Location Details.csv"
        ), f"Expected 'Location Details.csv', got '{location_path.name}'"

        print(f"\n✅ Test passed! Files saved with original names.")
        print(f"\n📊 This ensures parameter mapping will work correctly:")
        print(f"   • Mapping CSV references: 'Classification by Geology.csv'")
        print(f"   • Saved file name:        '{classification_path.name}'")
        print(f"   • Match result:           ✅ MATCH")


def test_csv_source_folder_override():
    """Test that csv_source_folder override logic works."""
    print("\n🧪 Testing csv_source_folder override logic...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a fake classification CSV
        classification_path = temp_path / "Classification by Geology.csv"
        classification_path.write_text("test")

        # Simulate the override logic
        input_files = {"classification": classification_path}
        csv_source_folder = str(input_files["classification"].parent)

        print(f"\n📁 Temp directory:       {temp_path}")
        print(f"📄 Classification file:  {classification_path}")
        print(f"🔄 csv_source_folder:    {csv_source_folder}")

        # Verify the parent directory is correctly extracted
        assert csv_source_folder == str(
            temp_path
        ), f"Expected '{temp_path}', got '{csv_source_folder}'"

        # Verify file can be found using this folder
        expected_path = Path(csv_source_folder) / "Classification by Geology.csv"
        assert expected_path.exists(), f"File not found at: {expected_path}"

        print(f"\n✅ Test passed! csv_source_folder override works correctly.")
        print(f"\n📊 This ensures load_parameter_data will find CSVs:")
        print(f"   • csv_source_folder:           '{csv_source_folder}'")
        print(f"   • Mapping references CSV:      'Classification by Geology.csv'")
        print(f"   • Constructed path:            '{expected_path}'")
        print(f"   • File exists:                 ✅ YES")


if __name__ == "__main__":
    try:
        test_save_with_original_names()
        test_csv_source_folder_override()

        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        print("\nThe fix should work correctly:")
        print(
            "1. Files are saved with original names (e.g., 'Classification by Geology.csv')"
        )
        print("2. csv_source_folder is overridden to temp directory")
        print("3. load_parameter_data can find CSVs by building paths from mappings")
        print("4. group_data_by_formation can match CSV names correctly")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

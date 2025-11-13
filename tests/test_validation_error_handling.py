"""
Test script to verify validation error handling for missing columns and corrupted CSVs.
"""

import sys
from pathlib import Path
import pandas as pd
import tempfile

# Add parent directory to path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from validation import get_required_files_from_mapping, get_parameter_source_files


def test_missing_parameter_column():
    """Test that missing 'parameter' column raises clear error."""
    print("\n🧪 Test 1: Missing 'parameter' column")

    # Create test CSV without 'parameter' column
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("csv_file,column_name,priority_rank\n")
        f.write("Test.csv,TestColumn,1\n")
        temp_path = Path(f.name)

    try:
        result = get_parameter_source_files(temp_path, ["aline"])
        print("❌ FAILED - Should have raised ValueError")
    except ValueError as e:
        if "missing required columns" in str(e).lower():
            print(f"✅ PASSED - Got expected error: {e}")
        else:
            print(f"⚠️ PARTIAL - Got ValueError but unexpected message: {e}")
    except Exception as e:
        print(f"❌ FAILED - Got unexpected exception: {type(e).__name__}: {e}")
    finally:
        temp_path.unlink()


def test_missing_csv_file_column():
    """Test that missing 'csv_file' column raises clear error."""
    print("\n🧪 Test 2: Missing 'csv_file' column")

    # Create test CSV without 'csv_file' column
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("parameter,column_name,priority_rank\n")
        f.write("LiquidLimit,TestColumn,1\n")
        temp_path = Path(f.name)

    try:
        result = get_parameter_source_files(temp_path, ["aline"])
        print("❌ FAILED - Should have raised ValueError")
    except ValueError as e:
        if "missing required columns" in str(e).lower():
            print(f"✅ PASSED - Got expected error: {e}")
        else:
            print(f"⚠️ PARTIAL - Got ValueError but unexpected message: {e}")
    except Exception as e:
        print(f"❌ FAILED - Got unexpected exception: {type(e).__name__}: {e}")
    finally:
        temp_path.unlink()


def test_corrupted_csv():
    """Test that corrupted CSV raises clear error."""
    print("\n🧪 Test 3: Corrupted CSV file")

    # Create corrupted CSV
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("parameter,csv_file,priority_rank\n")
        f.write('LiquidLimit,"Test.csv,1\n')  # Unclosed quote
        f.write("PlasticityIndex,Test2.csv\n")  # Wrong number of columns
        temp_path = Path(f.name)

    try:
        result = get_parameter_source_files(temp_path, ["aline"])
        print("⚠️ PARTIAL - Pandas parsed corrupted CSV (may be too lenient)")
    except ValueError as e:
        print(f"✅ PASSED - Got expected error: {e}")
    except Exception as e:
        print(f"⚠️ PARTIAL - Got exception (pandas parsing): {type(e).__name__}: {e}")
    finally:
        temp_path.unlink()


def test_valid_csv():
    """Test that valid CSV works correctly."""
    print("\n🧪 Test 4: Valid CSV file")

    # Create valid test CSV
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("parameter,csv_file,priority_rank\n")
        f.write("LiquidLimit,Classification by Geology.csv,1\n")
        f.write("PlasticityIndex,Classification by Geology.csv,1\n")
        temp_path = Path(f.name)

    try:
        result = get_parameter_source_files(temp_path, ["aline"])

        # Check result structure
        if "LiquidLimit" in result and "PlasticityIndex" in result:
            print(f"✅ PASSED - Got expected parameters: {list(result.keys())}")
            print(f"   LiquidLimit sources: {result['LiquidLimit']}")
        else:
            print(
                f"❌ FAILED - Missing expected parameters. Got: {list(result.keys())}"
            )
    except Exception as e:
        print(f"❌ FAILED - Unexpected exception: {type(e).__name__}: {e}")
    finally:
        temp_path.unlink()


def test_missing_file():
    """Test that missing file raises clear error."""
    print("\n🧪 Test 5: Missing CSV file")

    missing_path = Path("nonexistent_mapping.csv")

    try:
        result = get_parameter_source_files(missing_path, ["aline"])
        print("❌ FAILED - Should have raised FileNotFoundError")
    except FileNotFoundError as e:
        print(f"✅ PASSED - Got expected error: {e}")
    except Exception as e:
        print(f"❌ FAILED - Got unexpected exception: {type(e).__name__}: {e}")


def test_get_required_files_error_propagation():
    """Test that errors propagate correctly through get_required_files_from_mapping."""
    print("\n🧪 Test 6: Error propagation in get_required_files_from_mapping")

    # Create test CSV without 'parameter' column
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("csv_file,column_name\n")
        f.write("Test.csv,TestColumn\n")
        temp_path = Path(f.name)

    try:
        result = get_required_files_from_mapping(temp_path, ["aline"])
        print("❌ FAILED - Should have raised ValueError")
    except ValueError as e:
        if "error processing mapping csv" in str(e).lower():
            print(f"✅ PASSED - Got expected error with context: {e}")
        else:
            print(f"⚠️ PARTIAL - Got ValueError but unexpected message: {e}")
    except Exception as e:
        print(f"❌ FAILED - Got unexpected exception: {type(e).__name__}: {e}")
    finally:
        temp_path.unlink()


if __name__ == "__main__":
    print("=" * 70)
    print("🔬 Validation Error Handling Test Suite")
    print("=" * 70)

    test_missing_parameter_column()
    test_missing_csv_file_column()
    test_corrupted_csv()
    test_valid_csv()
    test_missing_file()
    test_get_required_files_error_propagation()

    print("\n" + "=" * 70)
    print("✅ Test suite completed")
    print("=" * 70)

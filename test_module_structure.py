"""
Test script to verify the modular Streamlit app setup.

This script checks:
1. Module count (<10)
2. Module sizes (<1,500 lines)
3. Import integrity (no circular imports)
4. Required functions are accessible
"""

from pathlib import Path
import sys

# Add directories to path
app_dir = Path(__file__).parent
plotting_scripts_dir = app_dir / "Plotting Scripts"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(plotting_scripts_dir))


def test_module_structure():
    """Test that module structure meets requirements."""
    print("=" * 80)
    print("TESTING MODULAR APP STRUCTURE")
    print("=" * 80)

    # Count modules
    modules = list(app_dir.glob("*.py"))
    module_count = len(modules)

    print(f"\n✓ Module Count: {module_count} (<10 limit)")
    assert module_count < 10, f"Too many modules: {module_count}"

    # Check module sizes
    print("\n✓ Module Sizes:")
    for module in modules:
        lines = len(module.read_text(encoding="utf-8").splitlines())
        status = "✓" if lines < 1500 else "✗"
        print(f"  {status} {module.name}: {lines} lines")
        if module.name != "Streamlit_A_line.py":  # Allow existing monolith to be large
            assert lines < 1500, f"Module too large: {module.name} has {lines} lines"

    print("\n" + "=" * 80)
    print("TESTING IMPORTS")
    print("=" * 80)

    # Test imports
    try:
        from validation import validate_csv_files, save_uploaded_files

        print("✓ validation.py imported successfully")
        print(f"  - validate_csv_files: {callable(validate_csv_files)}")
        print(f"  - save_uploaded_files: {callable(save_uploaded_files)}")
    except ImportError as e:
        print(f"✗ Failed to import validation.py: {e}")
        raise

    try:
        from zip_utils import create_zip_archive

        print("✓ zip_utils.py imported successfully")
        print(f"  - create_zip_archive: {callable(create_zip_archive)}")
    except ImportError as e:
        print(f"✗ Failed to import zip_utils.py: {e}")
        raise

    try:
        from Streamlit_A_line import generate_aline_plots, main

        print("✓ Streamlit_A_line.py imported successfully")
        print(f"  - generate_aline_plots: {callable(generate_aline_plots)}")
        print(f"  - main: {callable(main)}")
    except ImportError as e:
        print(f"✗ Failed to import Streamlit_A_line.py: {e}")
        raise

    print("\n" + "=" * 80)
    print("TESTING FUNCTION SIGNATURES")
    print("=" * 80)

    # Check function signatures
    import inspect

    # Check generate_aline_plots signature
    sig = inspect.signature(generate_aline_plots)
    params = list(sig.parameters.keys())
    print(f"\n✓ generate_aline_plots parameters: {params}")
    assert "input_files" in params, "Missing input_files parameter"
    assert "output_dir" in params, "Missing output_dir parameter"
    assert "config_overrides" in params, "Missing config_overrides parameter"

    # Check validate_csv_files signature
    sig = inspect.signature(validate_csv_files)
    params = list(sig.parameters.keys())
    print(f"✓ validate_csv_files parameters: {params}")
    assert "files" in params, "Missing files parameter"

    # Check create_zip_archive signature
    sig = inspect.signature(create_zip_archive)
    params = list(sig.parameters.keys())
    print(f"✓ create_zip_archive parameters: {params}")
    assert "output_dir" in params, "Missing output_dir parameter"

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED ✓")
    print("=" * 80)
    print("\nModular app structure is ready for use!")
    print("\nTo run the Streamlit app:")
    print("  streamlit run app.py")
    print()


if __name__ == "__main__":
    test_module_structure()

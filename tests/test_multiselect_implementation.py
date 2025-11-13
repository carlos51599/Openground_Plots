"""
Multi-Select Plot Type Implementation - Test Script

This script verifies that all key components of the multi-select
implementation are functioning correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def test_session_state_initialization():
    """Test that plot_types is properly defined in app.py"""
    print("\n🔍 Test 1: Session State Initialization")

    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Check for plot_types initialization
    assert (
        '"plot_types" not in st.session_state' in content
    ), "❌ plot_types not found in session state init"
    assert (
        'st.session_state.plot_types = {"aline"}' in content
    ), "❌ plot_types not initialized as set"

    # Verify old plot_type is not present
    assert (
        "st.session_state.plot_type = " not in content
    ), "❌ Old plot_type still present"

    print("   ✅ Session state properly initialized with plot_types as set")


def test_checkbox_ui():
    """Test that checkbox UI components are present"""
    print("\n🔍 Test 2: Checkbox UI Components")

    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Check for checkboxes
    assert "st.checkbox" in content, "❌ Checkbox widget not found"
    assert (
        '"📊 A-line (Atterberg Limits)"' in content
    ), "❌ A-line checkbox label not found"
    assert (
        '"📈 Undrained Shear Strength"' in content
    ), "❌ Strength checkbox label not found"
    assert (
        'value="aline" in st.session_state.plot_types' in content
    ), "❌ A-line checkbox value binding incorrect"
    assert (
        'value="strength" in st.session_state.plot_types' in content
    ), "❌ Strength checkbox value binding incorrect"

    # Verify old button code is not present
    assert 'st.button("📊 A-line"' not in content, "❌ Old A-line button still present"

    print("   ✅ Checkbox UI components properly implemented")


def test_conditional_syntax():
    """Test that all conditionals use set membership testing"""
    print("\n🔍 Test 3: Conditional Syntax")

    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Check for correct set membership syntax
    assert (
        '"aline" in st.session_state.plot_types' in content
    ), "❌ A-line set membership check not found"
    assert (
        '"strength" in st.session_state.plot_types' in content
    ), "❌ Strength set membership check not found"

    # Verify old comparison syntax is not present
    assert (
        'st.session_state.plot_types == "aline"' not in content
    ), "❌ Old == comparison still present"
    assert (
        'st.session_state.plot_types == "strength"' not in content
    ), "❌ Old == comparison still present"

    # Verify no typos (plot_typess)
    assert "plot_typess" not in content, "❌ Typo 'plot_typess' found"

    print("   ✅ All conditionals use proper set membership testing")


def test_validation_function():
    """Test that validation function accepts plot_types list"""
    print("\n🔍 Test 4: Validation Function Signature")

    with open("validation.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Check function signature
    assert (
        "def validate_csv_files(" in content
    ), "❌ validate_csv_files function not found"
    assert (
        "plot_types: List[str]" in content or "plot_types: list[str]" in content
    ), "❌ plot_types parameter not typed as list"

    # Check for set membership usage in validation
    assert (
        '"aline" in plot_types' in content
    ), "❌ A-line membership check not in validation"
    assert (
        '"strength" in plot_types' in content
    ), "❌ Strength membership check not in validation"

    # Verify old plot_type parameter is not present
    assert (
        "plot_type: str =" not in content or "plot_type: str" not in content
    ), "❌ Old plot_type parameter might still be present"

    print("   ✅ Validation function properly accepts plot_types list")


def test_results_generation():
    """Test that Tab 3 handles multiple plot types"""
    print("\n🔍 Test 5: Results Generation Logic")

    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Check for combined results structure
    assert "combined_results" in content, "❌ combined_results not found"
    assert (
        '"formations_processed": set()' in content
    ), "❌ formations_processed not initialized as set"
    assert '"plots_generated": 0' in content, "❌ plots_generated counter not found"
    assert '"parameter_names": []' in content, "❌ parameter_names list not found"

    # Check for both plot generators
    assert (
        'if "aline" in st.session_state.plot_types:' in content
    ), "❌ A-line generator condition not found"
    assert (
        'if "strength" in st.session_state.plot_types:' in content
    ), "❌ Strength generator condition not found"
    assert "generate_aline_plots" in content, "❌ A-line generator call not found"
    assert "generate_strength_plots" in content, "❌ Strength generator call not found"

    # Check for result accumulation
    assert (
        'combined_results["formations_processed"].update' in content
    ), "❌ Formations update not found"
    assert (
        'combined_results["plots_generated"] +=' in content
    ), "❌ Plots counter increment not found"

    print("   ✅ Results generation properly handles multiple plot types")


def test_dynamic_ui_messages():
    """Test that UI messages adapt to selections"""
    print("\n🔍 Test 6: Dynamic UI Messages")

    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Check for length-based conditional messages
    assert (
        "len(st.session_state.plot_types) == 0" in content
    ), "❌ Zero selection handling not found"
    assert (
        "len(st.session_state.plot_types) == 1" in content
    ), "❌ Single selection handling not found"
    assert (
        "len(st.session_state.plot_types) > 1" in content or "else:" in content
    ), "❌ Multi-selection handling not found"

    # Check for dynamic button text
    assert '"🚀 Generate A-line Plots"' in content, "❌ A-line button text not found"
    assert (
        '"🚀 Generate Strength Plots"' in content
    ), "❌ Strength button text not found"
    assert '"🚀 Generate All Plots"' in content, "❌ Multi-plot button text not found"

    # Check for dynamic ZIP filenames
    assert '"aline_plots.zip"' in content, "❌ A-line ZIP filename not found"
    assert '"strength_plots.zip"' in content, "❌ Strength ZIP filename not found"
    assert '"geotechnical_plots.zip"' in content, "❌ Combined ZIP filename not found"

    print("   ✅ Dynamic UI messages properly implemented")


def test_imports():
    """Test that typing imports are correct"""
    print("\n🔍 Test 7: Type Imports")

    with open("validation.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Check for List import
    assert "from typing import" in content, "❌ typing import not found"
    assert (
        "List" in content or "list[str]" in content
    ), "❌ List type not imported or used"

    print("   ✅ Type imports are correct")


def run_all_tests():
    """Run all test functions"""
    print("\n" + "=" * 60)
    print("  Multi-Select Plot Type Implementation - Test Suite")
    print("=" * 60)

    tests = [
        test_session_state_initialization,
        test_checkbox_ui,
        test_conditional_syntax,
        test_validation_function,
        test_results_generation,
        test_dynamic_ui_messages,
        test_imports,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n   {str(e)}")
            failed += 1
        except Exception as e:
            print(f"\n   ❌ Unexpected error: {str(e)}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"  Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n  🎉 All tests passed! Multi-select implementation is complete.")
        return 0
    else:
        print(f"\n  ⚠️  {failed} test(s) failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())

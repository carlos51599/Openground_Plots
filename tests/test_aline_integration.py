"""Integration test for A-line plot generation."""

import sys
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(app_dir / "Plotting Scripts"))

from Streamlit_A_line import generate_aline_plots


def test_aline_generation():
    """Test A-line plot generation with real data files."""
    print("🧪 Testing A-line plot generation...")

    # Setup input files
    input_files = {
        "mapping": app_dir / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv",
        "location": app_dir / "Location Details.csv",
        "classification": app_dir / "Classification by Geology.csv",
    }

    # Verify all files exist
    for key, path in input_files.items():
        if not path.exists():
            print(f"❌ Missing file: {key} -> {path}")
            return False
        print(f"✅ Found {key}: {path.name}")

    # Create temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)

        print(f"\n📂 Output directory: {output_dir}")
        print("\n🚀 Running A-line plot generation...")

        # Run generation
        try:
            results = generate_aline_plots(
                input_files=input_files,
                output_dir=output_dir,
                config_overrides={
                    "output_control": {
                        "enabled": True,
                        "plots": {
                            "enabled": True,
                            "investigation_series_plots_with_outliers": True,
                            "investigation_series_plots_without_outliers": True,
                            "investigation_series_plots_plotly_with_outliers": False,
                        },
                        "data": {
                            "enabled": False,
                        },
                    },
                },
            )

            print("\n📊 Results:")
            print(f"  Success: {results['success']}")
            print(f"  Plots generated: {results['plots_generated']}")
            print(f"  Formations processed: {len(results['formations_processed'])}")
            print(f"  Parameter: {results['parameter_name']}")

            if results["success"]:
                print("\n✅ Test PASSED!")
                print("\nFormations processed:")
                for formation in results["formations_processed"]:
                    print(f"  • {formation}")
                return True
            else:
                print(f"\n❌ Test FAILED: {results.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"\n❌ Test FAILED with exception: {e}")
            import traceback

            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = test_aline_generation()
    sys.exit(0 if success else 1)

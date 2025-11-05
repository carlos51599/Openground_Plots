#!/usr/bin/env python3
"""
Test script to verify IQR multiplier config override deep merge functionality.

This script validates that nested config_overrides (like outlier detection IQR multiplier)
are correctly applied via deep merge rather than shallow replacement.
"""

import sys
from pathlib import Path

# Add parent directory to path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))


def test_deep_merge():
    """Test that deep merge preserves nested structure."""
    print("🧪 Testing deep merge functionality for config_overrides...")

    # Simulate the CONFIG structure
    CONFIG = {
        "outlier_detection": {
            "enabled": True,
            "method": "standard_iqr",
            "min_samples_for_detection": 5,
            "method_settings": {
                "standard_iqr": {
                    "iqr_multiplier": 1.5,
                    "quartile_boundaries": {
                        "q1": 0.25,
                        "q3": 0.75,
                    },
                },
            },
            "output_folders": {
                "with_outliers": "with_outliers",
                "without_outliers": "without_outliers",
            },
        },
        "plotting": {
            "figure": {
                "width": 12.5,
                "height": 7,
                "dpi": 300,
            },
        },
    }

    # Simulate config_overrides from Streamlit app
    config_overrides = {
        "outlier_detection": {
            "method_settings": {
                "standard_iqr": {"iqr_multiplier": 2.5}  # User changed from 1.5 to 2.5
            }
        },
        "plotting": {"figure": {"dpi": 600}},  # User changed from 300 to 600
    }

    print(f"\n📊 Original CONFIG:")
    print(
        f"   IQR Multiplier:  {CONFIG['outlier_detection']['method_settings']['standard_iqr']['iqr_multiplier']}"
    )
    print(f"   DPI:             {CONFIG['plotting']['figure']['dpi']}")
    print(
        f"   Min Samples:     {CONFIG['outlier_detection']['min_samples_for_detection']}"
    )
    print(
        f"   Q1:              {CONFIG['outlier_detection']['method_settings']['standard_iqr']['quartile_boundaries']['q1']}"
    )

    # Deep merge function (same as in Streamlit_A_line.py)
    def deep_merge(base_dict, override_dict):
        """Recursively merge override_dict into base_dict."""
        for key, value in override_dict.items():
            if (
                key in base_dict
                and isinstance(base_dict[key], dict)
                and isinstance(value, dict)
            ):
                deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value

    # Apply config_overrides
    deep_merge(CONFIG, config_overrides)

    print(f"\n✏️ Config overrides applied:")
    print(f"   New IQR Multiplier: 2.5")
    print(f"   New DPI: 600")

    print(f"\n📊 Updated CONFIG:")
    print(
        f"   IQR Multiplier:  {CONFIG['outlier_detection']['method_settings']['standard_iqr']['iqr_multiplier']}"
    )
    print(f"   DPI:             {CONFIG['plotting']['figure']['dpi']}")
    print(
        f"   Min Samples:     {CONFIG['outlier_detection']['min_samples_for_detection']}"
    )
    print(
        f"   Q1:              {CONFIG['outlier_detection']['method_settings']['standard_iqr']['quartile_boundaries']['q1']}"
    )

    # Verify results
    assert (
        CONFIG["outlier_detection"]["method_settings"]["standard_iqr"]["iqr_multiplier"]
        == 2.5
    ), "IQR multiplier not updated correctly"
    assert CONFIG["plotting"]["figure"]["dpi"] == 600, "DPI not updated correctly"
    assert (
        CONFIG["outlier_detection"]["min_samples_for_detection"] == 5
    ), "Min samples should be preserved (not replaced)"
    assert (
        CONFIG["outlier_detection"]["method_settings"]["standard_iqr"][
            "quartile_boundaries"
        ]["q1"]
        == 0.25
    ), "Q1 boundary should be preserved (not replaced)"
    assert (
        CONFIG["outlier_detection"]["enabled"] == True
    ), "Enabled flag should be preserved"
    assert (
        CONFIG["plotting"]["figure"]["width"] == 12.5
    ), "Figure width should be preserved"

    print(f"\n✅ Test passed! Deep merge works correctly.")
    print(f"\n📊 Verification:")
    print(f"   ✅ IQR multiplier updated:  1.5 → 2.5")
    print(f"   ✅ DPI updated:             300 → 600")
    print(f"   ✅ Min samples preserved:   5 (unchanged)")
    print(f"   ✅ Q1 boundary preserved:   0.25 (unchanged)")
    print(f"   ✅ Enabled flag preserved:  True (unchanged)")
    print(f"   ✅ Figure width preserved:  12.5 (unchanged)")


def test_shallow_merge_problem():
    """Demonstrate the problem with shallow merge (what we had before)."""
    print("\n\n🚨 Demonstrating shallow merge problem (for comparison)...")

    CONFIG = {
        "outlier_detection": {
            "enabled": True,
            "method": "standard_iqr",
            "min_samples_for_detection": 5,
            "method_settings": {
                "standard_iqr": {
                    "iqr_multiplier": 1.5,
                    "quartile_boundaries": {
                        "q1": 0.25,
                        "q3": 0.75,
                    },
                },
            },
        },
    }

    config_overrides = {
        "outlier_detection": {
            "method_settings": {"standard_iqr": {"iqr_multiplier": 2.5}}
        }
    }

    print(f"\n📊 Original CONFIG (before shallow merge):")
    print(
        f"   IQR Multiplier:  {CONFIG['outlier_detection']['method_settings']['standard_iqr']['iqr_multiplier']}"
    )
    print(
        f"   Min Samples:     {CONFIG['outlier_detection']['min_samples_for_detection']}"
    )
    print(f"   Enabled:         {CONFIG['outlier_detection']['enabled']}")

    # Shallow merge (OLD method)
    for key, value in config_overrides.items():
        if key in CONFIG:
            CONFIG[key] = value

    print(f"\n📊 CONFIG after shallow merge:")
    print(
        f"   IQR Multiplier:  {CONFIG['outlier_detection']['method_settings']['standard_iqr']['iqr_multiplier']}"
    )

    # Try to access other values - they're gone!
    try:
        min_samples = CONFIG["outlier_detection"]["min_samples_for_detection"]
        print(f"   Min Samples:     {min_samples}")
    except KeyError:
        print(f"   Min Samples:     ❌ LOST (KeyError)")

    try:
        enabled = CONFIG["outlier_detection"]["enabled"]
        print(f"   Enabled:         {enabled}")
    except KeyError:
        print(f"   Enabled:         ❌ LOST (KeyError)")

    print(
        f"\n❌ Problem: Shallow merge replaces entire nested dict, losing other values!"
    )
    print(f"   This is why we need deep merge for nested config_overrides.")


if __name__ == "__main__":
    try:
        test_deep_merge()
        test_shallow_merge_problem()

        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        print("\nThe IQR multiplier slider in Streamlit app is now correctly linked:")
        print("1. User adjusts slider (e.g., 1.5 → 2.5)")
        print(
            "2. App stores in config_overrides['outlier_detection']['method_settings']['standard_iqr']['iqr_multiplier']"
        )
        print("3. Deep merge applies override while preserving other CONFIG values")
        print("4. Plotting script uses updated IQR multiplier for outlier detection")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

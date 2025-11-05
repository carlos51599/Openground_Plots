#!/usr/bin/env python3
"""
Multi-Source Parameter Plotting System - Moisture Content vs Depth
AI-Optimized Monolith Implementation - All Phases Complete

LEGEND COUNT FEATURE (2025-10-31):
Added data point counts to legend entries in HTML interactive plots.
Each investigation in the legend now displays as "Investigation Name (n=x)"
where x is the total number of data points for that investigation across
all test types and formations. This provides immediate visibility into
sample size for each investigation.

IMPLEMENTATION:
- Line ~3067: Calculate investigation_counts dictionary
- Line ~3184: Add count to regular trace legend names
- Line ~3267: Add count to dummy circle trace legend names

CRITICAL PLOTLY LEGEND FIX (2025-10-29):
Previously, the Plotly HTML interactive plots had `groupclick="toggleitem"` in the legend
configuration, which only toggled individual traces (single marker types). This defeated
the purpose of investigation-based legendgroup organization.

ROOT CAUSE: Plotly's groupclick parameter controls legend behavior:
- "toggleitem" (old, incorrect): Toggles only the clicked trace
- "togglegroup" (new, correct): Toggles ALL traces in the same legendgroup

FIX LOCATION: Line ~2923 in generate_investigation_series_plot_plotly()
Changed: groupclick="toggleitem"
To:      groupclick="togglegroup"

RESULT: Clicking a legend entry now toggles ALL points of that investigation color,
regardless of marker shape (test type). This makes the investigation-based color
scheme functional in the interactive HTML plots.

Architectural Overview:

Responsibility:
Generates moisture content vs depth scatter plots by consolidating data from multiple CSV sources
(test types) for geotechnical parameters. The system is configurable and parameter-agnostic,
automatically identifying and combining all relevant test types for any parameter defined in
the global parameter mapping CSV. Creates investigation-series plots that color by
investigation while using marker shapes for test types.

Key Interactions:
- Input: Global parameter mapping CSV + geological data CSVs + Location Details CSV
- Configuration: Parameter selection, color schemes, geological mappings (reused from v27)
- Processing: Mapping extraction → CSV loading → formation grouping → outlier filtering
  → investigation-series plot generation (colors by investigation, shapes by test type) →
  investigation tracking (CSV summaries) → Excel export with highlighted outliers
- Output: Investigation-series scatter plots + investigation CSV summaries + Excel exports
  in Output/[Parameter_Name]/investigation_series/ and Output/[Parameter_Name]/data/
- Output Control: Three-level hierarchy (Master → Category → Individual) for selective output

Navigation Guide:
Data flows: Parameter mapping extraction (PHASE 1) → CSV data loading (PHASE 2) →
Formation grouping (PHASE 3) → Outlier filtering (PHASE 3b) →
Investigation-series plots (PHASE 4) → Investigation tracking (PHASE 5) →
Excel export with highlighted outliers (PHASE 6)
Section markers (# ═════) delineate logical processing blocks for easy AI navigation
Use VS Code outline (Ctrl+Shift+O) to jump between functions

OUTPUT CONTROL ARCHITECTURE:

Three-Level Hierarchy System:
1. Master Toggle: CONFIG["output_control"]["enabled"] - disables ALL output if False
2. Category Toggles: ["plots"]["enabled"] or ["data"]["enabled"] - disable categories
3. Individual Toggles: Specific plot types (investigation_series_plots_with_outliers,
   investigation_series_plots_without_outliers) and data exports (investigation_summary_csv,
   excel_with_highlighted_outliers)

All three levels must be True for output to be generated.

Output Types Controlled:
- Plots: investigation_series_plots_with_outliers, investigation_series_plots_without_outliers
- Data: investigation_summary_csv, excel_with_highlighted_outliers

Helper Functions:
- should_generate_output(master, category, item): Core logic for three-level checks
- should_generate_plot(plot_name): Convenience wrapper for plot outputs
- should_generate_data_export(export_name): Convenience wrapper for data exports

Integration Points:
- Phase 4 investigation-series: New plot type with investigation-based coloring
- Phase 5 CSV export: Wraps export_investigation_csv() calls
- Phase 6 Excel export: Wraps export_highlighted_excel() calls

CONFIGURATION ARCHITECTURE:

Single source of truth: All configuration consolidated in CONFIG dictionary
- Coordination boundaries: Orchestrator functions extract config values
- Primitive injection: Business logic functions accept explicit typed parameters
- Zero hidden dependencies: All function behavior predictable from signatures
- Full testability: Functions accept simple primitives, no config mocking required

Implementation Status:
- Phase 1: Parameter Mapping Extraction ✅
- Phase 2: CSV Data Loading ✅
- Phase 3: Formation Grouping ✅
- Phase 3b: Outlier Filtering ✅
- Phase 4: Investigation Series Plot Generation ✅
- Phase 5: Investigation Source Tracking ✅
- Phase 6: Excel Export with Highlighted Outliers ✅
- Output Control System ✅

Phase 2 Implementation Details:
- Reused v27's complete data loading architecture (load_csv_data)
- Formation splitting applied automatically (weathered/unweathered for GF/KC)
- RTD sub-formation classification (RTD_1, RTD_2, RTD_3)
- Location filtering (BP/CCT exclusions)
- Column standardization (Location ID, Top Depth, Geological_Strata)
- Empirical calculations (SPT N-value to cu conversion with formation-specific f1 factors)

Phase 3 Implementation Details:
- Groups data by geological formation for separate plots
- Maps parameter columns from parameter_mappings to each CSV
- Validates required columns (Geological_Strata, Top Depth, parameter)
- Filters null values from parameter data and depth values
- Returns nested dict: {formation_name: {csv_name: dataframe}}

Phase 3b Implementation Details:
- Lightweight outlier filtering without plot generation
- Uses same IQR method as deleted formation plot functions
- Adds 'is_outlier' column to each formation's dataframes
- Required for investigation-series plots to filter outliers correctly

Phase 4 Implementation Details:
- Generates plots with investigation-based coloring and test-type marker shapes
- Uses _add_investigation_column() logic to map Location IDs to investigations
- Color palette rotates through CONFIG["investigation_series"]["investigation_colors"]
- Marker shapes inherited from CONFIG["csv_source_settings"] per test type
- Dual legend: investigation colors + test type shapes
- Creates both with-outliers and without-outliers versions
- Publication-quality scatter plots (300 DPI, 4:5 aspect ratio)
- X-axis at top (parameter values), Y-axis inverted (depth increases downward)
- Output: {output_folder}/{parameter_name}/investigation_series/{with/without_outliers}/{formation_name}.png
- Configurable via CONFIG["investigation_series"]["enabled"]

Phase 5 Implementation Details:
- Generates investigation source tracking CSV summaries
- Tracks data count per investigation-formation-CSV combination
- Creates TWO CSV versions: with outliers and without outliers
- Output controlled via CONFIG["output_control"]["data"]["investigation_summary_csv"]

Phase 6 Implementation Details:
- Exports source CSV data as Excel spreadsheets with outlier highlighting
- Creates ONE Excel file per test type (CSV source) containing ALL formations
- Outlier rows highlighted in red for easy visual identification
- Uses same outlier detection logic as plotting (standard IQR method)
- Preserves all columns from source CSVs for complete data context
- Auto-adjusts column widths and freezes header row for navigation
- Organizes by test type: {test_type}.xlsx (e.g., SPT.xlsx, CPT.xlsx, Samples.xlsx)
- Output: {output_folder}/{parameter_name}/data/excel_highlighted/
- Configurable via CONFIG["output_control"]["data"]["excel_with_highlighted_outliers"]
"""

# UTF-8 Configuration for Windows
import sys
import os

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

# Standard library imports
import logging
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Optional, Tuple

# Third-party imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from scipy import odr
from sklearn.decomposition import PCA
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows

# ═══════════════════════════════════════════════════════════════════════════
# 🏗️ INITIALIZATION & CONFIGURATION SECTION
# ═══════════════════════════════════════════════════════════════════════════

# Logging Configuration with UTF-8 encoding
# Force UTF-8 for stdout to handle emoji characters on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# MODIFICATION POINT: Navigation Constants for AI Assistance
NAV_CONSTANTS = {
    "sections": {
        "INIT": "🏗️ INITIALIZATION & CONFIGURATION SECTION",
        "PHASE1": "📊 PHASE 1: PARAMETER MAPPING EXTRACTION",
        "PHASE2": "💾 PHASE 2: CSV DATA LOADING",
        "PHASE3": "🔄 PHASE 3: FORMATION GROUPING",
        "PHASE3b": "🧹 PHASE 3b: OUTLIER FILTERING",
        "PHASE4": "🎨 PHASE 4: INVESTIGATION SERIES PLOT GENERATION",
        "PHASE5": "📋 PHASE 5: INVESTIGATION SOURCE TRACKING",
        "PHASE6": "📊 PHASE 6: EXCEL EXPORT WITH HIGHLIGHTED OUTLIERS",
        "MAIN": "⚡ MAIN EXECUTION SECTION",
    },
    "orchestrators": [
        "extract_parameter_mappings",
        "load_parameter_data",
        "group_data_by_formation",
        "filter_outliers_from_formations",
        "generate_investigation_series_plots",
        "generate_investigation_summary",
        "generate_excel_exports",
    ],
}

# MODIFICATION POINT: Consolidated Configuration Dictionary
# Single source of truth for all configuration settings
CONFIG = {
    # ═══════════════════════════════════════════════════════════════════════
    # OUTPUT CONTROL CONFIGURATION
    # Three-level hierarchy: Master → Category → Individual
    # ═══════════════════════════════════════════════════════════════════════
    "output_control": {
        "enabled": True,  # MODIFICATION POINT: Master toggle - disables ALL output if False
        "plots": {
            "enabled": True,  # MODIFICATION POINT: Plots category toggle
            # Individual plot type toggles
            "investigation_series_plots_with_outliers": False,  # Investigation-series plots (with_outliers folder)
            "investigation_series_plots_without_outliers": False,  # Investigation-series plots (without_outliers folder)
            "investigation_series_plots_manually_identified": False,  # Investigation-series plots (manually_identified_excluded folder)
            "investigation_series_plots_plotly_with_outliers": True,  # Plotly HTML interactive plots (with_outliers folder only)
        },
        "data": {
            "enabled": True,  # MODIFICATION POINT: Data exports category toggle
            # Individual data export toggles
            "investigation_summary_csv": False,  # Investigation source tracking CSV
            "excel_with_highlighted_outliers": False,  # Excel export with red highlighting for outliers
        },
    },
    # ═══════════════════════════════════════════════════════════════════════
    # PARAMETER CONFIGURATION - User Modification Point
    # ═══════════════════════════════════════════════════════════════════════
    "parameter": {
        "name": "MoistureContent",  # MODIFICATION POINT: Change to any parameter
        "display_name": "Moisture Content (%)",  # For axis labels
        "mapping_csv": "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv",
        "csv_source_folder": "Openground CSVs",
        "output_base_folder": "Output",
    },
    # ═══════════════════════════════════════════════════════════════════════
    # GEOLOGICAL MAPPINGS CONFIGURATION (Reused from v27)
    # ═══════════════════════════════════════════════════════════════════════
    "mappings": {
        "geology_code_descriptions": {
            "KC": "Kimmeridge Clay Formation",
            "GF": "Gault Clay Formation",
            "LG": "Lower Greensand Formation",
            "RTD": "River Terrace Deposits",
            "HD": "Head Deposits",
            "AMKC": "Ampthill Clay Formation and Kimmeridge Clay Formation",
            "AC": "Ampthill Clay Formation",
            "AL": "Alluvium",
            "CG": "Corallian Group",
            "MG": "Made Ground",
            "TS": "Topsoil",
            # Formation splitting enhancement - weathered/unweathered variants
            "GF_W": "Gault Clay Formation (Weathered)",
            "GF_UW": "Gault Clay Formation (Unweathered)",
            "KC_W": "Kimmeridge Clay Formation (Weathered)",
            "KC_UW": "Kimmeridge Clay Formation (Unweathered)",
            # RTD sub-formations
            "RTD_1": "River Terrace Deposits (Northmoor)",
            "RTD_2": "River Terrace Deposits (Summertown-Radley)",
            "RTD_3": "River Terrace Deposits (Wolvercote)",
            "RTD_Undefined": "River Terrace Deposits (Undefined Classification)",
        },
        "formation_splitting": {
            "enabled": True,
            "target_formations": ["GF", "KC"],
            "weathering_classification": {
                "weathered_suffix": "_W",
                "unweathered_suffix": "_UW",
                "fallback_classification": "undefined",
            },
            "rtd_classification": {
                "enabled": True,
                "target_formations": ["RTD"],
                "mapping": {
                    "RTD_1": "rtd_1",
                    "RTD_2": "rtd_2",
                    "RTD_3": "rtd_3",
                    "Superficial Deposits": "undefined",
                    "Soliflucted": "undefined",
                },
                "fallback_classification": "undefined",
            },
        },
        "column_variations": {
            "location_id": [
                "LocationID",
                "Location ID",
            ],
            "geology_code": [
                "GeologyCode",
                "Geology Code",
            ],
            "geology_code_description": [
                "GeologyCodeDescription",
                "Geology Code Description",
            ],
            "geology_code2": [
                "GeologyCode2",
                "Geology Code2",
                "Geology Code 2",
            ],
            "geology_code2_description": [
                "GeologyCode2Description",
                "Geology Code2 Description",
                "Geology Code 2 Description",
            ],
            "top_depth": [
                "DepthTop",
                "SampleTop",
                "Test Depth",
                "SPT Top Depth",
                "Ground Water Strike",
                "Top Depth",
                "ResponseZoneTop",
                "Depth Top",
            ],
        },
    },
    # ═══════════════════════════════════════════════════════════════════════
    # FILTERING CONFIGURATION (Reused from v27)
    # ═══════════════════════════════════════════════════════════════════════
    "filtering": {
        "location_filter": {
            "enabled": True,
            "exclude_prefixes": ["BP", "CCT"],
            "case_sensitive": False,
        },
    },
    # ═══════════════════════════════════════════════════════════════════════
    # OUTLIER DETECTION CONFIGURATION (Reused from v27)
    # ═══════════════════════════════════════════════════════════════════════
    "outlier_detection": {
        "enabled": True,
        "method": "standard_iqr",  # Using standard IQR for plotting
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
    # ═══════════════════════════════════════════════════════════════════════
    # MANUAL OUTLIER EXCLUSION CONFIGURATION (Phase 3c)
    # Controls manual outlier identification from Excel spreadsheet
    # ═══════════════════════════════════════════════════════════════════════
    "manual_outlier_exclusion": {
        "enabled": True,  # MODIFICATION POINT: Enable/disable manual outlier exclusion
        "excel_file": "Identified Outliers.xlsx",  # Excel file with manually identified outliers
        "sheets": {
            # Maps parameter name to sheet name in Excel file
            "MoistureContent": "MCvsDeph",  # Note: Sheet has typo in original Excel file
        },
        "match_tolerance": {
            # Tolerance for matching parameter and depth values (floating-point comparison)
            "parameter": 1e-5,  # Tolerance for matching parameter value (x-coordinate)
            "depth": 1e-5,  # Tolerance for matching depth value (y-coordinate)
        },
        "output_folder": "manually_identified_excluded",  # Subfolder name for plots with manual outliers excluded
    },
    # ═══════════════════════════════════════════════════════════════════════
    # PLOTTING CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════
    "plotting": {
        "figure": {
            "width": 8.67,  # Increased by 1/12 (8 * 13/12 = 8.67) for wider plot area
            "height": 12,  # 2:3 aspect ratio (taller than wider) - matches UndrainedShearStrength_v7.py
            "dpi": 300,
        },
        "colors": {
            # One color per CSV source - simple rotation through color palette
            # Matches the style from triaxial_total_stress_vs_depth_by_formation.py
            "csv_source_colors": [
                "#0057B7",  # Blue
                "#006400",  # Dark Green
                "#8B0000",  # Dark Red
                "#4B0082",  # Indigo
                "#FF8C00",  # Dark Orange
                "#2E8B57",  # Sea Green
                "#8A2BE2",  # Blue Violet
                "#DC143C",  # Crimson
                "#1E90FF",  # Dodger Blue
                "#228B22",  # Forest Green
            ],
        },
        "axes": {
            # Matches exact formatting from triaxial_total_stress_vs_depth_by_formation.py
            "x_label_position": "top",
            "x_label_size": 14,
            "x_label_weight": "normal",  # Options: 'normal', 'bold', 'light', 'heavy'
            "y_label": "Depth (m)",
            "y_label_size": 14,
            "y_label_weight": "normal",  # Options: 'normal', 'bold', 'light', 'heavy'
            "x_limit_left": 0,  # X-axis starts at 0
            "y_margin": 1,  # Add 1m margin to max depth
            "invert_y": True,  # Depth increases downward
            "grid": True,
            "grid_which": "both",
            "grid_style": "-",
            "grid_width": 0.5,
            "grid_color": "gray",
            "grid_alpha": 0.3,  # Grid transparency
        },
        "legend": {
            "location": "upper center",  # Position at top center
            "bbox_to_anchor": (
                0.5,
                -0.05,
            ),  # Position below plot (centered horizontally, below y=0)
            "ncol": 3,  # Number of columns for horizontal layout
            "edgecolor": "black",
            "framealpha": 0.9,  # Legend background transparency
            "fixed_width": True,  # Match legend box width to plot area width (absolute equality)
        },
        "save": {
            "bbox_inches": "tight",
        },
    },
    # ═══════════════════════════════════════════════════════════════════════
    # PER-SOURCE PLOTTING SETTINGS
    # MODIFICATION POINT: Configure individual test type appearance
    # Marker types matched to UndrainedShearStrength_v8.py where applicable
    # ═══════════════════════════════════════════════════════════════════════
    "csv_source_settings": {
        # Samples by Geology
        "Samples by Geology.csv": {
            "plotted": True,
            "order": 1,
            "plot_points": True,
            "marker": "o",  # Circle
            "marker_size": 50,
            "alpha": 1,  # Full opacity (matching UndrainedShearStrength)
            "legend_name_points": "Samples",
        },
        # SPT by Geology - Matches UndrainedShearStrength_v8.py
        "SPT by Geology.csv": {
            "plotted": True,
            "order": 2,
            "plot_points": True,
            "marker": "x",  # X marker (matches UndrainedShearStrength)
            "marker_size": 55,  # Matches UndrainedShearStrength
            "marker_thickness": 2,  # Line thickness for 'x' marker (matches UndrainedShearStrength)
            "alpha": 1,  # Full opacity (matching UndrainedShearStrength)
            "legend_name_points": "SPT",
        },
        # CPT by Geology - Matches UndrainedShearStrength_v8.py
        "CPT by Geology.csv": {
            "plotted": True,
            "order": 3,
            "plot_points": True,
            "marker": "s",  # Square marker (matches UndrainedShearStrength)
            "marker_size": 40,  # Matches UndrainedShearStrength
            "alpha": 1,  # Full opacity (matching UndrainedShearStrength)
            "legend_name_points": "CPT",
        },
        # Triaxial Total Stress by Geology - Matches UndrainedShearStrength_v8.py
        "Triaxial Total Stress by Geology.csv": {
            "plotted": True,
            "order": 4,
            "plot_points": True,
            "marker": "D",  # Diamond marker (matches UndrainedShearStrength)
            "marker_size": 65,  # Matches UndrainedShearStrength
            "alpha": 1,  # Full opacity (matching UndrainedShearStrength)
            "legend_name_points": "Triaxial Total Stress",
        },
        # Triaxial Effective Stress by Geology
        "Triaxial Effective Stress by Geology.csv": {
            "plotted": True,
            "order": 5,
            "plot_points": True,
            "marker": "v",  # Triangle-down
            "marker_size": 55,
            "alpha": 1,  # Full opacity (matching UndrainedShearStrength)
            "legend_name_points": "Triaxial Effective Stress",
        },
        # Shear Box by Geology
        "Shear Box by Geology.csv": {
            "plotted": True,
            "order": 6,
            "plot_points": True,
            "marker": "p",  # Pentagon
            "marker_size": 60,
            "alpha": 1,  # Full opacity (matching UndrainedShearStrength)
            "legend_name_points": "Shear Box",
        },
        # Vane Tests by Geology
        "Vane Tests by Geology.csv": {
            "plotted": True,
            "order": 7,
            "plot_points": True,
            "marker": "*",  # Star
            "marker_size": 70,
            "alpha": 1,  # Full opacity (matching UndrainedShearStrength)
            "legend_name_points": "Vane Tests",
        },
        # Classification by Geology
        "Classification by Geology.csv": {
            "plotted": True,
            "order": 8,
            "plot_points": True,
            "marker": "^",  # Triangle-up (changed from 'x' to avoid duplicate with SPT)
            "marker_size": 60,
            "alpha": 1,  # Full opacity (matching UndrainedShearStrength)
            "legend_name_points": "Classification",
        },
        # Consolidation by Geology
        "Consolidation by Geology.csv": {
            "plotted": True,
            "order": 9,
            "plot_points": True,
            "marker": "+",  # Plus
            "marker_size": 60,
            "marker_thickness": 2,  # Line thickness for '+' marker
            "alpha": 1,  # Full opacity (matching UndrainedShearStrength)
            "legend_name_points": "Consolidation",
        },
        # Compaction by Geology
        "Compaction by Geology.csv": {
            "plotted": True,
            "order": 10,
            "plot_points": True,
            "marker": "h",  # Hexagon
            "marker_size": 60,
            "alpha": 1,  # Full opacity (matching UndrainedShearStrength)
            "legend_name_points": "Compaction",
        },
    },
    # ═══════════════════════════════════════════════════════════════════════
    # DEFAULT SOURCE SETTINGS - Fallback for Unmapped CSV Sources
    # ═══════════════════════════════════════════════════════════════════════
    "default_source_settings": {
        "plotted": True,
        "plot_points": True,
        "marker": "o",  # Circle
        "marker_size": 50,
        "alpha": 0.7,
        "legend_name_points": None,
    },
    # ═══════════════════════════════════════════════════════════════════════
    # INVESTIGATION SERIES CONFIGURATION
    # Controls investigation-based coloring with test-type shapes
    # ═══════════════════════════════════════════════════════════════════════
    "investigation_series": {
        "enabled": True,  # MODIFICATION POINT: Enable/disable investigation-series plots
        "output_folder": "investigation_series",  # Subfolder name for investigation-series plots
        # Color palette for investigations (rotates through if more investigations than colors)
        # Professional color palette with high distinguishability
        "investigation_colors": [
            "#0070C0",  # Blue
            "#444444",  # Dark Gray
            "#596A19",  # Olive
            "#7CAE00",  # Lime Green
            "#B29800",  # Gold
            "#9F2F4E",  # Maroon
            "#D55E00",  # Orange
            "#8400CD",  # Purple
            "#C70077",  # Magenta
            "#E11A82",  # Pink
            "#FFD300",  # Yellow
            "#00BFC4",  # Cyan
            "#C0B3D3",  # Lavender
        ],
        # Legend configuration specific to investigation-series plots
        "legend": {
            "show_investigation_colors": True,  # Show color legend for investigations
            "show_test_type_shapes": True,  # Show shape legend for test types
            "investigation_label_prefix": "",  # Prefix for investigation labels (e.g., "Site: ")
            "test_type_label_prefix": "",  # Prefix for test type labels (e.g., "Test: ")
            "force_circle_markers": True,  # MODIFICATION POINT: If True, forces legend markers to display as circles (actual plot markers remain unchanged)
        },
    },
    # ═══════════════════════════════════════════════════════════════════════
    # INVESTIGATION TRACKING CONFIGURATION (Phase 5)
    # Controls investigation source tracking CSV export
    # ═══════════════════════════════════════════════════════════════════════
    "investigation_tracking": {
        "enabled": True,  # MODIFICATION POINT: Enable/disable Phase 5 investigation tracking
        "location_details_csv": "Location Details.csv",  # CSV file with Location ID -> Investigation mapping
        "per_investigation_plots": {
            "fallback_investigation_name": "Unknown",  # Default name for missing/unmatched Location IDs
            "location_id_column_variants": [
                "LocationID",
                "Location ID",
            ],  # Possible Location ID column names
            "investigation_column_variants": [
                "Investigation",
            ],  # Possible Investigation column names
        },
        "output": {
            "data_folder_name": "data",  # Subfolder for data exports (within parameter output folder)
        },
        "output_columns": [
            "Formation",
            "Test Type",
            "Investigation",
            "Value Count",
        ],  # Column order for CSV export
    },
    # ═══════════════════════════════════════════════════════════════════════
    # EXCEL EXPORT CONFIGURATION (Phase 6)
    # Controls Excel export with outlier highlighting
    # ═══════════════════════════════════════════════════════════════════════
    "excel_export": {
        "enabled": True,  # MODIFICATION POINT: Enable/disable Phase 6 Excel export
        "output_folder": "excel_highlighted",  # Subfolder name within data folder
        "highlight_color": "FFFF0000",  # ARGB format (red highlighting for outliers)
        "freeze_header": True,  # Freeze first row for easier navigation
    },
    # ═══════════════════════════════════════════════════════════════════════
    # MARKERS CONFIGURATION (for investigation-series plots)
    # ═══════════════════════════════════════════════════════════════════════
    "markers": {
        "edgecolors": "black",
        "linewidths": 0.3,
    },
    # ═══════════════════════════════════════════════════════════════════════
    # AXES CONFIGURATION (enhanced for investigation-series plots)
    # ═══════════════════════════════════════════════════════════════════════
    "axes": {
        # Matches exact formatting from triaxial_total_stress_vs_depth_by_formation.py
        "x_label_position": "top",
        "x_label_size": 14,
        "x_label_weight": "normal",  # Options: 'normal', 'bold', 'light', 'heavy'
        "y_label": "Depth (m)",
        "y_label_size": 14,
        "y_label_weight": "normal",  # Options: 'normal', 'bold', 'light', 'heavy'
        "x_limit_left": 0,  # X-axis starts at 0
        "y_margin": 1,  # Add 1m margin to max depth
        "invert_y": True,  # Depth increases downward
        "grid": True,
        "grid_which": "both",
        "grid_style": "-",
        "grid_width": 0.5,
        "grid_color": "gray",
        "grid_alpha": 0.3,  # Grid transparency
    },
    # ═══════════════════════════════════════════════════════════════════════
    # LEGEND CONFIGURATION (for investigation-series plots)
    # ═══════════════════════════════════════════════════════════════════════
    "legend": {
        "location": "upper center",  # Position at top center
        "bbox_to_anchor": (
            0.5,
            -0.05,
        ),  # Position below plot (centered horizontally, below y=0)
        "ncol": 3,  # Number of columns for horizontal layout
        "edgecolor": "black",
        "framealpha": 0.9,  # Legend background transparency
        "fixed_width": True,  # Match legend box width to plot area width (absolute equality)
    },
    # ═══════════════════════════════════════════════════════════════════════
    # PLOT TITLE CONFIGURATION (for investigation-series plots)
    # ═══════════════════════════════════════════════════════════════════════
    "plot_title": {
        "enabled": True,  # MODIFICATION POINT: Set to True to show plot title
        "font_size": 16,
        "font_weight": "bold",
        "font_family": "Arial",
        "pad": 20,  # Spacing between title and plot area (matplotlib)
    },
    # ═══════════════════════════════════════════════════════════════════════
    # SAVE CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════
    "save": {
        "bbox_inches": "tight",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# 🔍 OUTLIER DETECTION FUNCTIONS (Reused from v27)
# ═══════════════════════════════════════════════════════════════════════════


def detect_outliers_standard_iqr(
    values_clean: pd.Series, method_settings: Dict[str, Any]
) -> Tuple[pd.Series, pd.Series, float, float]:
    """
    Detect outliers using the standard Tukey boxplot method.

    Based on: Tukey (1977) "Exploratory Data Analysis"
    Implementation: Outliers beyond Q1 - 1.5*IQR and Q3 + 1.5*IQR

    Args:
        values_clean: Clean numerical data (no NaNs)
        method_settings: Method-specific configuration settings

    Returns:
        tuple[pd.Series, pd.Series, float, float]:
            - mild_outliers: pandas Series of outlier values
            - extreme_outliers: pandas Series (empty for standard IQR method)
            - lower_bound: float, the calculated lower fence
            - upper_bound: float, the calculated upper fence
    """
    # Validate data
    if values_clean.empty or values_clean.isna().all():
        empty_series = pd.Series([], dtype=float)
        return empty_series, empty_series, float("nan"), float("nan")

    # Get method-specific settings
    iqr_multiplier = method_settings.get("iqr_multiplier", 1.5)
    quartile_settings = method_settings.get(
        "quartile_boundaries", {"q1": 0.25, "q3": 0.75}
    )

    # Calculate quartiles
    q1 = values_clean.quantile(quartile_settings["q1"])
    q3 = values_clean.quantile(quartile_settings["q3"])
    iqr = q3 - q1

    # Handle constant data (zero IQR)
    if iqr == 0:
        logger.debug(
            f"Zero IQR detected for dataset with {len(values_clean)} values - no outliers identified"
        )
        empty_series = pd.Series([], dtype=float)
        return empty_series, empty_series, float("nan"), float("nan")

    # Calculate fences
    lower_fence = q1 - iqr_multiplier * iqr
    upper_fence = q3 + iqr_multiplier * iqr

    # Identify outliers
    outlier_mask = (values_clean < lower_fence) | (values_clean > upper_fence)
    outliers = values_clean[outlier_mask]

    logger.debug(
        f"Standard IQR outlier detection: {len(outliers)} outliers from {len(values_clean)} samples "
        f"(bounds: [{lower_fence:.3f}, {upper_fence:.3f}])"
    )

    return (
        outliers,
        pd.Series([], dtype=float),  # No extreme outliers in standard method
        float(lower_fence),
        float(upper_fence),
    )


def detect_outliers_per_csv(
    csv_dict: Dict[str, pd.DataFrame],
    parameter_mappings: pd.DataFrame,
    formation_name: str,
    outlier_config: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """
    Detect outliers per test type (CSV) within a formation.

    Args:
        csv_dict: Dictionary of {csv_name: dataframe} for one formation
        parameter_mappings: Parameter mapping dataframe
        formation_name: Name of the formation being processed
        outlier_config: Outlier detection configuration

    Returns:
        dict: {csv_name: {"outlier_indices": set, "outlier_count": int, "total_samples": int}}
    """
    outlier_results = {}

    if not outlier_config["enabled"]:
        logger.info(f"📊 Outlier detection disabled for {formation_name}")
        return outlier_results

    logger.info(f"🔍 Detecting outliers per test type for {formation_name}...")

    for csv_name, df in csv_dict.items():
        # Find parameter column for this CSV
        param_row = parameter_mappings[parameter_mappings["csv_file"] == csv_name]
        if param_row.empty:
            continue

        param_column = param_row.iloc[0]["column_name"]

        # Validate parameter column exists
        if param_column not in df.columns:
            logger.warning(
                f"⚠️ Parameter column '{param_column}' not found in {csv_name}"
            )
            continue

        # Extract clean numeric values while preserving index
        values_series = df[param_column]
        values_clean = pd.to_numeric(values_series, errors="coerce").dropna()

        # Check minimum samples
        if len(values_clean) < outlier_config["min_samples_for_detection"]:
            logger.debug(
                f"  ⏭️ {csv_name}: {len(values_clean)} samples < {outlier_config['min_samples_for_detection']} minimum - skipping outlier detection"
            )
            outlier_results[csv_name] = {
                "outlier_indices": set(),
                "outlier_count": 0,
                "total_samples": len(values_clean),
            }
            continue

        # Detect outliers using standard IQR method
        method_settings = outlier_config["method_settings"][outlier_config["method"]]
        mild_outliers, _, lower_bound, upper_bound = detect_outliers_standard_iqr(
            values_clean, method_settings
        )

        # Store outlier indices
        outlier_indices = set(mild_outliers.index.tolist())
        outlier_count = len(outlier_indices)
        total_samples = len(values_clean)

        outlier_results[csv_name] = {
            "outlier_indices": outlier_indices,
            "outlier_count": outlier_count,
            "total_samples": total_samples,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
        }

        logger.info(
            f"  ✅ {csv_name}: {outlier_count}/{total_samples} outliers detected "
            f"(bounds: [{lower_bound:.2f}, {upper_bound:.2f}])"
        )

    return outlier_results


# ═══════════════════════════════════════════════════════════════════════════
# 🔄 HELPER FUNCTIONS (Reused from v27)
# ═══════════════════════════════════════════════════════════════════════════


def find_column_in_dataframe(
    df: pd.DataFrame,
    column_type: str,
    column_variations: Dict[str, List[str]],
    csv_name: Optional[str] = None,
) -> Optional[str]:
    """
    Find the correct column name in a DataFrame by checking all possible variations.

    Args:
        df: pandas DataFrame to search for columns
        column_type: String key from column_variations (e.g., 'geology_code2')
        column_variations: Dictionary mapping column types to lists of possible names
        csv_name: Optional CSV name for debugging purposes

    Returns:
        str or None: The found column name, or None if not found
    """
    if column_type not in column_variations:
        logger.warning(f"⚠️ Unknown column type '{column_type}' requested")
        return None

    available_columns = df.columns.tolist()
    possible_names = column_variations[column_type]

    # Check each possible name (exact match first)
    for name in possible_names:
        if name in available_columns:
            logger.debug(
                f"✅ Found column '{name}' for type '{column_type}' in {csv_name or 'DataFrame'}"
            )
            return name

    # If no exact match, try case-insensitive matching
    for name in possible_names:
        for col in available_columns:
            if name.lower() == col.lower():
                logger.debug(
                    f"✅ Found column '{col}' (case-insensitive) for type '{column_type}' in {csv_name or 'DataFrame'}"
                )
                return col

    # If still not found, log available columns for debugging
    logger.warning(
        f"❌ Column type '{column_type}' not found in {csv_name or 'DataFrame'}. "
        f"Available columns: {', '.join(available_columns[:5])}{'...' if len(available_columns) > 5 else ''}"
    )
    return None


def _get_geology_column_names(
    df: pd.DataFrame,
    csv_name: str,
    column_variations: Dict[str, List[str]],
) -> Tuple[Optional[str], Optional[str]]:
    """Get the geology column names by finding them in the DataFrame using flexible matching."""
    geology_desc_col = find_column_in_dataframe(
        df, "geology_code_description", column_variations, csv_name
    )
    geology_code_col = find_column_in_dataframe(
        df, "geology_code", column_variations, csv_name
    )
    return geology_desc_col, geology_code_col


def _find_geology_description_column(
    df_copy: pd.DataFrame, csv_name: str, geology_desc_col: Optional[str]
) -> bool:
    """Find and map geology description column to standard name."""
    if geology_desc_col and geology_desc_col in df_copy.columns:
        logger.debug(f"INFO {csv_name}: Found {geology_desc_col}")
        df_copy["Geological_Strata"] = df_copy[geology_desc_col]
        return True
    elif "Geology Code Description" in df_copy.columns:
        logger.debug(f"INFO {csv_name}: Found standard 'Geology Code Description'")
        df_copy["Geological_Strata"] = df_copy["Geology Code Description"]
        return True
    return False


def _create_description_from_code(
    df_copy: pd.DataFrame,
    csv_name: str,
    geology_code_col: Optional[str],
    geology_code_descriptions: Dict[str, str],
) -> None:
    """Create geology description from geology code using mapping."""
    if geology_code_col and geology_code_col in df_copy.columns:
        logger.debug(
            f"CREATING DESCRIPTION: {csv_name}: Creating description from {geology_code_col}"
        )
        df_copy["Geological_Strata"] = df_copy[geology_code_col].map(
            geology_code_descriptions
        )
        # Keep original code if unmapped to prevent data loss
        df_copy["Geological_Strata"].fillna(df_copy[geology_code_col], inplace=True)
    elif "Geology Code" in df_copy.columns:
        logger.debug(
            f"INFO {csv_name}: Creating description from standard 'Geology Code'"
        )
        df_copy["Geological_Strata"] = df_copy["Geology Code"].map(
            geology_code_descriptions
        )
        # Keep original code if unmapped to prevent data loss
        df_copy["Geological_Strata"].fillna(df_copy["Geology Code"], inplace=True)
    else:
        logger.error(
            f"❌ GEOLOGY PROCESSING FAILED: {csv_name} - No geology code column found"
        )
        df_copy["Geological_Strata"] = "Unknown Formation"


def _handle_missing_strata_values(df_copy: pd.DataFrame, csv_name: str) -> None:
    """Handle and log missing strata values."""
    missing_strata = df_copy["Geological_Strata"].isna().sum()
    if missing_strata > 0:
        logger.warning(
            f"WARNING {csv_name}: {missing_strata} rows with missing strata description"
        )


def classify_weathering_state(
    geology_code: str,
    geology_code2: Optional[str],
    geology_code2_desc: Optional[str],
    weathered_suffix: str,
    unweathered_suffix: str,
    fallback_classification: str,
) -> str:
    """Classify weathering state based on Geology Code2 prefix and suffix patterns."""
    if not geology_code2 or pd.isna(geology_code2):
        return fallback_classification

    geology_code2_clean = str(geology_code2).strip()

    # Validate prefix matches formation code first
    expected_prefix = f"{geology_code}_"
    if not geology_code2_clean.startswith(expected_prefix):
        return fallback_classification

    # Check suffix patterns for matching prefix entries
    if geology_code2_clean.endswith(weathered_suffix):
        return "weathered"

    if geology_code2_clean.endswith(unweathered_suffix):
        return "unweathered"

    return fallback_classification


def classify_rtd_subformation(
    geology_code: str,
    geology_code2: Optional[str],
    geology_code2_desc: Optional[str],
    rtd_mapping: Dict[str, str],
    fallback_classification: str,
) -> str:
    """Classify RTD sub-formation based on Geology Code2 patterns."""
    if geology_code != "RTD":
        return fallback_classification

    if not geology_code2 or pd.isna(geology_code2):
        return fallback_classification

    geology_code2_clean = str(geology_code2).strip()

    if geology_code2_clean in rtd_mapping:
        return rtd_mapping[geology_code2_clean]

    return fallback_classification


def create_enhanced_formation_code(
    geology_code: str,
    classification_state: str,
    target_formations: List[str],
    formation_type: str = "weathering",
) -> str:
    """Create enhanced formation code with weathering or RTD sub-formation designation."""
    if geology_code not in target_formations:
        return geology_code

    # Handle RTD formations
    if formation_type == "rtd" and geology_code == "RTD":
        if classification_state == "rtd_1":
            return "RTD_1"
        elif classification_state == "rtd_2":
            return "RTD_2"
        elif classification_state == "rtd_3":
            return "RTD_3"
        elif classification_state == "undefined":
            return "RTD_Undefined"
        else:
            return geology_code

    # Handle weathering formations (GF, KC)
    elif formation_type == "weathering" and geology_code in ["GF", "KC"]:
        if classification_state == "weathered":
            return f"{geology_code}_W"
        elif classification_state == "unweathered":
            return f"{geology_code}_UW"
        elif classification_state == "undefined":
            return geology_code
        else:
            return geology_code

    return geology_code


def _get_geology_code2_column_names(
    df: pd.DataFrame,
    csv_name: str,
    column_variations: Dict[str, List[str]],
) -> Tuple[Optional[str], Optional[str]]:
    """Get the correct Geology Code2 column names by finding them in the DataFrame."""
    geology_code2_col = find_column_in_dataframe(
        df, "geology_code2", column_variations, csv_name
    )
    geology_code2_desc_col = find_column_in_dataframe(
        df, "geology_code2_description", column_variations, csv_name
    )
    return geology_code2_col, geology_code2_desc_col


def add_strata_description(
    df: pd.DataFrame,
    csv_name: str,
    geology_code_descriptions: Dict[str, str],
    column_variations: Dict[str, List[str]],
) -> pd.DataFrame:
    """Add Geology Code Description column if missing and standardize strata column."""
    df_copy = df.copy()
    geology_desc_col, geology_code_col = _get_geology_column_names(
        df_copy, csv_name, column_variations
    )

    geology_desc_found = _find_geology_description_column(
        df_copy, csv_name, geology_desc_col
    )

    if not geology_desc_found and geology_code_col is not None:
        _create_description_from_code(
            df_copy, csv_name, geology_code_col, geology_code_descriptions
        )

    _handle_missing_strata_values(df_copy, csv_name)

    return df_copy


def _apply_formation_splitting(
    df: pd.DataFrame,
    csv_name: str,
    geology_code_col: str,
    geology_code2_col: str,
    geology_code2_desc_col: Optional[str],
    target_formations: List[str],
    weathering_config: Dict[str, str],
    geology_code_descriptions: Dict[str, str],
    rtd_target_formations: Optional[List[str]] = None,
    rtd_classification_config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Apply formation splitting logic to DataFrame for both weathering and RTD classifications."""
    df_copy = df.copy()

    # Extract weathering configuration
    weathered_suffix = weathering_config["weathered_suffix"]
    unweathered_suffix = weathering_config["unweathered_suffix"]
    fallback_classification = weathering_config["fallback_classification"]

    # Initialize counters for logging
    splitting_applied = 0
    weathered_count = 0
    unweathered_count = 0
    undefined_count = 0
    rtd_1_count = 0
    rtd_2_count = 0
    rtd_3_count = 0
    rtd_undefined_count = 0

    # Process each row for formation splitting
    for idx, row in df_copy.iterrows():
        geology_code = row.get(geology_code_col)
        geology_code2 = row.get(geology_code2_col)
        geology_code2_desc = (
            row.get(geology_code2_desc_col) if geology_code2_desc_col else None
        )

        # Weathering classification section
        if geology_code in target_formations:
            weathering_state = classify_weathering_state(
                geology_code,
                geology_code2,
                geology_code2_desc,
                weathered_suffix,
                unweathered_suffix,
                fallback_classification,
            )

            enhanced_code = create_enhanced_formation_code(
                geology_code,
                weathering_state,
                target_formations,
                formation_type="weathering",
            )

            if weathering_state == "undefined":
                base_code = geology_code
                if base_code in geology_code_descriptions:
                    base_description = geology_code_descriptions[base_code]
                    df_copy.loc[idx, "Geological_Strata"] = (
                        f"{base_description} (Undefined Classification)"
                    )
                    splitting_applied += 1
            elif enhanced_code in geology_code_descriptions:
                df_copy.loc[idx, "Geological_Strata"] = geology_code_descriptions[
                    enhanced_code
                ]
                splitting_applied += 1

            if weathering_state == "weathered":
                weathered_count += 1
            elif weathering_state == "unweathered":
                unweathered_count += 1
            else:
                undefined_count += 1

        # RTD classification section
        elif (
            rtd_target_formations
            and geology_code in rtd_target_formations
            and rtd_classification_config
        ):
            rtd_mapping = rtd_classification_config["mapping"]
            rtd_fallback_classification = rtd_classification_config[
                "fallback_classification"
            ]

            rtd_subformation = classify_rtd_subformation(
                geology_code,
                geology_code2,
                geology_code2_desc,
                rtd_mapping,
                rtd_fallback_classification,
            )

            enhanced_code = create_enhanced_formation_code(
                geology_code,
                rtd_subformation,
                rtd_target_formations,
                formation_type="rtd",
            )

            if enhanced_code in geology_code_descriptions:
                df_copy.loc[idx, "Geological_Strata"] = geology_code_descriptions[
                    enhanced_code
                ]
                splitting_applied += 1

            if rtd_subformation == "rtd_1":
                rtd_1_count += 1
            elif rtd_subformation == "rtd_2":
                rtd_2_count += 1
            elif rtd_subformation == "rtd_3":
                rtd_3_count += 1
            else:
                rtd_undefined_count += 1

    # Log formation splitting results
    if splitting_applied > 0:
        if weathered_count + unweathered_count + undefined_count > 0:
            logger.info(
                f"✅ {csv_name}: Weathering classification applied to {weathered_count + unweathered_count + undefined_count} rows "
                f"(W:{weathered_count}, UW:{unweathered_count}, Undefined:{undefined_count})"
            )
        if rtd_1_count + rtd_2_count + rtd_3_count + rtd_undefined_count > 0:
            logger.info(
                f"✅ {csv_name}: RTD classification applied to {rtd_1_count + rtd_2_count + rtd_3_count + rtd_undefined_count} rows "
                f"(RTD_1:{rtd_1_count}, RTD_2:{rtd_2_count}, RTD_3:{rtd_3_count}, Undefined:{rtd_undefined_count})"
            )
    else:
        logger.debug(f"INFO {csv_name}: No formation splitting applied")

    return df_copy


def create_enhanced_geological_strata_column(
    df: pd.DataFrame,
    csv_name: str,
    geology_code_descriptions: Dict[str, str],
    column_variations: Dict[str, List[str]],
    formation_splitting_config: Dict[str, Any],
) -> pd.DataFrame:
    """Enhanced formation mapping with weathered/unweathered splitting capability."""
    # Start with standard geological enhancement
    df_enhanced = add_strata_description(
        df,
        csv_name,
        geology_code_descriptions,
        column_variations,
    )

    # Check if formation splitting is enabled
    if not formation_splitting_config.get("enabled", False):
        logger.debug(
            f"INFO {csv_name}: Formation splitting disabled, using standard processing"
        )
        return df_enhanced

    # Extract formation splitting configuration
    target_formations = formation_splitting_config["target_formations"]
    weathering_config = formation_splitting_config["weathering_classification"]

    # Extract RTD configuration if enabled
    rtd_target_formations = None
    rtd_classification_config = None
    if formation_splitting_config.get("rtd_classification", {}).get("enabled", False):
        rtd_target_formations = formation_splitting_config["rtd_classification"][
            "target_formations"
        ]
        rtd_classification_config = formation_splitting_config["rtd_classification"]

    # Get Geology Code2 column names
    geology_code2_col, geology_code2_desc_col = _get_geology_code2_column_names(
        df_enhanced, csv_name, column_variations
    )

    # Check if Geology Code2 column exists (description column is no longer required)
    if geology_code2_col is None or geology_code2_col not in df_enhanced.columns:
        logger.debug(
            f"INFO {csv_name}: No Geology Code 2 column found, using standard strata"
        )
        return df_enhanced

    logger.info(f"🔄 {csv_name}: Applying formation splitting for {target_formations}")

    # Get geology code column
    geology_code_col = find_column_in_dataframe(
        df_enhanced, "geology_code", column_variations, csv_name
    )
    if geology_code_col is None or geology_code_col not in df_enhanced.columns:
        logger.warning(f"WARNING {csv_name}: No geology code column found")
        return df_enhanced

    # Apply formation splitting logic
    df_enhanced = _apply_formation_splitting(
        df_enhanced,
        csv_name,
        geology_code_col,
        geology_code2_col,
        geology_code2_desc_col,
        target_formations,
        weathering_config,
        geology_code_descriptions,
        rtd_target_formations,
        rtd_classification_config,
    )

    return df_enhanced


def standardize_location_columns(
    df: pd.DataFrame,
    csv_name: str,
    column_variations: Dict[str, List[str]],
) -> pd.DataFrame:
    """Standardize location and depth column names via safe copy operation using flexible matching."""
    df_copy = df.copy()

    # Standardize location column using flexible matching
    location_col = find_column_in_dataframe(
        df_copy, "location_id", column_variations, csv_name
    )
    if location_col is not None:
        df_copy["Location ID"] = df_copy[location_col]
        logger.debug(f"✅ {csv_name}: Mapped '{location_col}' to 'Location ID'")
    elif "Location ID" not in df_copy.columns:
        logger.warning(
            f"WARNING {csv_name}: No location column found - will skip location-based analysis"
        )

    # Standardize depth column using flexible matching
    depth_col = find_column_in_dataframe(
        df_copy, "top_depth", column_variations, csv_name
    )
    if depth_col is not None:
        df_copy["Top Depth"] = df_copy[depth_col]
        logger.debug(f"✅ {csv_name}: Mapped '{depth_col}' to 'Top Depth'")
    elif "Top Depth" not in df_copy.columns:
        logger.warning(
            f"WARNING {csv_name}: No depth column found - will use default values"
        )

    return df_copy


def filter_location_ids(
    df: pd.DataFrame,
    csv_name: str,
    enabled: bool,
    exclude_prefixes: List[str],
    case_sensitive: bool,
    column_variations: Dict[str, List[str]],
) -> pd.DataFrame:
    """Filter out rows with excluded location ID prefixes using flexible column matching."""
    if not enabled:
        return df

    df_copy = df.copy()
    initial_count = len(df_copy)

    # Find location column using flexible matching
    location_col = find_column_in_dataframe(
        df_copy, "location_id", column_variations, csv_name
    )

    if location_col is None:
        logger.debug(f"INFO {csv_name}: No location column found for filtering")
        return df_copy

    # Create filter mask
    filter_mask = pd.Series([True] * len(df_copy), index=df_copy.index)

    for prefix in exclude_prefixes:
        if case_sensitive:
            prefix_filter = (
                df_copy[location_col].astype(str).str.startswith(prefix, na=False)
            )
        else:
            prefix_filter = (
                df_copy[location_col]
                .astype(str)
                .str.upper()
                .str.startswith(prefix.upper(), na=False)
            )

        filter_mask = filter_mask & ~prefix_filter

    # Apply filter
    df_copy = df_copy[filter_mask]

    filtered_count = len(df_copy)
    excluded_count = initial_count - filtered_count

    if excluded_count > 0:
        logger.info(
            f"🚫 {csv_name}: Filtered out {excluded_count} rows with excluded location prefixes ({exclude_prefixes})"
        )
    else:
        logger.debug(f"INFO {csv_name}: No rows filtered (no matching prefixes found)")

    return df_copy


def load_csv_data(csv_files: List) -> Dict[str, pd.DataFrame]:
    """Load and standardize all CSV files with geological enhancement (Reused from v27)."""
    logger.info(f"📊 Loading {len(csv_files)} CSV files...")
    csv_data_dict = {}

    # Extract configuration values (coordination boundary)
    geology_code_descriptions = CONFIG["mappings"]["geology_code_descriptions"]
    column_variations = CONFIG["mappings"]["column_variations"]
    formation_splitting_config = CONFIG["mappings"]["formation_splitting"]

    # Filter configuration
    filter_config = CONFIG["filtering"]["location_filter"]
    filter_enabled = filter_config["enabled"]
    exclude_prefixes = filter_config["exclude_prefixes"]
    case_sensitive = filter_config["case_sensitive"]

    for csv_file in csv_files:
        # Handle both string paths and Path objects
        if isinstance(csv_file, str):
            csv_path = Path(csv_file)
            csv_name = Path(csv_file).name
        else:
            csv_path = csv_file
            csv_name = csv_file.name

        logger.debug(f"LOADING Loading {csv_name}...")

        try:
            # Load CSV with defensive data handling
            df = pd.read_csv(csv_path, encoding="utf-8")

            # Validate DataFrame is not empty
            if df.empty:
                logger.warning(f"WARNING {csv_name}: CSV file is empty, skipping.")
                continue

            # Defensive data handling
            df.columns = df.columns.str.strip()  # Remove whitespace from column names
            logger.debug(f"  STATS Loaded {len(df)} rows, {len(df.columns)} columns")

            # Add strata description with enhanced formation splitting
            df_with_strata = create_enhanced_geological_strata_column(
                df,
                csv_name,
                geology_code_descriptions,
                column_variations,
                formation_splitting_config,
            )
            if df_with_strata is None:
                continue

            # Standardize location columns
            standardized_df = standardize_location_columns(
                df_with_strata, csv_name, column_variations
            )
            if standardized_df is None:
                continue

            # Apply location ID filtering
            filtered_df = filter_location_ids(
                standardized_df,
                csv_name,
                filter_enabled,
                exclude_prefixes,
                case_sensitive,
                column_variations,
            )
            if filtered_df is not None:
                csv_data_dict[csv_name] = filtered_df
                logger.info(f"✅ {csv_name}: Successfully processed")
            else:
                logger.error(
                    f"❌ CSV PROCESSING FAILED: {csv_name} - Failed during filtering"
                )

        except Exception as e:
            logger.error(f"❌ CSV LOAD FAILED: {csv_name} - {str(e)}")

    logger.info(f"✅ Successfully loaded {len(csv_data_dict)} CSV files")
    return csv_data_dict


# ═══════════════════════════════════════════════════════════════════════════
# 🔧 EMPIRICAL CALCULATIONS (Reused from v27)
# ═══════════════════════════════════════════════════════════════════════════


def apply_empirical_calculations(
    df_copy: pd.DataFrame,
    parameter_name: str,
    csv_name: str,
    column_name: str,
    f1_factor_config: Optional[Dict[str, float]] = None,
    geology_code_descriptions: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """Apply empirical calculations for derived parameters with formation-specific factors.

    Args:
        df_copy: DataFrame copy to modify
        parameter_name: Target parameter being analyzed
        csv_name: Source CSV file name
        column_name: Source column name
        f1_factor_config: Dictionary mapping formation codes to f1 factors
        geology_code_descriptions: Existing geology code descriptions from CONFIG

    Returns:
        DataFrame: Modified dataframe with empirical calculations applied
    """
    # MODIFICATION POINT: Add new empirical calculations here

    # SPT N-value to Undrained Shear Strength conversion with formation-specific f1 factors
    if (
        parameter_name == "UndrainedShearStrength"
        and csv_name == "SPT by Geology.csv"
        and column_name == "N"
        and f1_factor_config is not None
    ):
        logger.info(
            f"🔄 Applying formation-specific SPT cu calculations for {csv_name}"
        )

        # Check if Geological_Strata column exists
        if "Geological_Strata" not in df_copy.columns:
            logger.warning(
                "⚠️ No Geological_Strata column found - using default f1 factor"
            )
            default_f1 = f1_factor_config.get("default_f1_factor", 4.5)
            df_copy[column_name] = (
                pd.to_numeric(df_copy[column_name], errors="coerce") * default_f1
            )
            return df_copy

        # Initialize calculated column - start with default f1 for all samples
        calculated_column = f"{column_name}_calculated_cu"
        default_f1 = f1_factor_config.get("default_f1_factor", 4.5)

        # Apply default calculation to all valid N values first
        df_copy[calculated_column] = (
            pd.to_numeric(df_copy[column_name], errors="coerce") * default_f1
        )

        formation_counts = {"default": {"f1_factor": default_f1, "conversions": 0}}
        total_conversions = df_copy[calculated_column].notna().sum()

        # Override with formation-specific f1 factors where formation is identified
        for formation_code, f1_factor in f1_factor_config.items():
            if formation_code == "default_f1_factor":
                continue

            # Multi-tier formation matching with undefined formation support:
            # Tier 1: Exact enhanced code match (e.g., "KC_W", "KC_UW") - Highest priority
            # Tier 2: Undefined formation match (e.g., "Kimmeridge Clay Formation (Undefined Classification)" -> "KC_undefined")
            # Tier 3: Default f1 factor - Fallback (NO LONGER supports simple "KC"/"GF" matches)

            # Find rows matching this formation code
            formation_mask = pd.Series([False] * len(df_copy), index=df_copy.index)

            # Handle undefined formation codes (KC_undefined, GF_undefined)
            if "_undefined" in formation_code:
                base_formation = formation_code.replace("_undefined", "")

                # Map to formation descriptions for undefined classification matching
                if (
                    geology_code_descriptions
                    and base_formation in geology_code_descriptions
                ):
                    target_description = f"{geology_code_descriptions[base_formation]} (Undefined Classification)"
                    undefined_match = df_copy["Geological_Strata"] == target_description
                    formation_mask = formation_mask | undefined_match

            # Enhanced code matching (KC_W, KC_UW, GF_W, GF_UW, etc.) - match using descriptions
            elif formation_code in geology_code_descriptions:
                target_description = geology_code_descriptions[formation_code]
                exact_match = df_copy["Geological_Strata"] == target_description
                formation_mask = formation_mask | exact_match

            if formation_mask.any():
                # Apply formation-specific calculation (override default)
                valid_n_mask = pd.to_numeric(
                    df_copy[column_name], errors="coerce"
                ).notna()
                calculation_mask = formation_mask & valid_n_mask

                df_copy.loc[calculation_mask, calculated_column] = (
                    pd.to_numeric(
                        df_copy.loc[calculation_mask, column_name], errors="coerce"
                    )
                    * f1_factor
                )

                conversions = calculation_mask.sum()
                formation_counts[formation_code] = {
                    "f1_factor": f1_factor,
                    "conversions": conversions,
                }

                logger.info(
                    f"  ✅ {formation_code} (f1={f1_factor}): {conversions} conversions"
                )

        # Count remaining samples that used default f1 factor
        identified_samples = sum(
            info["conversions"]
            for code, info in formation_counts.items()
            if code != "default"
        )
        default_samples = total_conversions - identified_samples
        formation_counts["default"]["conversions"] = default_samples

        if default_samples > 0:
            logger.info(
                f"  ⚠️ Unidentified formations (f1={default_f1}): {default_samples} conversions"
            )

        # Replace original column and cleanup
        df_copy[column_name] = df_copy[calculated_column]
        df_copy.drop(columns=[calculated_column], inplace=True)

        logger.info(
            f"✅ Formation-specific SPT calculation completed: {total_conversions} total conversions"
        )

    # Legacy SPT calculation for backward compatibility when no f1 config is provided
    elif (
        parameter_name == "UndrainedShearStrength"
        and csv_name == "SPT by Geology.csv"
        and column_name == "N"
        and f1_factor_config is None
    ):
        logger.info(
            f"🔄 Applying legacy empirical calculation: cu = f1 × N for {csv_name}"
        )

        # Create a new column for the calculated cu values
        calculated_column = f"{column_name}_calculated_cu"

        # Apply the empirical formula: cu = f1 × N
        df_copy[calculated_column] = (
            pd.to_numeric(df_copy[column_name], errors="coerce") * 4.5
        )

        # Count successful conversions
        valid_conversions = df_copy[calculated_column].notna().sum()
        total_n_values = df_copy[column_name].notna().sum()

        logger.info(
            f"✅ Legacy empirical calculation completed: {valid_conversions}/{total_n_values} N-values converted to cu"
        )

        # Replace the original column with the calculated values
        df_copy[column_name] = df_copy[calculated_column]

        # Clean up the temporary column
        df_copy.drop(columns=[calculated_column], inplace=True)

    return df_copy


# ═══════════════════════════════════════════════════════════════════════════
# �📊 PHASE 1: PARAMETER MAPPING EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════


def extract_parameter_mappings(
    parameter_name: str, mapping_csv_path: str
) -> pd.DataFrame:
    """
    Extract CSV-to-column mappings for specified parameter from global mapping file.

    This function parses Global_Parameter_Mapping_Extraction_only_CORRECTED.csv to identify
    all CSV files and columns containing data for the target parameter. Results are sorted
    by priority_rank (lower is better) and quality_score (higher is better) to ensure
    highest quality data sources are used first.

    Args:
        parameter_name: Target parameter matching 'parameter' column in mapping CSV
                       (e.g., "UndrainedShearStrength", "MoistureContent")
        mapping_csv_path: Path to Global_Parameter_Mapping_Extraction_only_CORRECTED.csv

    Returns:
        DataFrame with columns: [csv_file, column_name, priority_rank, quality_score]
        Sorted by priority_rank ascending, quality_score descending
        Empty DataFrame if parameter not found

    Raises:
        FileNotFoundError: If mapping_csv_path does not exist
        KeyError: If required columns missing from mapping CSV

    Example Output:
        >>> extract_parameter_mappings("UndrainedShearStrength", "Global_Parameter_Mapping.csv")

                                      csv_file           column_name  priority_rank  quality_score
        0   Triaxial Total Stress by Geology.csv                    Cu              1             10
        1  Triaxial Effective Stress by Geology.csv                  Cu              2              9
        2              Vane Tests by Geology.csv  Undrained Shear Strength           3              8
    """
    logger.info(f"🚀 PHASE 1: Extracting parameter mappings for '{parameter_name}'")

    # === VALIDATION SECTION ===
    mapping_path = Path(mapping_csv_path)
    if not mapping_path.exists():
        logger.error(f"❌ Mapping file not found: {mapping_csv_path}")
        raise FileNotFoundError(f"Mapping CSV not found: {mapping_csv_path}")

    # === DATA LOADING SECTION ===
    try:
        mapping_df = pd.read_csv(mapping_csv_path)
        logger.info(
            f"📊 Loaded mapping CSV: {len(mapping_df)} total parameter mappings"
        )
    except Exception as e:
        logger.error(f"❌ Failed to read mapping CSV: {e}")
        raise

    # === COLUMN VALIDATION SECTION ===
    required_cols = [
        "parameter",
        "csv_file",
        "column_name",
        "priority_rank",
        "quality_score",
    ]
    missing_cols = [col for col in required_cols if col not in mapping_df.columns]
    if missing_cols:
        logger.error(f"❌ Missing required columns in mapping CSV: {missing_cols}")
        raise KeyError(f"Mapping CSV missing required columns: {missing_cols}")

    # === PARAMETER FILTERING SECTION ===
    param_mappings = mapping_df[mapping_df["parameter"] == parameter_name].copy()

    if param_mappings.empty:
        logger.warning(f"⚠️ No mappings found for parameter '{parameter_name}'")
        logger.warning(
            f"Available parameters: {sorted(mapping_df['parameter'].unique())}"
        )
        return pd.DataFrame(columns=required_cols)

    # === SORTING SECTION ===
    # Sort by priority_rank (lower is better) and quality_score (higher is better)
    param_mappings = param_mappings.sort_values(
        by=["priority_rank", "quality_score"], ascending=[True, False]
    ).reset_index(drop=True)

    # === LOGGING SECTION ===
    logger.info(f"✅ Found {len(param_mappings)} CSV sources for '{parameter_name}':")
    for idx, row in param_mappings.iterrows():
        logger.info(
            f"  {idx+1}. {row['csv_file']:<45} → {row['column_name']:<30} "
            f"(Priority: {row['priority_rank']}, Quality: {row['quality_score']})"
        )

    # Return only required columns
    return param_mappings[required_cols]


# ═══════════════════════════════════════════════════════════════════════════
# 💾 PHASE 2: CSV DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════


def load_parameter_data(
    parameter_mappings: pd.DataFrame, csv_source_folder: str
) -> Dict[str, pd.DataFrame]:
    """
    Load all CSV files containing the target parameter with geological enhancement.

    This function wraps v27's load_csv_data() to load CSVs identified in Phase 1.
    It handles column standardization, location filtering, and formation enhancement
    (weathered/unweathered classification) automatically via the reused v27 functions.

    Args:
        parameter_mappings: DataFrame from extract_parameter_mappings() with columns:
                           [csv_file, column_name, priority_rank, quality_score]
        csv_source_folder: Folder containing CSV files (e.g., "Openground CSVs")

    Returns:
        Dict[csv_filename, enhanced_dataframe] with:
        - Standardized columns: "Location ID", "Top Depth", "Geological_Strata"
        - Formation splitting applied: GF → GF_W/GF_UW, KC → KC_W/KC_UW
        - Location filtering applied: BP/CCT locations removed
        - All original parameter columns preserved

    Example:
        >>> param_mappings = extract_parameter_mappings("UndrainedShearStrength", "Global_Mapping.csv")
        >>> csv_data = load_parameter_data(param_mappings, "Openground CSVs")
        >>> csv_data.keys()
        dict_keys(['Triaxial Total Stress by Geology.csv', 'Vane Tests by Geology.csv'])
    """
    logger.info(f"🚀 PHASE 2: Loading CSV data for parameter sources")

    # === CSV PATH CONSTRUCTION SECTION ===
    # Build list of unique CSV file paths from parameter mappings
    unique_csv_files = parameter_mappings["csv_file"].unique()
    csv_files = [
        Path(csv_source_folder) / csv_filename for csv_filename in unique_csv_files
    ]

    logger.info(f"📂 Will load {len(csv_files)} unique CSV files:")
    for csv_file in csv_files:
        logger.info(f"  • {csv_file.name}")

    # === DATA LOADING SECTION ===
    # Call v27's load_csv_data() - handles complete data loading workflow:
    # 1. Column standardization (standardize_location_columns)
    # 2. Location filtering (filter_location_ids) - removes BP/CCT
    # 3. Formation enhancement (create_enhanced_geological_strata_column)
    #    - Weathered/unweathered classification for GF/KC
    #    - RTD sub-formation classification
    csv_data_dict = load_csv_data(csv_files)

    # === EMPIRICAL CALCULATIONS SECTION ===
    # Apply empirical calculations (e.g., SPT N-value to cu conversion)
    # MODIFICATION POINT: This processes each loaded CSV before grouping by formation
    if csv_data_dict and "empirical_calculations" in CONFIG:
        logger.info("")
        logger.info(f"🔧 Applying empirical calculations...")

        # Extract configuration values (coordination boundary)
        f1_factor_config = CONFIG["empirical_calculations"]["spt_to_cu_factors"]
        geology_code_descriptions = CONFIG["mappings"]["geology_code_descriptions"]

        # Get parameter name from caller context (extract from parameter_mappings)
        # Note: We need to infer parameter_name from context since it's not passed
        # For now, use CONFIG parameter name
        parameter_name = CONFIG["parameter"]["name"]

        # Process each CSV file with its parameter column
        for _, mapping in parameter_mappings.iterrows():
            csv_name = mapping["csv_file"]
            column_name = mapping["column_name"]

            if csv_name in csv_data_dict:
                df_original = csv_data_dict[csv_name]
                df_modified = apply_empirical_calculations(
                    df_original.copy(),
                    parameter_name,
                    csv_name,
                    column_name,
                    f1_factor_config,
                    geology_code_descriptions,
                )
                csv_data_dict[csv_name] = df_modified

        logger.info(f"✅ Empirical calculations complete")
        logger.info("")

    # === VALIDATION SECTION ===
    if not csv_data_dict:
        logger.error("❌ PHASE 2 FAILED: No CSV files successfully loaded")
        return {}

    # === LOGGING SECTION ===
    logger.info("")
    logger.info(f"✅ PHASE 2 COMPLETE: Loaded {len(csv_data_dict)} CSV files")
    for csv_name, df in csv_data_dict.items():
        formations = (
            df["Geological_Strata"].nunique()
            if "Geological_Strata" in df.columns
            else 0
        )
        logger.info(f"  • {csv_name}: {len(df)} rows, {formations} formations")

    return csv_data_dict


# ═══════════════════════════════════════════════════════════════════════════
# 🎨 COLOR MAPPING: CONSISTENT COLOR ASSIGNMENT
# ═══════════════════════════════════════════════════════════════════════════


def create_global_color_mapping(
    parameter_mappings: pd.DataFrame,
) -> Dict[str, str]:
    """
    Create a global color mapping dictionary for all test types.

    This ensures consistent color assignment across all formations, even when
    some test types are missing from individual formations.

    Args:
        parameter_mappings: DataFrame with columns [csv_file, column_name, priority_rank, quality_score]

    Returns:
        dict: {csv_name: color_hex_code} mapping for all test types
    """
    logger.info("🎨 Creating global color mapping for all test types...")

    # Get color palette from CONFIG
    color_palette = CONFIG["plotting"]["colors"]["csv_source_colors"]

    # Get all unique CSV files (test types) from parameter mappings
    csv_files = sorted(parameter_mappings["csv_file"].unique())

    # Create mapping: {csv_name: color}
    color_mapping = {}
    for idx, csv_name in enumerate(csv_files):
        color = color_palette[idx % len(color_palette)]
        color_mapping[csv_name] = color
        logger.debug(f"  {csv_name}: {color}")

    logger.info(f"✅ Color mapping created for {len(color_mapping)} test types")
    return color_mapping


def load_manual_outliers(
    parameter_name: str, excel_file: str, sheet_mapping: Dict[str, str]
) -> Optional[pd.DataFrame]:
    """
    Load manually identified outliers from Excel spreadsheet.

    Reads the Excel file specified in CONFIG and extracts manually identified
    outliers for the current parameter. These outliers are matched against
    data points by Location ID, parameter value, and depth.

    Args:
        parameter_name: Parameter name (e.g., "MoistureContent")
        excel_file: Path to Excel file with manual outliers
        sheet_mapping: Dict mapping parameter names to sheet names

    Returns:
        DataFrame with columns [Location ID, parameter_value, depth_value, Test Type, Notes]
        or None if disabled/error occurs
    """
    if not CONFIG["manual_outlier_exclusion"]["enabled"]:
        logger.info("⏭️ Manual outlier exclusion disabled in CONFIG")
        return None

    sheet_name = sheet_mapping.get(parameter_name)
    if not sheet_name:
        logger.warning(
            f"⚠️ No sheet mapping found for parameter '{parameter_name}' in manual outlier config"
        )
        return None

    try:
        logger.info(
            f"💾 Loading manual outliers from '{excel_file}' (Sheet: '{sheet_name}')..."
        )
        df_outliers = pd.read_excel(excel_file, sheet_name=sheet_name)

        # Standardize column names for matching
        df_outliers = df_outliers.rename(
            columns={
                "Location ID": "Location ID",
                "x": "parameter_value",
                "y": "depth_value",
            }
        )

        required_cols = ["Location ID", "parameter_value", "depth_value"]
        if not all(col in df_outliers.columns for col in required_cols):
            logger.error(
                f"❌ Manual outlier Excel sheet '{sheet_name}' is missing required columns: {required_cols}"
            )
            return None

        # Clean up Location IDs (strip whitespace)
        df_outliers["Location ID"] = df_outliers["Location ID"].astype(str).str.strip()

        logger.info(f"✅ Loaded {len(df_outliers)} manually identified outliers")
        return df_outliers

    except FileNotFoundError:
        logger.error(f"❌ Manual outlier Excel file not found: {excel_file}")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to load manual outliers: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 🔄 PHASE 3: FORMATION GROUPING
# ═══════════════════════════════════════════════════════════════════════════


def group_data_by_formation(
    csv_data_dict: Dict[str, pd.DataFrame], parameter_mappings: pd.DataFrame
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Group data by geological formation for plotting.

    This function organizes loaded CSV data into a nested structure where each formation
    contains data from all relevant CSV sources. The grouping enables generation of
    separate plots for each geological formation with color-coded test types.

    Args:
        csv_data_dict: Dictionary of loaded and enhanced CSV data
                      Key: CSV filename (e.g., "Triaxial Total Stress by Geology.csv")
                      Value: DataFrame with standardized columns including "Geological_Strata"
        parameter_mappings: DataFrame from extract_parameter_mappings() with columns:
                           [csv_file, column_name, priority_rank, quality_score]
                           Used to lookup parameter column name for each CSV

    Returns:
        Nested dictionary structure: {formation_name: {csv_name: dataframe}}
        - Outer keys: Geological formation names (e.g., "Gault Clay Formation (Weathered)")
        - Inner keys: CSV filenames containing data for that formation
        - Inner values: DataFrames with columns [Location ID, Top Depth, Geological_Strata, parameter_column]

        Example:
        {
            "Gault Clay Formation (Weathered)": {
                "Triaxial Total Stress by Geology.csv": DataFrame(150 rows, Cu column),
                "Vane Tests by Geology.csv": DataFrame(45 rows, Undrained Shear Strength column)
            },
            "Kimmeridge Clay Formation (Unweathered)": {
                "Triaxial Total Stress by Geology.csv": DataFrame(89 rows, Cu column)
            }
        }

    Processing Logic:
    1. For each CSV, lookup parameter column name from parameter_mappings
    2. Verify required columns exist (Geological_Strata, Top Depth, parameter column)
    3. Group CSV data by Geological_Strata values
    4. Filter out rows with null parameter values or depths
    5. Store non-empty formation groups in nested dictionary structure

    Notes:
    - Empty formations (after filtering nulls) are not included in output
    - CSVs missing required columns are skipped with warning log
    - Formation names match enhanced codes from Phase 2 (e.g., GF_W → "Gault Clay Formation (Weathered)")
    """
    logger.info(f"🚀 PHASE 3: Grouping data by geological formation")

    # === INITIALIZATION SECTION ===
    # Use defaultdict for automatic dictionary creation
    formation_dict = defaultdict(lambda: defaultdict(pd.DataFrame))

    # === CSV ITERATION SECTION ===
    for csv_name, df in csv_data_dict.items():
        logger.debug(f"  Processing {csv_name}...")

        # === PARAMETER COLUMN LOOKUP SECTION ===
        # Get parameter column name for this CSV from mappings
        matching_mappings = parameter_mappings[
            parameter_mappings["csv_file"] == csv_name
        ]

        if matching_mappings.empty:
            logger.warning(f"⚠️ {csv_name}: No parameter mapping found, skipping")
            continue

        column_name = matching_mappings["column_name"].iloc[0]

        # === COLUMN VALIDATION SECTION ===
        # Verify parameter column exists in DataFrame
        if column_name not in df.columns:
            logger.warning(
                f"⚠️ {csv_name}: Parameter column '{column_name}' not found in data, skipping"
            )
            continue

        # Verify required columns exist
        required_cols = ["Geological_Strata", "Top Depth", column_name]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(
                f"⚠️ {csv_name}: Missing required columns {missing_cols}, skipping"
            )
            continue

        # === FORMATION GROUPING SECTION ===
        # Get unique formations in this CSV
        formations = df["Geological_Strata"].unique()

        for formation in formations:
            # Filter data for this formation
            formation_data = df[df["Geological_Strata"] == formation].copy()

            # === DATA CLEANING SECTION ===
            # Remove rows with null parameter values or depths
            formation_data = formation_data.dropna(subset=[column_name, "Top Depth"])

            # === STORAGE SECTION ===
            # Only store non-empty formation groups
            if not formation_data.empty:
                formation_dict[formation][csv_name] = formation_data
                logger.debug(
                    f"    → {formation}: {len(formation_data)} samples from {csv_name}"
                )

    # === LOGGING SECTION ===
    logger.info("")
    logger.info(f"✅ Grouped data into {len(formation_dict)} formations:")

    for formation, csv_dict in sorted(formation_dict.items()):
        total_samples = sum(len(df) for df in csv_dict.values())
        csv_count = len(csv_dict)
        logger.info(
            f"  • {formation}: {total_samples} samples from {csv_count} CSV source(s)"
        )

        # Log CSV breakdown for each formation
        for csv_name, df in csv_dict.items():
            logger.debug(f"      - {csv_name}: {len(df)} samples")

    # Convert defaultdict to regular dict for cleaner output
    return dict(formation_dict)


# ═══════════════════════════════════════════════════════════════════════════
# 🧹 PHASE 3b: OUTLIER FILTERING (WITHOUT PLOTTING)
# ═══════════════════════════════════════════════════════════════════════════


def filter_outliers_from_formations(
    formation_groups: Dict[str, Dict[str, pd.DataFrame]],
    parameter_mappings: pd.DataFrame,
) -> None:
    """
    Apply outlier filtering to all formations without generating plots.

    Lightweight outlier filtering that adds 'is_outlier' column to each formation's
    dataframes. This enables Phase 4 (investigation-series plots) to correctly
    filter outliers when generating with-outliers vs without-outliers versions.

    Args:
        formation_groups: Dict mapping formations to CSV data dicts (MODIFIED IN-PLACE)
        parameter_mappings: Parameter mapping DataFrame

    Side Effects:
        Modifies formation_groups in-place by adding 'is_outlier' column to each DataFrame
    """
    if not CONFIG["outlier_detection"]["enabled"]:
        logger.info("⏭️ Outlier filtering disabled in CONFIG - skipping Phase 3b")
        return

    logger.info(
        f"🚀 PHASE 3b: Filtering outliers for {len(formation_groups)} formations"
    )

    for formation_name in sorted(formation_groups.keys()):
        csv_dict = formation_groups[formation_name]

        # Detect outliers per CSV
        outlier_results = detect_outliers_per_csv(
            csv_dict,
            parameter_mappings,
            formation_name,
            CONFIG["outlier_detection"],
        )

        # Mark outliers in each DataFrame
        for csv_name, df in csv_dict.items():
            if csv_name in outlier_results:
                outlier_indices = outlier_results[csv_name]["outlier_indices"]
                df["is_outlier"] = df.index.isin(outlier_indices)
            else:
                df["is_outlier"] = False

    logger.info("✅ Outlier filtering complete - 'is_outlier' column added to all data")


# ═══════════════════════════════════════════════════════════════════════════
# 📍 PHASE 3c: MANUAL OUTLIER MARKING
# ═══════════════════════════════════════════════════════════════════════════


def mark_manual_outliers(
    formation_groups: Dict[str, Dict[str, pd.DataFrame]],
    manual_outliers_df: Optional[pd.DataFrame],
    parameter_mappings: pd.DataFrame,
    param_tolerance: float,
    depth_tolerance: float,
) -> None:
    """
    Mark manually identified outliers in formation dataframes.

    Adds 'is_manual_outlier' boolean column to each DataFrame based on matching
    Location ID, parameter value, and depth value from the manual outliers Excel.

    Args:
        formation_groups: Nested dict of formation data (MODIFIED IN-PLACE)
        manual_outliers_df: DataFrame with manual outliers from Excel
        parameter_mappings: Parameter mapping DataFrame
        param_tolerance: Tolerance for matching parameter values
        depth_tolerance: Tolerance for matching depth values

    Side Effects:
        Modifies formation_groups in-place by adding 'is_manual_outlier' column
    """
    if manual_outliers_df is None or manual_outliers_df.empty:
        logger.info(
            "⏭️ No manual outliers to mark - adding False column for consistency"
        )
        # Add column with all False values for consistency
        for csv_dict in formation_groups.values():
            for df in csv_dict.values():
                df["is_manual_outlier"] = False
        return

    logger.info("🚀 PHASE 3c: Marking manually identified outliers...")

    total_marked = 0
    outliers_by_loc = manual_outliers_df.groupby("Location ID")

    for formation_name, csv_dict in formation_groups.items():
        for csv_name, df in csv_dict.items():
            # Initialize column
            df["is_manual_outlier"] = False

            # Get parameter column for this CSV
            matching_mappings = parameter_mappings[
                parameter_mappings["csv_file"] == csv_name
            ]
            if matching_mappings.empty:
                continue

            param_col = matching_mappings["column_name"].iloc[0]

            if param_col not in df.columns or "Top Depth" not in df.columns:
                continue

            # Mark manual outliers by matching Location ID + values
            marked_indices = []
            for index, row in df.iterrows():
                loc_id = str(row["Location ID"]).strip()

                if loc_id in outliers_by_loc.groups:
                    possible_matches = outliers_by_loc.get_group(loc_id)

                    for _, outlier_row in possible_matches.iterrows():
                        param_match = np.isclose(
                            row[param_col],
                            outlier_row["parameter_value"],
                            atol=param_tolerance,
                        )
                        depth_match = np.isclose(
                            row["Top Depth"],
                            outlier_row["depth_value"],
                            atol=depth_tolerance,
                        )

                        if param_match and depth_match:
                            marked_indices.append(index)
                            total_marked += 1
                            break  # Move to next row once matched

            if marked_indices:
                df.loc[marked_indices, "is_manual_outlier"] = True
                logger.info(
                    f"  ✅ {formation_name} | {csv_name}: Marked {len(marked_indices)} manual outliers"
                )

    logger.info(
        f"✅ Phase 3c complete: Marked a total of {total_marked} manual outliers"
    )


def print_manual_outlier_summary(
    manual_outliers_df: Optional[pd.DataFrame],
    formation_groups: Dict[str, Dict[str, pd.DataFrame]],
    parameter_mappings: pd.DataFrame,
) -> None:
    """
    Print summary table of manual outlier identification status.

    Shows which manual outliers from the Excel file were successfully
    identified and excluded, and provides reasons for any that weren't.

    Args:
        manual_outliers_df: DataFrame with manual outliers from Excel
        formation_groups: Formation data with is_manual_outlier column
        parameter_mappings: Parameter mappings to find column names
    """
    if manual_outliers_df is None or manual_outliers_df.empty:
        logger.info("⏭️ No manual outliers loaded - skipping summary")
        return

    logger.info("")
    logger.info("=" * 150)
    logger.info("📋 MANUAL OUTLIER EXCLUSION SUMMARY")
    logger.info("=" * 150)
    logger.info("")

    # Track identification status
    results = []

    for idx, outlier_row in manual_outliers_df.iterrows():
        location_id = outlier_row["Location ID"]
        param_value = outlier_row["parameter_value"]
        depth_value = outlier_row["depth_value"]
        test_type = outlier_row.get("Test Type", "Unknown")
        notes = outlier_row.get("Notes", "")

        # Search for this outlier in formation groups
        identified = False
        reason = "Not found in any formation data"

        for formation_name, csv_dict in formation_groups.items():
            for csv_name, df in csv_dict.items():
                # Check if this is the right CSV for the test type
                if test_type not in csv_name:
                    continue

                # Get parameter column
                matching_mappings = parameter_mappings[
                    parameter_mappings["csv_file"] == csv_name
                ]
                if matching_mappings.empty:
                    continue

                param_col = matching_mappings["column_name"].iloc[0]

                if param_col not in df.columns or "Top Depth" not in df.columns:
                    continue

                # Check if this location+value combination exists and is marked
                location_matches = df[df["Location ID"] == location_id]

                if not location_matches.empty:
                    # Check for matching parameter and depth values
                    for _, row in location_matches.iterrows():
                        param_match = np.isclose(row[param_col], param_value, atol=1e-5)
                        depth_match = np.isclose(
                            row["Top Depth"], depth_value, atol=1e-5
                        )

                        if param_match and depth_match:
                            # Found the data point - check if marked as manual outlier
                            if "is_manual_outlier" in df.columns:
                                if row.get("is_manual_outlier", False):
                                    identified = True
                                    reason = "✅ Successfully identified and excluded"
                                else:
                                    reason = "Found but not marked (possible tolerance mismatch)"
                            else:
                                reason = "Found but is_manual_outlier column missing"
                            break

                    if not identified and reason == "Not found in any formation data":
                        reason = (
                            "Location ID exists but parameter/depth values don't match"
                        )

                if identified:
                    break

            if identified:
                break

        results.append(
            {
                "Entry #": idx + 1,
                "Location ID": location_id,
                "x (Param)": f"{param_value:.2f}",
                "y (Depth)": f"{depth_value:.2f}",
                "Test Type": test_type,
                "Excluded?": "✅ Yes" if identified else "❌ No",
                "Reason": reason,
                "Notes": notes,
            }
        )

    # Summary statistics
    total = len(results)
    identified_count = sum(1 for r in results if r["Excluded?"] == "✅ Yes")

    logger.info("📊 Summary Statistics:")
    logger.info(f"   Total manual outlier entries in Excel: {total}")
    logger.info(
        f"   Successfully identified & excluded: {identified_count} ({identified_count/total*100:.1f}%)"
    )
    logger.info(
        f"   Not identified: {total - identified_count} ({(total - identified_count)/total*100:.1f}%)"
    )
    logger.info("")

    # Print table header
    logger.info("📋 Detailed Breakdown:")
    logger.info("")
    header = (
        f"{'#':<5} | {'Location ID':<12} | {'x (Param)':<10} | {'y (Depth)':<10} | "
        f"{'Test Type':<25} | {'Excluded?':<12} | {'Reason':<50}"
    )
    logger.info(header)
    logger.info("-" * len(header))

    # Print table rows
    for result in results:
        logger.info(
            f"{result['Entry #']:<5} | {result['Location ID']:<12} | {result['x (Param)']:<10} | "
            f"{result['y (Depth)']:<10} | {result['Test Type']:<25} | {result['Excluded?']:<12} | "
            f"{result['Reason']:<50}"
        )

    logger.info("")
    logger.info("=" * 150)


# ═══════════════════════════════════════════════════════════════════════════
# 🎨 PHASE 4: INVESTIGATION SERIES PLOT GENERATION
# ═══════════════════════════════════════════════════════════════════════════


def create_investigation_color_mapping(
    investigations: List[str], color_palette: List[str]
) -> Dict[str, str]:
    """
    Create color mapping for investigations using rotating color palette.

    Assigns a unique color to each investigation from the provided palette.
    If there are more investigations than colors, the palette rotates.

    Args:
        investigations: List of unique investigation names
        color_palette: List of hex color codes (e.g., ["#0057B7", "#8B0000"])

    Returns:
        Dictionary mapping investigation names to hex color codes

    Example:
        >>> create_investigation_color_mapping(
        ...     ["Site A", "Site B", "Site C"],
        ...     ["#0057B7", "#8B0000"]
        ... )
        {"Site A": "#0057B7", "Site B": "#8B0000", "Site C": "#0057B7"}
    """
    investigation_colors = {}
    for idx, investigation in enumerate(sorted(investigations)):
        color_idx = idx % len(color_palette)
        investigation_colors[investigation] = color_palette[color_idx]
    return investigation_colors


def _load_location_details_for_plotting(
    csv_folder: str,
    location_csv_name: str,
    location_id_variants: List[str],
    investigation_variants: List[str],
) -> pd.DataFrame:
    """
    Load Location Details CSV for per-investigation plotting.

    Reads the Location Details CSV file and returns a DataFrame with standardized
    column names for Location ID and Investigation. Handles column name variations
    and missing values.

    Args:
        csv_folder: Absolute path to folder containing Location Details CSV
        location_csv_name: Name of the Location Details CSV file
        location_id_variants: List of possible Location ID column names
        investigation_variants: List of possible Investigation column names

    Returns:
        pd.DataFrame with standardized 'Location ID' and 'Investigation' columns,
        or empty DataFrame if file not found or error occurs
    """
    csv_folder_path = Path(csv_folder)
    location_csv = csv_folder_path / location_csv_name

    try:
        df = pd.read_csv(location_csv, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()

        # Find Location ID column
        location_id_col = None
        for variant in location_id_variants:
            if variant in df.columns:
                location_id_col = variant
                break

        # Find Investigation column
        investigation_col = None
        for variant in investigation_variants:
            if variant in df.columns:
                investigation_col = variant
                break

        if not location_id_col or not investigation_col:
            logger.warning(
                f"⚠️ Required columns not found in {location_csv_name}. "
                f"Expected: {location_id_variants} and {investigation_variants}"
            )
            return pd.DataFrame()

        # Standardize column names
        result_df = df[[location_id_col, investigation_col]].copy()
        result_df.columns = ["Location ID", "Investigation"]

        # Strip whitespace
        result_df["Location ID"] = result_df["Location ID"].astype(str).str.strip()
        result_df["Investigation"] = result_df["Investigation"].astype(str).str.strip()

        return result_df

    except FileNotFoundError:
        logger.warning(f"⚠️ Location Details CSV not found: {location_csv}")
        return pd.DataFrame()
    except Exception as e:
        logger.warning(f"⚠️ Failed to load location details: {str(e)}")
        return pd.DataFrame()


def _add_investigation_column(
    csv_data: pd.DataFrame,
    location_details: pd.DataFrame,
    fallback_name: str,
) -> pd.DataFrame:
    """
    Add Investigation column to CSV data by joining with Location Details.

    Joins the CSV data with location details based on Location ID to add
    an Investigation column. Uses fallback name for missing or unmatched
    Location IDs.

    Args:
        csv_data: Data from single CSV source (must have 'Location ID' column)
        location_details: DataFrame with 'Location ID' and 'Investigation' columns
        fallback_name: Default investigation name for missing/unmatched IDs

    Returns:
        pd.DataFrame with new 'Investigation' column added
    """
    if location_details.empty or "Location ID" not in csv_data.columns:
        # No location details or no Location ID column - use fallback
        result = csv_data.copy()
        result["Investigation"] = fallback_name
        return result

    # Merge with location details
    result = csv_data.merge(
        location_details,
        on="Location ID",
        how="left",
    )

    # Fill missing investigation names with fallback
    result["Investigation"] = result["Investigation"].fillna(fallback_name)

    return result


def _generate_test_type_checkbox_html(test_type_info: List[Dict[str, Any]]) -> str:
    """
    Generate custom HTML/CSS/JavaScript for test type checkboxes.

    Creates interactive checkboxes positioned directly below the investigations legend,
    matching the exact styling of Plotly's native legend. Each checkbox controls
    visibility of corresponding test type traces in the Plotly chart.

    Args:
        test_type_info: List of dicts with keys:
            - name: Clean test type name (e.g., "Consolidation")
            - symbol: Plotly marker symbol (e.g., "circle", "square")
            - legendgroup: Legend group identifier for Plotly traces

    Returns:
        HTML string containing styled checkboxes and JavaScript toggle logic
    """
    # Start building HTML with Plotly legend-matching styles
    checkbox_html = """
<div id="testTypeCheckboxes" style="
    position: fixed;
    left: 50px;
    top: 80px;
    background: rgb(255, 255, 255);
    border: 1px solid rgba(128, 128, 128, 0.3);
    border-radius: 4px;
    padding: 8px;
    font-family: Arial, sans-serif;
    font-size: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    min-width: 120px;
    z-index: 1000;
">
    <div style="font-weight: normal; margin-bottom: 4px; font-size: 11px; font-family: 'Arial Bold', sans-serif; color: rgb(42, 63, 95);">
        Test Types
    </div>
"""

    # Add checkbox for each test type
    for i, test_info in enumerate(test_type_info):
        test_name = test_info["name"]
        symbol = test_info["symbol"]
        legendgroup = test_info["legendgroup"]

        # Convert Plotly symbol to Unicode/CSS representation
        # Complete mapping for all test type markers
        symbol_map = {
            "circle": "●",
            "square": "■",
            "triangle-up": "▲",
            "triangle-down": "▼",
            "diamond": "◆",
            "pentagon": "⬟",
            "star": "★",
            "x": "✕",
            "cross": "✚",
            "hexagon": "⬢",
            "triangle-right": "▶",
            "triangle-left": "◀",
        }
        symbol_display = symbol_map.get(symbol, "●")  # Default to circle if not found

        checkbox_html += f"""
    <div style="margin: 2px 0; display: flex; align-items: center;">
        <input type="checkbox" 
               id="testType_{i}" 
               data-legendgroup="{legendgroup}"
               checked
               style="margin-right: 6px; cursor: pointer; width: 12px; height: 12px;">
        <label for="testType_{i}" style="cursor: pointer; display: flex; align-items: center; user-select: none; font-size: 10px; color: rgb(42, 63, 95);">
            <span style="margin-right: 4px; color: gray; font-size: 10px;">{symbol_display}</span>
            <span>{test_name}</span>
        </label>
    </div>
"""

    # Close container div and add JavaScript with dynamic positioning
    checkbox_html += """
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // Get reference to Plotly div
    var plotDiv = document.querySelector('.plotly-graph-div');
    
    // Add event listeners to all checkboxes
    var checkboxes = document.querySelectorAll('#testTypeCheckboxes input[type="checkbox"]');
    
    checkboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            var legendGroup = this.getAttribute('data-legendgroup');
            var isChecked = this.checked;
            
            // Find all traces with matching legendgroup
            var update = {visible: isChecked};
            var traceIndices = [];
            
            plotDiv.data.forEach(function(trace, idx) {
                if (trace.legendgroup === legendGroup) {
                    traceIndices.push(idx);
                }
            });
            
            // Update trace visibility
            if (traceIndices.length > 0) {
                Plotly.restyle(plotDiv, 'visible', isChecked, traceIndices);
            }
        });
    });
});
</script>
"""

    return checkbox_html


def generate_investigation_series_plot(
    formation_name: str,
    csv_dict: Dict[str, pd.DataFrame],
    parameter_mappings: pd.DataFrame,
    parameter_display_name: str,
    output_folder: Path,
    location_details: pd.DataFrame,
    fallback_investigation_name: str,
    filter_column: Optional[str] = None,
) -> None:
    """
    Generate plot with investigation-based coloring and test-type shapes.

    Creates scatter plot where:
    - Colors represent different investigations (rotating palette)
    - Markers/shapes represent different test types (from CONFIG)
    - Each data point is colored by its investigation source

    Args:
        formation_name: Geological formation name
        csv_dict: Dict mapping CSV names to DataFrames
        parameter_mappings: Parameter mapping DataFrame
        parameter_display_name: Display name for axis labels
        output_folder: Output directory Path
        location_details: DataFrame with Location ID -> Investigation mapping
        fallback_investigation_name: Default name for missing investigations
        filter_column: Column name to filter outliers (e.g., "is_outlier", "is_manual_outlier")
                      If None, no filtering is applied

    Output:
        Saves PNG: {output_folder}/{formation_name_sanitized}.png
    """
    logger.info(
        f"🎨 Generating investigation-series plot for formation: {formation_name}"
    )

    # === CONFIGURATION EXTRACTION ===
    fig_width = CONFIG["plotting"]["figure"]["width"]
    fig_height = CONFIG["plotting"]["figure"]["height"]
    fig_dpi = CONFIG["plotting"]["figure"]["dpi"]

    marker_edgecolors = CONFIG["markers"]["edgecolors"]
    marker_linewidths = CONFIG["markers"]["linewidths"]

    x_label_position = CONFIG["axes"]["x_label_position"]
    x_label_size = CONFIG["axes"]["x_label_size"]
    x_label_weight = CONFIG["axes"]["x_label_weight"]
    y_label = CONFIG["axes"]["y_label"]
    y_label_size = CONFIG["axes"]["y_label_size"]
    y_label_weight = CONFIG["axes"]["y_label_weight"]
    x_limit_left = CONFIG["axes"]["x_limit_left"]
    y_margin = CONFIG["axes"]["y_margin"]
    invert_y = CONFIG["axes"]["invert_y"]

    grid_enabled = CONFIG["axes"]["grid"]
    grid_which = CONFIG["axes"]["grid_which"]
    grid_style = CONFIG["axes"]["grid_style"]
    grid_width = CONFIG["axes"]["grid_width"]
    grid_color = CONFIG["axes"]["grid_color"]

    legend_location = CONFIG["legend"]["location"]
    legend_edgecolor = CONFIG["legend"]["edgecolor"]
    legend_ncol = CONFIG["legend"].get("ncol", 1)

    save_bbox_inches = CONFIG["save"]["bbox_inches"]

    investigation_colors = CONFIG["investigation_series"]["investigation_colors"]

    # === FIGURE INITIALIZATION ===
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    # === DATA COLLECTION ===
    all_parameter_values = []
    all_depth_values = []

    # Collect all investigations first to create color mapping
    all_investigations = set()

    # First pass: collect data with investigation info
    csv_data_with_investigations = {}

    for csv_name, df in csv_dict.items():
        # Find parameter column
        matching_mappings = parameter_mappings[
            parameter_mappings["csv_file"] == csv_name
        ]
        if matching_mappings.empty:
            continue

        column_name = matching_mappings["column_name"].iloc[0]
        if column_name not in df.columns or "Top Depth" not in df.columns:
            continue

        # Apply outlier filtering based on filter_column
        if filter_column and filter_column in df.columns:
            df_filtered = df[~df[filter_column]].copy()
        else:
            df_filtered = df.copy()

        # Add investigation column
        df_with_inv = _add_investigation_column(
            df_filtered, location_details, fallback_investigation_name
        )

        csv_data_with_investigations[csv_name] = {
            "df": df_with_inv,
            "column_name": column_name,
        }

        # Collect unique investigations
        all_investigations.update(df_with_inv["Investigation"].unique())

    # Create investigation color mapping
    investigation_color_map = create_investigation_color_mapping(
        list(all_investigations), investigation_colors
    )

    # === PLOTTING SECTION ===
    # Sort by test type order
    sorted_csv_items = sorted(
        csv_data_with_investigations.items(),
        key=lambda x: CONFIG["csv_source_settings"].get(x[0], {}).get("order", 999),
    )

    # Track legend entries to avoid duplicates
    plotted_investigations = set()

    # === PLOT DATA POINTS BY TEST TYPE ===
    for csv_name, data_info in sorted_csv_items:
        df_with_inv = data_info["df"]
        column_name = data_info["column_name"]

        # Get test type settings
        test_type_settings = CONFIG["csv_source_settings"].get(
            csv_name, CONFIG["default_source_settings"]
        )

        if not test_type_settings["plotted"]:
            continue

        marker_style = test_type_settings["marker"]
        marker_size = test_type_settings["marker_size"]
        plot_alpha = test_type_settings["alpha"]
        # Get marker thickness if specified (for 'x', '+' markers)
        marker_thickness = test_type_settings.get("marker_thickness", marker_linewidths)

        # Plot each investigation within this test type
        for investigation in sorted(df_with_inv["Investigation"].unique()):
            inv_data = df_with_inv[df_with_inv["Investigation"] == investigation]

            param_values = inv_data[column_name].values
            depth_values = inv_data["Top Depth"].values

            if len(param_values) == 0:
                continue

            # Get investigation color
            inv_color = investigation_color_map[investigation]

            # Track investigations for legend
            if investigation not in plotted_investigations:
                plotted_investigations.add(investigation)

            # Plot scatter points
            plot_points = test_type_settings.get("plot_points", True)
            if plot_points:
                ax.scatter(
                    param_values,
                    depth_values,
                    c=inv_color,
                    marker=marker_style,
                    s=marker_size,
                    alpha=plot_alpha,
                    edgecolors=marker_edgecolors,
                    linewidths=marker_thickness,
                )

            all_parameter_values.extend(param_values)
            all_depth_values.extend(depth_values)

    # === ADD INVESTIGATION COLOR LEGEND (with circle markers) ===
    for investigation in sorted(plotted_investigations):
        inv_color = investigation_color_map[investigation]
        ax.scatter(
            [],
            [],
            c=inv_color,
            marker="o",  # Use circle marker for investigation colors
            s=100,  # Standard legend marker size
            alpha=0.8,
            edgecolors=marker_edgecolors,
            linewidths=marker_linewidths,
            label=f"{investigation}",
        )

    # === ADD SHAPE LEGEND FOR TEST TYPES ===
    if CONFIG["investigation_series"]["legend"]["show_test_type_shapes"]:
        for csv_name, data_info in sorted_csv_items:
            test_type_settings = CONFIG["csv_source_settings"].get(
                csv_name, CONFIG["default_source_settings"]
            )

            if not test_type_settings["plotted"]:
                continue

            test_plots_points = test_type_settings.get("plot_points", True)
            if not test_plots_points:
                continue  # Skip test types that don't plot points

            marker_style = test_type_settings["marker"]
            marker_size = test_type_settings["marker_size"]
            # Get marker thickness if specified (for 'x', '+' markers)
            marker_thickness = test_type_settings.get(
                "marker_thickness", marker_linewidths
            )
            clean_test_name = csv_name.replace(" by Geology.csv", "").replace(
                ".csv", ""
            )

            # Add invisible marker with label for shape legend
            ax.scatter(
                [],
                [],
                c="gray",
                marker=marker_style,
                s=marker_size,
                alpha=0.7,
                edgecolors=marker_edgecolors,
                linewidths=marker_thickness,
                label=f"{clean_test_name} (shape)",
            )

    # === AXIS CONFIGURATION ===
    if all_parameter_values and all_depth_values:
        x_max = max(all_parameter_values) * 1.1
        y_max = max(all_depth_values) + y_margin

        ax.set_xlim(left=x_limit_left, right=x_max)

        # Set y-axis limits based on invert_y setting
        if invert_y:
            ax.set_ylim(top=0, bottom=y_max)
        else:
            ax.set_ylim(bottom=0, top=y_max)

    # Set axis labels
    ax.set_xlabel(
        parameter_display_name,
        fontsize=x_label_size,
        weight=x_label_weight,
    )
    ax.set_ylabel(y_label, fontsize=y_label_size, weight=y_label_weight)

    # Add plot title
    ax.set_title(formation_name, fontsize=16, weight="bold", pad=20)

    # Position X-axis at top
    if x_label_position == "top":
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position("top")

    # Grid
    if grid_enabled:
        ax.grid(
            which=grid_which,
            linestyle=grid_style,
            linewidth=grid_width,
            color=grid_color,
        )

    # === LEGEND ===
    legend_fixed_width = CONFIG["legend"].get("fixed_width", False)

    # Get legend handles and labels
    handles, labels = ax.get_legend_handles_labels()
    num_entries = len(labels)

    # Calculate optimal number of columns
    optimal_ncol = min(3, max(1, num_entries // 2))
    legend_fontsize = 8

    if legend_fixed_width:
        # Make legend match axes width exactly
        fig.canvas.draw()
        bbox_expand = (0, -0.15, 1, 0)

        legend = ax.legend(
            loc="lower left",
            bbox_to_anchor=bbox_expand,
            bbox_transform=ax.transAxes,
            edgecolor=legend_edgecolor,
            framealpha=0.9,
            ncol=optimal_ncol,
            mode="expand",
            borderaxespad=0,
            labelspacing=0.5,
            borderpad=0.5,
            fontsize=legend_fontsize,
            columnspacing=1.0,
        )
    else:
        legend = ax.legend(
            loc=legend_location,
            bbox_to_anchor=(0.5, -0.15),
            edgecolor=legend_edgecolor,
            framealpha=0.9,
            ncol=optimal_ncol,
            fontsize=legend_fontsize,
            labelspacing=0.5,
            borderpad=0.5,
        )

    # === SAVE ===
    output_folder.mkdir(parents=True, exist_ok=True)

    sanitized_name = (
        formation_name.replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
    )
    output_path = output_folder / f"{sanitized_name}.png"

    fig.savefig(output_path, dpi=fig_dpi, bbox_inches=save_bbox_inches)
    plt.close(fig)

    logger.info(f"✅ Saved investigation-series plot: {output_path}")


def generate_investigation_series_plot_plotly(
    formation_name: str,
    csv_dict: Dict[str, pd.DataFrame],
    parameter_mappings: pd.DataFrame,
    parameter_display_name: str,
    output_folder: Path,
    location_details: pd.DataFrame,
    fallback_investigation_name: str,
    outlier_results: Optional[Dict[str, Dict[str, Any]]] = None,
    mark_outliers: bool = True,
) -> None:
    """
    Generate interactive Plotly HTML version of depth vs parameter investigation plot.

    Creates an interactive HTML scatter plot with:
    - Investigation-based coloring (13-color palette rotation)
    - Test-type marker shapes (from CONFIG csv_source_settings)
    - Hover tooltips showing: Depth, Parameter, Location ID, Investigation name
    - Red circles highlighting detected outliers
    - Dual legend system (investigations + test types)
    - X-axis: Parameter value (top), Y-axis: Depth (m) - inverted

    Args:
        formation_name: Geological formation name
        csv_dict: Dict mapping CSV names to DataFrames
        parameter_mappings: Parameter mapping DataFrame
        parameter_display_name: Display name for axis labels
        output_folder: Output directory Path
        location_details: DataFrame with Location ID -> Investigation mapping
        fallback_investigation_name: Default name for missing investigations
        outlier_results: Optional outlier detection results
        mark_outliers: If True, marks outliers with red circles

    Output:
        Saves HTML: {output_folder}/{formation_name_sanitized}.html
    """
    logger.info(
        f"🎨 Generating interactive Plotly HTML plot for formation: {formation_name}"
    )

    # === CONFIGURATION EXTRACTION ===
    investigation_colors = CONFIG["investigation_series"]["investigation_colors"]
    param_name = CONFIG["parameter"]["name"]
    param_display_name = CONFIG["parameter"]["display_name"]
    force_circle_markers = CONFIG["investigation_series"]["legend"][
        "force_circle_markers"
    ]

    # === DATA COLLECTION ===
    # Collect all investigations first to create color mapping
    all_investigations = set()
    csv_data_with_investigations = {}

    for csv_name, df in csv_dict.items():
        # Find parameter column
        param_mappings = parameter_mappings[
            (parameter_mappings["csv_file"] == csv_name)
            & (parameter_mappings["parameter"] == param_name)
        ]

        if param_mappings.empty:
            continue

        param_column = param_mappings["column_name"].iloc[0]

        if param_column not in df.columns:
            continue

        # Handle outliers - keep all data but mark outliers
        if outlier_results and csv_name in outlier_results:
            outlier_indices = outlier_results[csv_name]["outlier_indices"]
            df_filtered = df.copy()
            df_filtered["is_outlier_plot"] = df_filtered.index.isin(outlier_indices)
        else:
            df_filtered = df.copy()
            df_filtered["is_outlier_plot"] = False

        # Add investigation column
        df_with_inv = _add_investigation_column(
            df_filtered, location_details, fallback_investigation_name
        )

        csv_data_with_investigations[csv_name] = {
            "df": df_with_inv,
            "param_column": param_column,
        }

        all_investigations.update(df_with_inv["Investigation"].unique())

    # Create investigation color mapping
    investigation_color_map = create_investigation_color_mapping(
        list(all_investigations), investigation_colors
    )

    # === CALCULATE INVESTIGATION COUNTS ===
    # Count total data points per investigation across all CSV sources
    investigation_counts = {}
    for csv_name, data_info in csv_data_with_investigations.items():
        df_with_inv = data_info["df"]
        # Count points per investigation in this CSV (excluding outliers if needed)
        for investigation in df_with_inv["Investigation"].unique():
            if investigation not in investigation_counts:
                investigation_counts[investigation] = 0
            # Count all points (both regular and outliers)
            investigation_counts[investigation] += len(
                df_with_inv[df_with_inv["Investigation"] == investigation]
            )

    # === PLOTLY MARKER SYMBOL MAPPING ===
    # Map matplotlib markers to Plotly symbols
    marker_symbol_map = {
        "o": "circle",
        "s": "square",
        "^": "triangle-up",
        "v": "triangle-down",
        "d": "diamond",
        "D": "diamond",
        "p": "pentagon",
        "*": "star",
        "x": "x",
        "+": "cross",
        "h": "hexagon",
        ">": "triangle-right",
        "<": "triangle-left",
    }

    # === CREATE PLOTLY FIGURE ===
    fig = go.Figure()

    # Sort by test type order
    sorted_csv_items = sorted(
        csv_data_with_investigations.items(),
        key=lambda x: CONFIG["csv_source_settings"].get(x[0], {}).get("order", 999),
    )

    # Track which investigations have been added to legend (color-only legend)
    legend_investigations = set()

    # Track test types for checkbox generation
    test_types_in_formation = set()

    # Collect outlier data grouped by test type AND investigation (for later trace generation)
    # Structure: {csv_name: {investigation: {"x": [], "y": [], "hover_text": [], "color": rgba, "marker_symbol": symbol}}}
    outliers_by_test_type_and_investigation = {}

    # === ADD DATA TRACES ===
    for csv_name, data_info in sorted_csv_items:
        df_with_inv = data_info["df"]
        param_column = data_info["param_column"]

        # Get test type settings
        test_type_settings = CONFIG["csv_source_settings"].get(
            csv_name, CONFIG["default_source_settings"]
        )

        if not test_type_settings["plotted"]:
            continue

        marker_style = test_type_settings["marker"]
        marker_size = test_type_settings["marker_size"] / 5  # Scale for Plotly
        plot_alpha = test_type_settings["alpha"]

        # Convert matplotlib marker to Plotly symbol
        plotly_symbol = marker_symbol_map.get(marker_style, "circle")
        clean_test_name = csv_name.replace(" by Geology.csv", "").replace(".csv", "")

        # Track test type for checkbox generation
        test_types_in_formation.add(clean_test_name)

        # Plot each investigation within this test type
        for investigation in sorted(df_with_inv["Investigation"].unique()):
            inv_data = df_with_inv[df_with_inv["Investigation"] == investigation]

            # Separate regular points from outliers
            regular_data = inv_data[~inv_data["is_outlier_plot"]]
            outlier_data = inv_data[inv_data["is_outlier_plot"]]

            inv_color = investigation_color_map[investigation]

            # Convert hex color to rgba for Plotly
            # Remove '#' and convert to RGB
            hex_color = inv_color.lstrip("#")
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            rgba_color = f"rgba({r},{g},{b},{plot_alpha})"

            # Add regular (non-outlier) points
            if len(regular_data) > 0:
                # Show legend only for FIRST trace of each investigation (color-only legend)
                # If force_circle_markers is True, we hide real traces from legend and use dummy circle traces
                show_legend_inv = (
                    investigation not in legend_investigations
                    and not force_circle_markers
                )

                # Create hover text
                hover_text = []
                for idx, row in regular_data.iterrows():
                    hover_text.append(
                        f"<b>{investigation}</b><br>"
                        f"Location ID: {row.get('Location ID', 'N/A')}<br>"
                        f"Depth: {row['Top Depth']:.2f} m<br>"
                        f"{param_display_name}: {row[param_column]:.2f}<br>"
                        f"Test Type: {clean_test_name}"
                    )

                # CRITICAL: Group by INVESTIGATION (color) not test type
                # This creates a color-only legend where clicking toggles ALL markers of that color
                # Legend includes count of data points (n=x)
                legend_name = (
                    f"{investigation} (n={investigation_counts[investigation]})"
                )

                fig.add_trace(
                    go.Scatter(
                        x=regular_data[param_column],
                        y=regular_data["Top Depth"],
                        mode="markers",
                        marker=dict(
                            symbol=plotly_symbol,  # Different marker shapes within same investigation
                            size=marker_size,
                            color=rgba_color,
                            line=dict(color="black", width=0.5),
                        ),
                        name=legend_name,  # Investigation name with count in legend
                        legendgroup=investigation,  # Group by investigation (COLOR)
                        showlegend=show_legend_inv,  # Show only first trace per investigation (or hide if using dummy circles)
                        hovertext=hover_text,
                        hoverinfo="text",
                        customdata=[[clean_test_name]]
                        * len(regular_data),  # Store test type for filtering
                    )
                )

                if show_legend_inv or force_circle_markers:
                    legend_investigations.add(investigation)

            # Collect outlier points grouped by test type AND investigation (for later trace generation)
            if mark_outliers and len(outlier_data) > 0:
                # Initialize CSV name in outlier dict if not exists
                if csv_name not in outliers_by_test_type_and_investigation:
                    outliers_by_test_type_and_investigation[csv_name] = {}

                # Initialize investigation within this test type if not exists
                if (
                    investigation
                    not in outliers_by_test_type_and_investigation[csv_name]
                ):
                    outliers_by_test_type_and_investigation[csv_name][investigation] = {
                        "x": [],
                        "y": [],
                        "hover_text": [],
                        "color": rgba_color,  # Store investigation color
                        "marker_symbol": plotly_symbol,  # Store test type marker symbol
                    }

                # Add outlier data to this test type + investigation combination
                outliers_by_test_type_and_investigation[csv_name][investigation][
                    "x"
                ].extend(outlier_data[param_column].tolist())
                outliers_by_test_type_and_investigation[csv_name][investigation][
                    "y"
                ].extend(outlier_data["Top Depth"].tolist())

                # Create hover text for these outliers
                for idx, row in outlier_data.iterrows():
                    outlier_hover_text_item = (
                        f"<b>OUTLIER - {investigation}</b><br>"
                        f"Location ID: {row.get('Location ID', 'N/A')}<br>"
                        f"Depth: {row['Top Depth']:.2f} m<br>"
                        f"{param_display_name}: {row[param_column]:.2f}<br>"
                        f"Test Type: {clean_test_name}"
                    )
                    outliers_by_test_type_and_investigation[csv_name][investigation][
                        "hover_text"
                    ].append(outlier_hover_text_item)

    # === ADD DUMMY CIRCLE LEGEND TRACES (IF ENABLED) ===
    # When force_circle_markers is True, add invisible dummy traces with circle markers
    # These traces only show in the legend to provide consistent circle symbols
    # The real data traces (with actual marker shapes) are hidden from legend but still visible and grouped
    if force_circle_markers:
        for investigation in sorted(legend_investigations):
            inv_color = investigation_color_map[investigation]
            # Convert hex color to rgba
            hex_color = inv_color.lstrip("#")
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            rgba_color = f"rgba({r},{g},{b},1.0)"  # Full opacity for legend

            # Add invisible dummy trace with circle marker
            # This trace appears ONLY in the legend and controls visibility of all real traces in its legendgroup
            # Legend includes count of data points (n=x)
            legend_name = f"{investigation} (n={investigation_counts[investigation]})"

            fig.add_trace(
                go.Scatter(
                    x=[None],  # No data - invisible on plot
                    y=[None],  # No data - invisible on plot
                    mode="markers",
                    marker=dict(
                        symbol="circle",  # Force circle for legend
                        size=10,  # Match outlier marker size for consistency
                        color=rgba_color,
                        line=dict(color="black", width=0.5),
                    ),
                    name=legend_name,  # Investigation name with count in legend
                    legendgroup=investigation,  # Same legendgroup as real traces - clicking toggles ALL
                    showlegend=True,  # This is the ONLY trace that shows in legend for this investigation
                    hoverinfo="skip",  # No hover for dummy trace
                )
            )

        # === ADD TOTAL COUNT TRACE (TEXT-ONLY LEGEND ENTRY) ===
        # Add a trace that only appears in legend to show total data point count
        total_count = sum(investigation_counts.values())
        fig.add_trace(
            go.Scatter(
                x=[None],  # No data - invisible on plot
                y=[None],  # No data - invisible on plot
                mode="text",  # Text mode - no marker displayed
                name=f"<b>Total n={total_count}</b>",  # Bold total count text
                showlegend=True,  # Show in legend
                hoverinfo="skip",  # No hover
                legendgroup="total_count",  # Separate group
                legendrank=9999,  # Force to bottom of legend
            )
        )

    # === ADD OUTLIER TRACES (GROUPED BY TEST TYPE AND INVESTIGATION) ===
    # Outliers use test-type-specific marker symbols and are controlled by test type checkboxes
    # Show single "Outlier" legend entry but maintain test type filtering
    if mark_outliers:
        outlier_legend_shown = False
        for (
            csv_name,
            investigations_dict,
        ) in outliers_by_test_type_and_investigation.items():
            # Get clean test name for customdata
            clean_test_name = csv_name.replace(" by Geology.csv", "").replace(
                ".csv", ""
            )

            for investigation, outlier_info in investigations_dict.items():
                if len(outlier_info["x"]) > 0:
                    # Use the test type's marker symbol for outliers
                    marker_symbol = outlier_info["marker_symbol"]

                    fig.add_trace(
                        go.Scatter(
                            x=outlier_info["x"],
                            y=outlier_info["y"],
                            mode="markers",
                            marker=dict(
                                symbol=marker_symbol,  # Use test type marker symbol
                                size=10,  # Fixed size for outliers
                                color="red",  # Red color for visual distinction
                                line=dict(color="darkred", width=1),
                            ),
                            name="Outlier",
                            legendgroup="Outlier",  # Separate legendgroup for outliers
                            showlegend=not outlier_legend_shown,  # Show legend only once
                            hovertext=outlier_info["hover_text"],
                            hoverinfo="text",
                            customdata=[[clean_test_name]]
                            * len(
                                outlier_info["x"]
                            ),  # Store test type for checkbox filtering
                            legendrank=2000,  # Push outliers to very bottom
                        )
                    )
                    outlier_legend_shown = True

    # === LAYOUT CONFIGURATION ===
    fig.update_layout(
        title=dict(text=formation_name, font=dict(size=14, family="Arial"), x=0.5),
        xaxis=dict(
            title=param_display_name,
            side="top",  # X-axis at top for depth plots
            showgrid=True,
            gridwidth=0.5,
            gridcolor="rgba(128,128,128,0.3)",
        ),
        yaxis=dict(
            title="Depth (m)",
            autorange="reversed",  # Invert Y-axis (depth increases downward)
            showgrid=True,
            gridwidth=0.5,
            gridcolor="rgba(128,128,128,0.3)",
        ),
        hovermode="closest",
        # Legend shows only investigation colors - clicking toggles all markers of that color
        legend=dict(
            title=dict(text="Investigations", font=dict(size=11, family="Arial Bold")),
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            font=dict(size=10),
            groupclick="togglegroup",  # Toggles ALL traces in legendgroup (all points of same investigation color)
            itemdoubleclick="toggle",
        ),
        plot_bgcolor="white",
        width=1200,  # Increased width to accommodate left margin without squishing
        height=800,
        margin=dict(
            l=300, r=50, t=50, b=50
        ),  # Add left margin for test type checkboxes
    )

    # === CUSTOM HTML CHECKBOX GENERATION FOR TEST TYPES ===
    # Generate checkboxes for each test type (marker shape) to allow individual filtering
    # Map test types to their corresponding Plotly symbols
    marker_symbol_map_py = {
        "o": "circle",
        "^": "triangle-up",
        "s": "square",
        "d": "diamond",
        "v": "triangle-down",
        "D": "diamond",
        "p": "pentagon",
        "*": "star",
        "x": "x",
        "+": "cross",
        "h": "hexagon",
        ">": "triangle-right",
        "<": "triangle-left",
    }

    # Build a mapping of test type names to their marker symbols
    test_type_to_symbol = {}
    for csv_name in sorted(csv_data_with_investigations.keys()):
        test_type_settings = CONFIG["csv_source_settings"].get(
            csv_name, CONFIG["default_source_settings"]
        )
        if test_type_settings["plotted"]:
            clean_test_name = csv_name.replace(" by Geology.csv", "").replace(
                ".csv", ""
            )
            marker_style = test_type_settings["marker"]
            plotly_symbol = marker_symbol_map_py.get(marker_style, "circle")
            if clean_test_name in test_types_in_formation:
                test_type_to_symbol[clean_test_name] = plotly_symbol

    test_type_checkboxes = []
    for test_type in sorted(test_types_in_formation):
        symbol = test_type_to_symbol.get(test_type, "circle")
        # Convert Plotly symbol to Unicode/CSS representation
        symbol_map = {
            "circle": "●",
            "square": "■",
            "triangle-up": "▲",
            "triangle-down": "▼",
            "diamond": "◆",
            "pentagon": "⬟",
            "star": "★",
            "x": "✕",
            "cross": "+",
            "hexagon": "⬡",
            "triangle-right": "▶",
            "triangle-left": "◀",
        }
        symbol_display = symbol_map.get(symbol, "●")
        test_type_checkboxes.append(
            f'    <div style="margin: 2px 0; display: flex; align-items: center;">\n'
            f'        <input type="checkbox" class="test-type-checkbox" '
            f'data-symbol="{symbol}" checked '
            f'style="margin-right: 6px; cursor: pointer; width: 12px; height: 12px;">\n'
            f'        <label style="cursor: pointer; display: flex; align-items: center; user-select: none; font-size: 10px; color: rgb(42, 63, 95);">\n'
            f'            <span style="margin-right: 4px; color: gray; font-size: 10px;">{symbol_display}</span>\n'
            f"            <span>{test_type}</span>\n"
            f"        </label>\n"
            f"    </div>"
        )

    checkbox_html = f"""
<div id="testTypeCheckboxes" style="
    position: fixed;
    left: 50px;
    top: 80px;
    background: rgb(255, 255, 255);
    border: 1px solid rgba(128, 128, 128, 0.3);
    border-radius: 4px;
    padding: 8px;
    font-family: Arial, sans-serif;
    font-size: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    min-width: 120px;
    z-index: 1000;
">
    <div style="font-weight: normal; margin-bottom: 4px; font-size: 11px; font-family: 'Arial Bold', sans-serif; color: rgb(42, 63, 95);">
        Test Types
    </div>
{''.join(test_type_checkboxes)}
</div>
    <script>
        document.querySelectorAll('.test-type-checkbox').forEach(checkbox => {{
            checkbox.addEventListener('change', function() {{
                const symbol = this.getAttribute('data-symbol');
                const isChecked = this.checked;
                
                // Find all traces with this marker symbol
                const plotDiv = document.querySelector('.plotly-graph-div');
                const data = plotDiv.data;
                
                // Update visibility for all traces with matching symbol
                const updates = {{}};
                data.forEach((trace, idx) => {{
                    if (trace.marker && trace.marker.symbol === symbol) {{
                        if (!updates[idx]) updates[idx] = {{}};
                        updates[idx]['visible'] = isChecked;
                    }}
                }});
                
                // Apply all updates at once
                Object.keys(updates).forEach(idx => {{
                    Plotly.restyle(plotDiv, updates[idx], parseInt(idx));
                }});
            }});
        }});
    </script>
    """

    # Add custom JavaScript to slow down double-click detection
    config = {
        "doubleClickDelay": 500,  # 500ms delay (default is 300ms)
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    }

    # === SAVE HTML ===
    output_folder.mkdir(parents=True, exist_ok=True)

    sanitized_name = (
        formation_name.replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
    )
    output_path = output_folder / f"{sanitized_name}.html"

    # Save the HTML file with custom checkboxes
    html_content = fig.to_html(config=config, include_plotlyjs="cdn")

    # Insert checkbox HTML before closing body tag
    html_content = html_content.replace("</body>", f"{checkbox_html}</body>")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"✅ Saved interactive Plotly HTML plot: {output_path}")


def generate_investigation_series_plots(
    formation_groups: Dict[str, Dict[str, pd.DataFrame]],
    parameter_mappings: pd.DataFrame,
    parameter_name: str,
    parameter_display_name: str,
    output_base_folder: str,
) -> None:
    """
    Generate investigation-series plots for all formations (orchestrator).

    Creates plots where colors represent investigations and shapes represent
    test types. Generates both with-outliers and without-outliers versions.

    Args:
        formation_groups: Dict mapping formations to CSV data dicts
        parameter_mappings: Parameter mapping DataFrame
        parameter_name: Technical parameter name
        parameter_display_name: Display name for axes
        output_base_folder: Base output folder path
    """
    if not CONFIG["investigation_series"]["enabled"]:
        logger.info("⏭️ Investigation-series plots disabled in CONFIG - skipping")
        return

    logger.info(
        f"🚀 Generating investigation-series plots for {len(formation_groups)} formations"
    )

    # Load location details
    csv_folder = CONFIG["parameter"]["csv_source_folder"]
    location_csv_name = CONFIG["investigation_tracking"]["location_details_csv"]
    per_inv_config = CONFIG["investigation_tracking"]["per_investigation_plots"]
    location_id_variants = per_inv_config["location_id_column_variants"]
    investigation_variants = per_inv_config["investigation_column_variants"]

    location_details = _load_location_details_for_plotting(
        csv_folder,
        location_csv_name,
        location_id_variants,
        investigation_variants,
    )

    fallback_name = per_inv_config["fallback_investigation_name"]

    # Setup output folders
    param_output_folder = Path(output_base_folder) / parameter_name
    inv_series_folder_base = (
        param_output_folder / CONFIG["investigation_series"]["output_folder"]
    )

    with_outliers_folder = (
        inv_series_folder_base
        / CONFIG["outlier_detection"]["output_folders"]["with_outliers"]
    )
    without_outliers_folder = (
        inv_series_folder_base
        / CONFIG["outlier_detection"]["output_folders"]["without_outliers"]
    )

    # Folder for manually identified outliers excluded
    manually_excluded_folder = (
        inv_series_folder_base / CONFIG["manual_outlier_exclusion"]["output_folder"]
    )

    # Separate folder for HTML interactive plots
    html_outliers_folder = (
        inv_series_folder_base
        / "html_interactive"
        / CONFIG["outlier_detection"]["output_folders"]["with_outliers"]
    )

    logger.info("📂 Output folders:")
    logger.info(f"   With outliers: {with_outliers_folder}")
    logger.info(f"   Without outliers: {without_outliers_folder}")
    logger.info(f"   Manually identified excluded: {manually_excluded_folder}")
    logger.info(f"   HTML interactive: {html_outliers_folder}")

    # Generate plots
    plot_count = 0

    for formation_name in sorted(formation_groups.keys()):
        csv_dict = formation_groups[formation_name]

        logger.info(f"\n📊 Processing formation: {formation_name}")

        # Detect outliers
        outlier_results = detect_outliers_per_csv(
            csv_dict,
            parameter_mappings,
            formation_name,
            CONFIG["outlier_detection"],
        )

        # Check output control settings
        output_control = extract_output_control_config()

        # Generate WITH outliers plot
        if should_generate_plot(
            "investigation_series_plots_with_outliers", output_control
        ):
            generate_investigation_series_plot(
                formation_name,
                csv_dict,
                parameter_mappings,
                parameter_display_name,
                with_outliers_folder,
                location_details,
                fallback_name,
                filter_column=None,  # No filtering
            )
            plot_count += 1

        # Generate WITHOUT IQR outliers plot
        if should_generate_plot(
            "investigation_series_plots_without_outliers", output_control
        ):
            generate_investigation_series_plot(
                formation_name,
                csv_dict,
                parameter_mappings,
                parameter_display_name,
                without_outliers_folder,
                location_details,
                fallback_name,
                filter_column="is_outlier",  # Filter IQR outliers
            )
            plot_count += 1

        # Generate WITHOUT manually identified outliers plot
        if should_generate_plot(
            "investigation_series_plots_manually_identified", output_control
        ):
            generate_investigation_series_plot(
                formation_name,
                csv_dict,
                parameter_mappings,
                parameter_display_name,
                manually_excluded_folder,
                location_details,
                fallback_name,
                filter_column="is_manual_outlier",  # Filter manually identified outliers
            )
            plot_count += 1

        # Generate Plotly interactive HTML plot (WITH outliers only)
        if should_generate_plot(
            "investigation_series_plots_plotly_with_outliers", output_control
        ):
            generate_investigation_series_plot_plotly(
                formation_name,
                csv_dict,
                parameter_mappings,
                parameter_display_name,
                html_outliers_folder,  # Use separate HTML folder
                location_details,
                fallback_name,
                outlier_results=outlier_results,  # Pass outlier info to mark them
                mark_outliers=True,  # Mark outliers with red circles
            )
            plot_count += 1

    logger.info(f"✅ Generated {plot_count} investigation-series plots")


# ═══════════════════════════════════════════════════════════════════════════
# 📈 PHASE 4: PLOT GENERATION (OLD FORMATION PLOTS - KEPT FOR REFERENCE)
# ═══════════════════════════════════════════════════════════════════════════


def generate_formation_plot(
    formation_name: str,
    csv_dict: Dict[str, pd.DataFrame],
    parameter_mappings: pd.DataFrame,
    parameter_display_name: str,
    output_folder: Path,
    color_mapping: Dict[str, str],
    outlier_results: Optional[Dict[str, Dict[str, Any]]] = None,
) -> None:
    """
    Generate depth vs. parameter scatter plot for a single geological formation.

    Creates a publication-quality scatter plot combining data from multiple CSV sources
    (test types) for the specified geological formation. Each CSV source is assigned
    a unique color from the global color_mapping for consistency across formations.
    Optionally filters outliers based on per-CSV outlier detection results.

    Args:
        formation_name: Geological formation name (e.g., "Gault Clay Formation (Weathered)")
        csv_dict: Dictionary mapping CSV filenames to DataFrames containing formation data
                 Each DataFrame has columns: [Location ID, Top Depth, Geological_Strata, parameter_column]
        parameter_mappings: DataFrame with columns [csv_file, column_name, priority_rank, quality_score]
                          Used to lookup parameter column name for each CSV
        parameter_display_name: Human-readable parameter name with units for axis label
                               (e.g., "Undrained Shear Strength Cu (kPa)")
        output_folder: Path object for output directory
        color_mapping: Global dictionary mapping {csv_name: color_hex} for consistent colors across formations

    Output:
        Saves PNG file: {output_folder}/{formation_name_sanitized}.png
        - Resolution: 300 DPI
        - Aspect ratio: 4:5 (width:height)
        - X-axis: Parameter values (top axis)
        - Y-axis: Depth in meters (inverted, increases downward)
        - Legend: Lists all CSV sources with corresponding colors
        - Grid: Both major and minor grid lines enabled

    Visual Design:
        - Scatter markers: Per-source configuration from CONFIG["csv_source_settings"]
        - Different marker shapes per test type for visual distinction
        - Edge colors: Black (linewidth=0.5)
        - Color assignment: Per-source from CONFIG["csv_source_settings"]
        - Y-axis inverted to show depth increasing downward (geological convention)
        - X-axis at top for readability

    Error Handling:
        - Skips CSVs with missing parameter columns (logs warning)
        - Skips empty DataFrames after filtering nulls
        - Gracefully handles missing depth or parameter data

    Example:
        >>> generate_formation_plot(
        ...     "Gault Clay Formation (Weathered)",
        ...     {"Triaxial Total Stress.csv": df1, "Vane Tests.csv": df2},
        ...     param_mappings,
        ...     "Undrained Shear Strength Cu (kPa)",
        ...     Path("Output/UndrainedShearStrength")
        ... )
        # Creates: Output/UndrainedShearStrength/Gault_Clay_Formation_Weathered.png
    """
    logger.info(f"📈 Generating plot for formation: {formation_name}")

    # === CONFIGURATION EXTRACTION SECTION ===
    # Extract plotting configuration from CONFIG (coordination boundary)
    fig_width = CONFIG["plotting"]["figure"]["width"]
    fig_height = CONFIG["plotting"]["figure"]["height"]
    fig_dpi = CONFIG["plotting"]["figure"]["dpi"]

    x_label_position = CONFIG["plotting"]["axes"]["x_label_position"]
    x_label_size = CONFIG["plotting"]["axes"]["x_label_size"]
    x_label_weight = CONFIG["plotting"]["axes"]["x_label_weight"]
    y_label = CONFIG["plotting"]["axes"]["y_label"]
    y_label_size = CONFIG["plotting"]["axes"]["y_label_size"]
    y_label_weight = CONFIG["plotting"]["axes"]["y_label_weight"]
    x_limit_left = CONFIG["plotting"]["axes"]["x_limit_left"]
    y_margin = CONFIG["plotting"]["axes"]["y_margin"]
    invert_y = CONFIG["plotting"]["axes"]["invert_y"]

    grid_enabled = CONFIG["plotting"]["axes"]["grid"]
    grid_which = CONFIG["plotting"]["axes"]["grid_which"]
    grid_style = CONFIG["plotting"]["axes"]["grid_style"]
    grid_width = CONFIG["plotting"]["axes"]["grid_width"]
    grid_color = CONFIG["plotting"]["axes"]["grid_color"]
    grid_alpha = CONFIG["plotting"]["axes"].get("grid_alpha", 0.3)  # Default to 0.3

    legend_location = CONFIG["plotting"]["legend"]["location"]
    legend_edgecolor = CONFIG["plotting"]["legend"]["edgecolor"]

    save_bbox_inches = CONFIG["plotting"]["save"]["bbox_inches"]

    # === FIGURE INITIALIZATION SECTION ===
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    # === DATA PLOTTING SECTION ===
    # Track overall data ranges for axis limits
    all_parameter_values = []
    all_depth_values = []

    # Plot data from each CSV source with unique color
    for csv_idx, (csv_name, df) in enumerate(csv_dict.items()):
        # === PARAMETER COLUMN LOOKUP SECTION ===
        # Find parameter column name for this CSV
        matching_mappings = parameter_mappings[
            parameter_mappings["csv_file"] == csv_name
        ]

        if matching_mappings.empty:
            logger.warning(f"⚠️ {csv_name}: No parameter mapping found, skipping plot")
            continue

        column_name = matching_mappings["column_name"].iloc[0]

        # === COLUMN VALIDATION SECTION ===
        if column_name not in df.columns:
            logger.warning(
                f"⚠️ {csv_name}: Parameter column '{column_name}' not found, skipping plot"
            )
            continue

        if "Top Depth" not in df.columns:
            logger.warning(f"⚠️ {csv_name}: 'Top Depth' column not found, skipping plot")
            continue

        # === DATA EXTRACTION SECTION ===
        # Extract parameter values and depths (already filtered for nulls in Phase 3)
        # Apply outlier filtering if outlier_results provided
        if outlier_results and csv_name in outlier_results:
            # Filter out outlier indices for this CSV
            outlier_indices = outlier_results[csv_name]["outlier_indices"]
            mask = ~df.index.isin(outlier_indices)
            df_filtered = df[mask]

            outlier_count = outlier_results[csv_name]["outlier_count"]
            logger.debug(
                f"  🔍 {csv_name}: Excluded {outlier_count} outliers, "
                f"{len(df_filtered)}/{len(df)} points remaining"
            )
        else:
            # No filtering - use all data
            df_filtered = df

        param_values = df_filtered[column_name].values
        depth_values = df_filtered["Top Depth"].values

        if len(param_values) == 0:
            logger.debug(f"  {csv_name}: No data points after filtering, skipping")
            continue

        # === COLOR ASSIGNMENT SECTION ===
        # Get color from global mapping for consistent assignment across formations
        color = color_mapping.get(csv_name, "#000000")  # Fallback to black if not found

        # === GET PER-SOURCE MARKER SETTINGS SECTION ===
        # Extract marker settings from csv_source_settings or use defaults
        source_settings = CONFIG["csv_source_settings"].get(
            csv_name, CONFIG["default_source_settings"]
        )

        marker = source_settings.get(
            "marker", CONFIG["default_source_settings"]["marker"]
        )
        marker_size_src = source_settings.get(
            "marker_size", CONFIG["default_source_settings"]["marker_size"]
        )
        marker_alpha_src = source_settings.get(
            "alpha", CONFIG["default_source_settings"]["alpha"]
        )
        legend_name = source_settings.get("legend_name_points", None)

        # === SCATTER PLOT SECTION ===
        # Clean CSV name for legend (remove " by Geology.csv" suffix)
        if legend_name is None:
            display_name = csv_name.replace(" by Geology.csv", "").replace(".csv", "")
        else:
            display_name = legend_name

        ax.scatter(
            param_values,
            depth_values,
            c=color,
            marker=marker,
            s=marker_size_src,
            alpha=marker_alpha_src,
            edgecolors="black",
            linewidths=0.5,
            label=display_name,
        )

        # === DATA RANGE TRACKING SECTION ===
        all_parameter_values.extend(param_values)
        all_depth_values.extend(depth_values)

        logger.debug(
            f"  ✅ Plotted {len(param_values)} points from {csv_name} "
            f"(color: {color}, marker: {marker})"
        )

    # === AXIS CONFIGURATION SECTION ===
    if len(all_parameter_values) == 0:
        logger.warning(f"⚠️ No data points to plot for formation '{formation_name}'")
        plt.close(fig)
        return

    # Set x-axis limits
    max_param = max(all_parameter_values)
    ax.set_xlim(left=x_limit_left, right=max_param * 1.1)  # 10% margin on right

    # Set y-axis limits with margin (inverted for depth)
    min_depth = min(all_depth_values)
    max_depth = max(all_depth_values)

    if invert_y:
        # For inverted axis: top value is minimum (0), bottom value is maximum (deepest)
        ax.set_ylim(
            top=max(0, min_depth - y_margin),  # Start at 0 or add margin at top
            bottom=max_depth + y_margin,  # Add margin at bottom (deepest)
        )
    else:
        # For normal axis: bottom is minimum, top is maximum
        ax.set_ylim(bottom=max(0, min_depth - y_margin), top=max_depth + y_margin)

    # === LABELS AND TITLE SECTION ===
    # X-axis label at top
    ax.set_xlabel(
        parameter_display_name,
        fontsize=x_label_size,
        fontweight=x_label_weight,
    )
    ax.xaxis.set_label_position(x_label_position)
    ax.xaxis.tick_top()

    # Y-axis label
    ax.set_ylabel(
        y_label,
        fontsize=y_label_size,
        fontweight=y_label_weight,
    )

    # Title with formation name
    ax.set_title(
        formation_name,
        fontsize=14,
        fontweight="bold",
        pad=20,
    )

    # === GRID SECTION ===
    if grid_enabled:
        ax.grid(
            which=grid_which,
            linestyle=grid_style,
            linewidth=grid_width,
            color=grid_color,
            alpha=grid_alpha,
        )

    # === LEGEND SECTION ===
    # Extract legend configuration
    legend_config = CONFIG["plotting"]["legend"]
    legend_location = legend_config.get("location", "upper center")
    legend_edgecolor = legend_config.get("edgecolor", "black")
    legend_framealpha = legend_config.get("framealpha", 0.9)
    legend_ncol = legend_config.get("ncol", 3)
    legend_fixed_width = legend_config.get("fixed_width", False)
    bbox_anchor = legend_config.get("bbox_to_anchor", None)

    # Calculate optimal number of columns based on legend entries
    handles, labels = ax.get_legend_handles_labels()
    num_entries = len(labels)
    optimal_ncol = min(3, max(1, num_entries // 2)) if num_entries > 0 else legend_ncol

    # Use smaller font and increased spacing to prevent overlap
    legend_fontsize = 10  # Standard matplotlib legend font size

    if bbox_anchor:
        if legend_fixed_width:
            # ABSOLUTE WIDTH MATCHING: Make legend exactly equal to axes width
            # Get axes position in figure coordinates
            fig.canvas.draw()  # Force draw to get accurate renderer
            ax_bbox = ax.get_position()  # Returns Bbox object with axes position

            # Calculate absolute bbox coordinates in axes coordinates
            # Legend will span from left edge (0) to right edge (1) of axes
            # Y position from CONFIG, in axes coordinates relative to axes bottom
            # Use -0.15 to ensure legend never overlaps plot area (further below)
            bbox_expand = (0, -0.15, 1, 0)  # (x_left, y, width, height)

            legend = ax.legend(
                loc="lower left",  # Anchor at bottom-left of bbox
                bbox_to_anchor=bbox_expand,
                bbox_transform=ax.transAxes,  # Use axes coordinate system
                edgecolor=legend_edgecolor,
                framealpha=legend_framealpha,
                ncol=optimal_ncol,  # Dynamic column count
                mode="expand",  # Expand legend to fill bbox width
                borderaxespad=0,  # No padding between legend and anchor point
                labelspacing=0.5,  # Reduced vertical space between entries
                borderpad=0.5,  # Reduced internal padding
                fontsize=legend_fontsize,
                columnspacing=1.0,  # Horizontal space between columns
            )
        else:
            # Standard legend (auto-sized)
            legend = ax.legend(
                loc=legend_location,
                bbox_to_anchor=(0.5, -0.15),  # More space below plot
                edgecolor=legend_edgecolor,
                framealpha=legend_framealpha,
                ncol=optimal_ncol,  # Dynamic column count
                labelspacing=0.5,  # Reduced vertical space
                borderpad=0.5,  # Reduced internal padding
                fontsize=legend_fontsize,
            )
    else:
        legend = ax.legend(
            loc=legend_location,
            edgecolor=legend_edgecolor,
            framealpha=legend_framealpha,
            ncol=optimal_ncol,  # Dynamic column count
            labelspacing=0.5,  # Reduced vertical space
            borderpad=0.5,  # Reduced internal padding
            fontsize=legend_fontsize,
        )

    # === FILE SAVING SECTION ===
    # Create output folder if it doesn't exist
    output_folder.mkdir(parents=True, exist_ok=True)

    # Sanitize formation name for filename
    sanitized_name = (
        formation_name.replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
    )
    output_path = output_folder / f"{sanitized_name}.png"

    # Save figure
    fig.savefig(
        output_path,
        dpi=fig_dpi,
        bbox_inches=save_bbox_inches,
    )
    plt.close(fig)

    logger.info(f"✅ Saved plot: {output_path}")


# ═══════════════════════════════════════════════════════════════════════════
# 🔧 OUTPUT CONTROL HELPERS
# ═══════════════════════════════════════════════════════════════════════════


def extract_output_control_config() -> Dict[str, Any]:
    """
    Extract output control configuration as primitive dict.

    Helper for orchestrator functions to extract CONFIG["output_control"]
    as a standalone dict for passing to business logic functions.

    Returns:
        dict: Output control configuration extracted from CONFIG
    """
    return CONFIG.get("output_control", {})


def should_generate_output(
    output_control: Dict[str, Any],
) -> bool:
    """
    Check if ANY outputs should be generated based on master toggle.

    Args:
        output_control: output_control section from CONFIG

    Returns:
        True if master toggle is ON, False otherwise
    """
    return output_control.get("enabled", True)


def should_generate_plot(
    plot_name: str,
    output_control: Dict[str, Any],
) -> bool:
    """
    Check if a specific plot should be generated.

    Hierarchy:
    1. Master toggle must be ON
    2. Plots category toggle must be ON
    3. Individual plot toggle must be ON (if exists)

    Args:
        plot_name: Name of plot toggle in output_control["plots"]
        output_control: output_control section from CONFIG

    Returns:
        True if plot should be generated, False otherwise
    """
    if not should_generate_output(output_control):
        return False

    plots_config = output_control.get("plots", {})
    category_toggle = plots_config.get("enabled", True)

    if not category_toggle:
        return False

    # Check individual plot toggle (default to True if not specified)
    return plots_config.get(plot_name, True)


def should_generate_data_export(
    export_name: str,
    output_control: Dict[str, Any],
) -> bool:
    """
    Check if a specific data export should be generated.

    Hierarchy:
    1. Master toggle must be ON
    2. Data category toggle must be ON
    3. Individual export toggle must be ON (if exists)

    Args:
        export_name: Name of export toggle in output_control["data"]
        output_control: output_control section from CONFIG

    Returns:
        True if data export should be generated, False otherwise
    """
    if not should_generate_output(output_control):
        return False

    data_config = output_control.get("data", {})
    category_toggle = data_config.get("enabled", True)

    if not category_toggle:
        return False

    # Check individual export toggle (default to True if not specified)
    return data_config.get(export_name, True)


def generate_formation_plots(
    formation_groups: Dict[str, Dict[str, pd.DataFrame]],
    parameter_mappings: pd.DataFrame,
    parameter_name: str,
    parameter_display_name: str,
    output_base_folder: str,
) -> None:
    """
    Generate plots for all geological formations with outlier detection (orchestrator function).

    This function coordinates plot generation for all formations identified in Phase 3.
    It creates TWO sets of plots: one with outliers and one without outliers.

    Args:
        formation_groups: Nested dictionary from group_data_by_formation()
                         Structure: {formation_name: {csv_name: dataframe}}
        parameter_mappings: DataFrame with columns [csv_file, column_name, priority_rank, quality_score]
        parameter_name: Technical parameter name (e.g., "UndrainedShearStrength")
                       Used for creating output folder name
        parameter_display_name: Human-readable parameter name with units
                               (e.g., "Undrained Shear Strength Cu (kPa)")
        output_base_folder: Base output folder path (e.g., "Output")

    Output Structure:
        Creates directories:
        {output_base_folder}/{parameter_name}/with_outliers/
        {output_base_folder}/{parameter_name}/without_outliers/

        Saves plots:
        {output_base_folder}/{parameter_name}/with_outliers/{formation_name}.png
        {output_base_folder}/{parameter_name}/without_outliers/{formation_name}.png

        Example:
        Output/
        └── UndrainedShearStrength/
            ├── with_outliers/
            │   ├── Gault_Clay_Formation_Weathered.png
            │   └── Kimmeridge_Clay_Formation_Weathered.png
            └── without_outliers/
                ├── Gault_Clay_Formation_Weathered.png
                └── Kimmeridge_Clay_Formation_Weathered.png

    Processing:
        - Detects outliers per test type (CSV) for each formation
        - Generates two matplotlib plots per formation (with/without outliers)
        - Uses per-source marker configurations for visual distinction by test type
        - Tracks total plots generated and logs summary
    """
    logger.info(f"🚀 PHASE 4: Generating plots for {len(formation_groups)} formations")

    # === OUTPUT CONTROL EXTRACTION ===
    output_control = CONFIG.get("output_control", {})

    # Check if any outputs should be generated
    if not should_generate_output(output_control):
        logger.info(
            "⚠️ Output generation disabled by master toggle - skipping all outputs"
        )
        return

    # === GLOBAL COLOR MAPPING SECTION ===
    # Create consistent color assignment for all test types
    color_mapping = create_global_color_mapping(parameter_mappings)

    # === OUTPUT FOLDER SETUP SECTION ===
    param_output_folder = Path(output_base_folder) / parameter_name
    with_outliers_folder = (
        param_output_folder
        / CONFIG["outlier_detection"]["output_folders"]["with_outliers"]
    )
    without_outliers_folder = (
        param_output_folder
        / CONFIG["outlier_detection"]["output_folders"]["without_outliers"]
    )

    logger.info(f"📂 Output folders:")
    logger.info(f"   With outliers: {with_outliers_folder}")
    logger.info(f"   Without outliers: {without_outliers_folder}")

    # === PLOT GENERATION SECTION ===
    plot_count = 0

    for formation_name in sorted(formation_groups.keys()):
        csv_dict = formation_groups[formation_name]

        logger.info(f"\n📊 Processing formation: {formation_name}")

        # === OUTLIER DETECTION SECTION ===
        outlier_results = detect_outliers_per_csv(
            csv_dict,
            parameter_mappings,
            formation_name,
            CONFIG["outlier_detection"],
        )

        # === PLOT GENERATION WITH OUTLIERS ===
        if should_generate_plot("formation_plots_with_outliers", output_control):
            logger.info(f"  📈 Generating plot WITH outliers...")
            generate_formation_plot(
                formation_name,
                csv_dict,
                parameter_mappings,
                parameter_display_name,
                with_outliers_folder,
                color_mapping,
                outlier_results=None,  # No filtering
            )
        else:
            logger.info(f"  ⏭️  Skipping plot WITH outliers (disabled in CONFIG)")

        # === PLOT GENERATION WITHOUT OUTLIERS ===
        if should_generate_plot("formation_plots_without_outliers", output_control):
            logger.info(f"  📈 Generating plot WITHOUT outliers...")
            generate_formation_plot(
                formation_name,
                csv_dict,
                parameter_mappings,
                parameter_display_name,
                without_outliers_folder,
                color_mapping,
                outlier_results=outlier_results,  # Apply filtering
            )
        else:
            logger.info(f"  ⏭️  Skipping plot WITHOUT outliers (disabled in CONFIG)")

        plot_count += 1

    # === SUMMARY SECTION ===
    logger.info("")
    logger.info(
        f"✅ PHASE 4 COMPLETE: Generated {plot_count} formation plots (2 versions each)"
    )
    logger.info("📂 Plots saved to:")
    logger.info(f"   With outliers: {with_outliers_folder}")
    logger.info(f"   Without outliers: {without_outliers_folder}")


# ═══════════════════════════════════════════════════════════════════════════
# 📋 PHASE 5: INVESTIGATION SOURCE TRACKING
# ═══════════════════════════════════════════════════════════════════════════


def load_location_details(
    csv_folder: str, location_details_csv_name: str
) -> Dict[str, str]:
    """
    Load Location Details CSV and create investigation lookup dictionary.

    Reads the Location Details CSV file and creates a mapping from Location ID
    to Investigation name. Handles missing/null values by assigning "Unknown".
    Strips whitespace from both Location ID and Investigation columns for
    consistent matching.

    Args:
        csv_folder: Absolute path to folder containing Location Details CSV
        location_details_csv_name: Name of the location details CSV file

    Returns:
        dict: {Location ID: Investigation} mapping with clean values

    Example Output:
        {"BH01": "1991 to 1992 - Exploration Associates",
         "CPT23": "2023 - Geotechnical Surveys Ltd",
         "TP05": "Unknown"}
    """
    csv_folder_path = Path(csv_folder)
    location_csv = csv_folder_path / location_details_csv_name

    logger.info(f"📂 Loading location details from: {location_csv}")

    try:
        # Load CSV file
        df = pd.read_csv(location_csv, encoding="utf-8-sig")
        logger.info(f"   Loaded {len(df)} location records")

        # Strip whitespace from column names
        df.columns = df.columns.str.strip()

        # Validate required columns exist
        required_columns = ["Location ID", "Investigation"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(
                f"Missing required columns in Location Details CSV: {missing_columns}"
            )

        # Handle missing values and strip whitespace
        df["Location ID"] = df["Location ID"].fillna("Unknown").astype(str).str.strip()
        df["Investigation"] = (
            df["Investigation"].fillna("Unknown").astype(str).str.strip()
        )

        # Convert to dictionary
        investigation_lookup = dict(zip(df["Location ID"], df["Investigation"]))

        unique_investigations = df["Investigation"].nunique()
        logger.info(
            f"   Created lookup for {len(investigation_lookup)} locations across "
            f"{unique_investigations} investigations"
        )

        return investigation_lookup

    except FileNotFoundError:
        logger.error(f"❌ Location Details CSV not found: {location_csv}")
        return {}
    except Exception as e:
        logger.error(f"❌ Failed to load location details: {str(e)}")
        return {}


def _process_csv_for_investigation_tracking(
    csv_name: str,
    df: pd.DataFrame,
    formation_name: str,
    investigation_lookup: Dict[str, str],
    parameter_mappings: pd.DataFrame,
) -> List[Dict[str, Any]]:
    """
    Process a single CSV to extract investigation source counts.

    Helper function for extract_investigation_sources. Processes one CSV file
    within a formation to count parameter values per investigation.

    Args:
        csv_name: Name of CSV file (e.g., "SPT by Geology.csv")
        df: DataFrame containing the CSV data
        formation_name: Name of geological formation
        investigation_lookup: Dict mapping {Location ID: Investigation}
        parameter_mappings: DataFrame with CSV to parameter column mappings

    Returns:
        list: Summary records for this CSV as list of dicts
    """
    # Clean test type name (remove "by Geology.csv" suffix)
    test_type = csv_name.replace(" by Geology.csv", "")

    # Find parameter column for this CSV
    param_row = parameter_mappings[parameter_mappings["csv_file"] == csv_name]
    if param_row.empty:
        logger.debug(f"      ⚠️ No parameter mapping found for {csv_name} - skipping")
        return []

    param_column = param_row.iloc[0]["column_name"]

    # Validate required columns exist
    required_cols = ["Location ID", param_column]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.debug(f"      ⚠️ Missing columns {missing_cols} in {csv_name} - skipping")
        return []

    # Filter rows with valid (non-null) parameter values
    df_valid = df[df[param_column].notna()].copy()

    if df_valid.empty:
        logger.debug(f"      ⚠️ No valid parameter values in {csv_name} - skipping")
        return []

    # Count values per investigation
    investigation_counts: Dict[str, int] = defaultdict(int)

    for _, row in df_valid.iterrows():
        location_id = str(row["Location ID"]).strip()
        investigation = investigation_lookup.get(location_id, "Unknown")
        investigation_counts[investigation] += 1

    # Create summary records for this test type
    records = []
    for investigation, count in investigation_counts.items():
        records.append(
            {
                "Formation": formation_name,
                "Test Type": test_type,
                "Investigation": investigation,
                "Value Count": count,
            }
        )

    logger.debug(
        f"      ✅ {test_type}: {len(investigation_counts)} "
        f"investigations, {len(df_valid)} total values"
    )

    return records


def extract_investigation_sources(
    grouped_by_formation: Dict[str, Dict[str, pd.DataFrame]],
    investigation_lookup: Dict[str, str],
    parameter_mappings: pd.DataFrame,
    parameter_name: str,
) -> List[Dict[str, Any]]:
    """
    Extract investigation sources from grouped formation data.

    Analyzes each formation's data to count parameter values per investigation
    source and test type combination. Matches Location IDs with investigations,
    cleans test type names, and filters null parameter values before counting.

    Args:
        grouped_by_formation: Nested dict {formation_name: {csv_name: dataframe}}
        investigation_lookup: Dict mapping {Location ID: Investigation}
        parameter_mappings: DataFrame with CSV to parameter column mappings
        parameter_name: Name of parameter being analyzed (unused but kept for API consistency)

    Returns:
        list: Summary records as list of dicts with keys:
              ["Formation", "Test Type", "Investigation", "Value Count"]

    Example Output:
        [{"Formation": "Made Ground",
          "Test Type": "SPT",
          "Investigation": "1991 to 1992 - Exploration Associates",
          "Value Count": 13}]
    """
    logger.info("🔍 Extracting investigation sources from formation data...")

    summary_records = []

    # Iterate through formations
    for formation_name, csv_dict in grouped_by_formation.items():
        logger.info(f"   Processing formation: {formation_name}")

        # Process each CSV source (test type)
        for csv_name, df in csv_dict.items():
            csv_records = _process_csv_for_investigation_tracking(
                csv_name,
                df,
                formation_name,
                investigation_lookup,
                parameter_mappings,
            )
            summary_records.extend(csv_records)

    logger.info(f"✅ Extracted {len(summary_records)} investigation source records")
    return summary_records


def export_investigation_csv(
    investigation_data: List[Dict[str, Any]],
    output_path: Path,
    columns: List[str],
) -> None:
    """
    Export investigation source data to CSV file.

    Converts list of investigation records to DataFrame, sorts for readability,
    and writes to CSV with specified column order. Creates output directory if
    needed.

    Args:
        investigation_data: List of dicts with investigation records
        output_path: Full path to output CSV file
        columns: List of column names in desired output order

    Raises:
        ValueError: If investigation_data is empty
        IOError: If CSV write fails
    """
    logger.info(f"💾 Exporting investigation summary to: {output_path}")

    if not investigation_data:
        logger.warning("⚠️ No investigation data to export - skipping CSV creation")
        return

    try:
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to DataFrame
        df = pd.DataFrame(investigation_data)

        # Sort for readability: Formation -> Test Type -> Investigation
        df_sorted = df.sort_values(
            ["Formation", "Test Type", "Investigation"], ignore_index=True
        )

        # Write CSV with specified column order
        df_sorted.to_csv(output_path, index=False, columns=columns, encoding="utf-8")

        logger.info(f"✅ Exported {len(df_sorted)} records to {output_path.name}")

    except Exception as e:
        logger.error(f"❌ Failed to export investigation CSV: {str(e)}")
        raise IOError(f"CSV export failed: {str(e)}") from e


def _export_both_investigation_csvs(
    data_with_outliers: List[Dict[str, Any]],
    data_without_outliers: List[Dict[str, Any]],
    data_folder: Path,
    output_columns: List[str],
    output_control: Dict[str, Any],
) -> None:
    """
    Export both with_outliers and without_outliers investigation CSV files.

    Helper function to keep generate_investigation_summary under 75 lines.
    Exports two versions of the investigation summary CSV to separate files
    for comparison and analysis.

    Args:
        data_with_outliers: Investigation records including outliers
        data_without_outliers: Investigation records excluding outliers
        data_folder: Directory for output CSV files
        output_columns: Column order for both CSV files
        output_control: Output control configuration dict

    Type Hints: Complete ✅
    CONFIG Access: 0 (business logic) ✅
    Lines: ~20 lines ✅
    """
    csv_with = data_folder / "investigation_summary_with_outliers.csv"
    csv_without = data_folder / "investigation_summary_without_outliers.csv"

    logger.info("💾 Writing both CSV versions...")
    logger.info(f"   WITH outliers: {csv_with.name}")

    if should_generate_data_export("investigation_summary_csv", output_control):
        export_investigation_csv(data_with_outliers, csv_with, output_columns)
    else:
        logger.info("   ⏭️ Skipping CSV export (disabled in output_control)")

    logger.info(f"   WITHOUT outliers: {csv_without.name}")

    if should_generate_data_export("investigation_summary_csv", output_control):
        export_investigation_csv(data_without_outliers, csv_without, output_columns)
    else:
        logger.info("   ⏭️ Skipping CSV export (disabled in output_control)")

    if should_generate_data_export("investigation_summary_csv", output_control):
        logger.info("✅ Both investigation summary CSVs exported successfully")
    else:
        logger.info("✅ Investigation tracking complete (CSV export disabled)")


def _execute_investigation_tracking_workflow(
    grouped_by_formation: Dict[str, Dict[str, pd.DataFrame]],
    grouped_without_outliers: Dict[str, Dict[str, pd.DataFrame]],
    parameter_mappings: pd.DataFrame,
    parameter_name: str,
    csv_source_folder: str,
    location_details_csv_name: str,
    data_folder: Path,
    output_columns: List[str],
    output_control: Dict[str, Any],
) -> None:
    """
    Execute investigation tracking workflow steps (business logic only).

    Helper function for generate_investigation_summary. Executes the sequence:
    load location details -> extract sources (WITH outliers) -> extract sources
    (WITHOUT outliers) -> export both CSVs. All parameters are explicit
    (no CONFIG access).

    Args:
        grouped_by_formation: Nested dict from Phase 3 output (with outliers)
        grouped_without_outliers: Nested dict from Phase 4 output (without outliers)
        parameter_mappings: DataFrame from Phase 1 output
        parameter_name: Parameter being analyzed
        csv_source_folder: Path to CSV source folder
        location_details_csv_name: Name of the location details CSV file
        data_folder: Directory for output CSV files
        output_columns: Column order for output CSV
        output_control: Output control configuration dict
    """
    # === LOAD LOCATION DETAILS ===
    logger.info("📂 Loading investigation data...")
    investigation_lookup = load_location_details(
        csv_source_folder, location_details_csv_name
    )

    if not investigation_lookup:
        logger.warning("⚠️ No investigation lookup data loaded - Phase 5 incomplete")
        return

    # === EXTRACT INVESTIGATION SOURCES (WITH OUTLIERS) ===
    logger.info("🔍 Extracting sources from formation data (WITH outliers)...")
    data_with_outliers = extract_investigation_sources(
        grouped_by_formation,
        investigation_lookup,
        parameter_mappings,
        parameter_name,
    )

    # === EXTRACT INVESTIGATION SOURCES (WITHOUT OUTLIERS) ===
    logger.info("🔍 Extracting sources from formation data (WITHOUT outliers)...")
    data_without_outliers = extract_investigation_sources(
        grouped_without_outliers,
        investigation_lookup,
        parameter_mappings,
        parameter_name,
    )

    if not data_with_outliers and not data_without_outliers:
        logger.warning("⚠️ No investigation data extracted - no CSV to export")
        return

    # === EXPORT BOTH CSV VERSIONS ===
    _export_both_investigation_csvs(
        data_with_outliers,
        data_without_outliers,
        data_folder,
        output_columns,
        output_control,
    )


def generate_investigation_summary(
    grouped_by_formation: Dict[str, Dict[str, pd.DataFrame]],
    grouped_without_outliers: Dict[str, Dict[str, pd.DataFrame]],
    parameter_mappings: pd.DataFrame,
    parameter_name: str,
    parameter_output_folder: Path,
) -> None:
    """
    Orchestrator for Phase 5: Investigation Source Tracking workflow.

    Coordinates the investigation tracking workflow by extracting CONFIG values
    (coordination boundary) and calling business logic. Generates TWO investigation
    summary CSVs in data subfolder: one with outliers and one without outliers.

    Args:
        grouped_by_formation: Nested dict from Phase 3 output (with outliers)
        grouped_without_outliers: Nested dict from Phase 4 output (without outliers)
        parameter_mappings: DataFrame from Phase 1 output
        parameter_name: Parameter being analyzed
        parameter_output_folder: Base output folder for parameter

    CONFIG Accesses (Orchestrator - 4 accesses):
        - investigation_tracking.enabled
        - investigation_tracking.output.data_folder_name
        - investigation_tracking.output_columns
        - parameter.csv_source_folder
    """
    logger.info("🚀 Starting Phase 5: Investigation Source Tracking...")

    # === CONFIG EXTRACTION (Coordination Boundary) ===
    if not CONFIG["investigation_tracking"]["enabled"]:
        logger.info("⚠️ Investigation tracking disabled in CONFIG - skipping Phase 5")
        return

    # Extract output control settings as primitives (coordination boundary)
    output_control = extract_output_control_config()

    csv_source_folder = CONFIG["parameter"]["csv_source_folder"]
    location_details_csv_name = CONFIG["investigation_tracking"]["location_details_csv"]
    data_folder_name = CONFIG["investigation_tracking"]["output"]["data_folder_name"]
    output_columns = CONFIG["investigation_tracking"]["output_columns"]

    # Construct output path
    data_folder = parameter_output_folder / data_folder_name

    try:
        _execute_investigation_tracking_workflow(
            grouped_by_formation,
            grouped_without_outliers,
            parameter_mappings,
            parameter_name,
            csv_source_folder,
            location_details_csv_name,
            data_folder,
            output_columns,
            output_control,
        )
        logger.info("✅ Phase 5 complete: Investigation tracking finished successfully")

    except Exception as e:
        logger.error(f"❌ Phase 5 failed: {str(e)}")
        logger.warning("⚠️ Continuing without investigation tracking...")
        raise


# ═══════════════════════════════════════════════════════════════════════════
# 📊 PHASE 6: EXCEL EXPORT WITH HIGHLIGHTED OUTLIERS
# ═══════════════════════════════════════════════════════════════════════════


def export_highlighted_excel(
    df: pd.DataFrame,
    output_path: Path,
    outlier_indices: set,
    highlight_color: str = "FFFF0000",
    freeze_header: bool = True,
) -> None:
    """
    Export DataFrame to Excel with outlier rows highlighted in red.

    Args:
        df: DataFrame to export
        output_path: Path to save Excel file
        outlier_indices: Set of row indices to highlight as outliers
        highlight_color: Fill color in ARGB format (default: red)
        freeze_header: Whether to freeze the first row
    """
    # Create workbook and worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Data"

    # Write header row
    for col_idx, column_name in enumerate(df.columns, start=1):
        ws.cell(row=1, column=col_idx, value=str(column_name))

    # Define red fill for outlier rows
    red_fill = PatternFill(
        start_color=highlight_color, end_color=highlight_color, fill_type="solid"
    )

    # Write data rows and apply highlighting
    for row_idx, (df_idx, row) in enumerate(df.iterrows(), start=2):
        is_outlier = df_idx in outlier_indices

        for col_idx, value in enumerate(row, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)

            # Handle different data types
            if pd.isna(value):
                cell.value = None
            elif isinstance(value, (int, float, np.integer, np.floating)):
                cell.value = float(value) if not pd.isna(value) else None
            else:
                cell.value = str(value)

            # Apply red highlighting for outlier rows
            if is_outlier:
                cell.fill = red_fill

    # Freeze header row for easier navigation
    if freeze_header:
        ws.freeze_panes = ws["A2"]

    # Auto-adjust column widths (approximate)
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
        ws.column_dimensions[column_letter].width = adjusted_width

    # Save workbook
    wb.save(output_path)
    logger.info(f"  📄 Exported: {output_path.name}")


def generate_excel_exports(
    formation_groups: Dict[str, Dict[str, pd.DataFrame]],
    parameter_mappings: pd.DataFrame,
    parameter_name: str,
    parameter_output_folder: Path,
) -> None:
    """
    Orchestrator for Phase 6: Excel export with highlighted outliers.

    Generates Excel files for each test type (CSV source) with all formations combined.
    Outlier rows are highlighted in red. Creates one Excel file per test type containing
    data from all formations.

    Args:
        formation_groups: Nested dict of formation → CSV → DataFrame
        parameter_mappings: Parameter mapping DataFrame from Phase 1
        parameter_name: Name of parameter being analyzed
        parameter_output_folder: Base output folder for parameter

    CONFIG Accesses (Orchestrator - 4 accesses):
        - excel_export.enabled
        - excel_export.output_folder
        - excel_export.highlight_color
        - excel_export.freeze_header
        - investigation_tracking.output.data_folder_name
    """
    logger.info("🚀 Starting Phase 6: Excel Export with Highlighted Outliers...")

    # === CONFIG EXTRACTION (Coordination Boundary) ===
    if not CONFIG["excel_export"]["enabled"]:
        logger.info("⚠️ Excel export disabled in CONFIG - skipping Phase 6")
        return

    # Extract output control settings as primitives (coordination boundary)
    output_control = extract_output_control_config()

    if not should_generate_data_export(
        "excel_with_highlighted_outliers", output_control
    ):
        logger.info("⏭️ Skipping Excel export (disabled in output_control)")
        return

    # Extract configuration
    excel_config = CONFIG["excel_export"]
    excel_folder = (
        parameter_output_folder
        / CONFIG["investigation_tracking"]["output"]["data_folder_name"]
        / excel_config["output_folder"]
    )
    excel_folder.mkdir(parents=True, exist_ok=True)

    highlight_color = excel_config["highlight_color"]
    freeze_header = excel_config["freeze_header"]

    # Reorganize data: Group by CSV source instead of formation
    # Structure: {csv_name: [(formation_name, df, outlier_indices), ...]}
    csv_source_data = defaultdict(list)

    # First pass: detect outliers for all formations
    outlier_results_by_formation = {}

    for formation_name, csv_dict in formation_groups.items():
        outlier_results = detect_outliers_per_csv(
            csv_dict,
            parameter_mappings,
            formation_name,
            CONFIG["outlier_detection"],
        )
        outlier_results_by_formation[formation_name] = outlier_results

        # Collect data for each CSV source
        for csv_name, df in csv_dict.items():
            if df.empty:
                continue

            # Get outlier indices for this formation-CSV combination
            outlier_data = outlier_results.get(csv_name, {})
            outlier_indices = outlier_data.get("outlier_indices", set())

            csv_source_data[csv_name].append((formation_name, df, outlier_indices))

    # Process each CSV source (test type)
    total_files = 0

    for csv_name, formation_data_list in csv_source_data.items():
        logger.info(f"📊 Processing test type: {csv_name}")

        # Combine all formations for this CSV source
        combined_df_list = []
        combined_outlier_row_numbers = set()
        current_row_offset = 0

        for formation_name, df, outlier_indices in formation_data_list:
            # Add formation data to combined DataFrame
            combined_df_list.append(df)

            # Convert outlier DataFrame indices to row numbers for this formation
            for outlier_idx in outlier_indices:
                if outlier_idx in df.index:
                    # Get the row position (0-based) within this formation's DataFrame
                    row_position = df.index.get_loc(outlier_idx)
                    # Adjust for combined DataFrame position
                    combined_row_number = row_position + current_row_offset
                    combined_outlier_row_numbers.add(combined_row_number)

            current_row_offset += len(df)

        # Concatenate all formation DataFrames for this test type
        if combined_df_list:
            combined_df = pd.concat(combined_df_list, ignore_index=True)

            # Create output filename (sanitize test type name)
            sanitized_test_type = (
                csv_name.replace(" by Geology.csv", "")
                .replace(".csv", "")
                .replace(" ", "_")
            )
            output_path = excel_folder / f"{sanitized_test_type}.xlsx"

            # Export to Excel with outlier highlighting
            export_highlighted_excel(
                combined_df,
                output_path,
                combined_outlier_row_numbers,
                highlight_color,
                freeze_header,
            )

            total_files += 1

    logger.info(
        f"✅ Phase 6 complete: Exported {total_files} Excel files with outlier highlighting"
    )


# ═══════════════════════════════════════════════════════════════════════════
# ⚡ MAIN EXECUTION SECTION
# ═══════════════════════════════════════════════════════════════════════════


def main():
    """
    Main execution function - orchestrates all phases of parameter plotting.

    Implementation Status:
    - Phase 1: Parameter Mapping Extraction ✅ COMPLETE
    - Phase 2: CSV Data Loading ✅ COMPLETE
    - Phase 3: Formation Grouping ✅ COMPLETE
    - Phase 3b: Outlier Filtering ✅ COMPLETE
    - Phase 3c: Manual Outlier Marking ✅ COMPLETE
    - Phase 4: Investigation Series Plot Generation ✅ COMPLETE
    - Phase 5: Investigation Source Tracking ✅ COMPLETE
    - Phase 6: Excel Export with Highlighted Outliers ✅ COMPLETE
    """
    logger.info("=" * 80)
    logger.info("🚀 Multi-Source Parameter Plotting System v1")
    logger.info("=" * 80)

    # === CONFIGURATION EXTRACTION ===
    parameter_name = CONFIG["parameter"]["name"]
    mapping_csv = CONFIG["parameter"]["mapping_csv"]
    csv_source_folder = CONFIG["parameter"]["csv_source_folder"]
    output_folder = CONFIG["parameter"]["output_base_folder"]

    logger.info(f"Parameter: {parameter_name}")
    logger.info(f"Mapping CSV: {mapping_csv}")
    logger.info(f"CSV Source Folder: {csv_source_folder}")
    logger.info(f"Output Folder: {output_folder}")
    logger.info("")

    try:
        # === PHASE 1: PARAMETER MAPPING EXTRACTION ===
        param_mappings = extract_parameter_mappings(parameter_name, mapping_csv)

        if param_mappings.empty:
            logger.error(f"❌ No data sources found for parameter '{parameter_name}'")
            logger.error("Cannot proceed without valid parameter mappings. Exiting.")
            return

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ Phase 1 Complete: Parameter mappings extracted successfully")
        logger.info("=" * 80)

        # === PHASE 2: CSV DATA LOADING ===
        logger.info("")
        csv_data_dict = load_parameter_data(param_mappings, csv_source_folder)

        if not csv_data_dict:
            logger.error(
                f"❌ No CSV data successfully loaded for parameter '{parameter_name}'"
            )
            logger.error("Cannot proceed without valid CSV data. Exiting.")
            return

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ Phase 2 Complete: CSV data loaded and enhanced with formations")
        logger.info("=" * 80)

        # === PHASE 3: FORMATION GROUPING ===
        logger.info("")
        formation_groups = group_data_by_formation(csv_data_dict, param_mappings)

        if not formation_groups:
            logger.error("❌ No formation groups created - all formations may be empty")
            logger.error("Cannot proceed without valid formation groups. Exiting.")
            return

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ Phase 3 Complete: Data grouped by geological formations")
        logger.info("=" * 80)

        # === PHASE 3b: OUTLIER FILTERING ===
        logger.info("")
        filter_outliers_from_formations(formation_groups, param_mappings)

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ Phase 3b Complete: Outlier filtering applied to all formations")
        logger.info("=" * 80)

        # === PHASE 3c: MANUAL OUTLIER MARKING ===
        logger.info("")

        # Load manual outliers from Excel
        excel_file_path = CONFIG["manual_outlier_exclusion"]["excel_file"]
        sheet_mapping = CONFIG["manual_outlier_exclusion"]["sheets"]

        manual_outliers_df = load_manual_outliers(
            parameter_name=parameter_name,
            excel_file=excel_file_path,
            sheet_mapping=sheet_mapping,
        )

        # Mark manual outliers in formation groups
        param_tolerance = CONFIG["manual_outlier_exclusion"]["match_tolerance"][
            "parameter"
        ]
        depth_tolerance = CONFIG["manual_outlier_exclusion"]["match_tolerance"]["depth"]

        mark_manual_outliers(
            formation_groups=formation_groups,
            manual_outliers_df=manual_outliers_df,
            parameter_mappings=param_mappings,
            param_tolerance=param_tolerance,
            depth_tolerance=depth_tolerance,
        )

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ Phase 3c Complete: Manual outliers marked successfully")
        logger.info("=" * 80)

        # === CREATE CLEAN COPY FOR PHASE 5 (WITHOUT OUTLIERS) ===
        # Deep copy formation_groups to create version without outliers for Phase 5
        formation_groups_without_outliers = {}
        for formation_name, csv_dict in formation_groups.items():
            formation_groups_without_outliers[formation_name] = {}
            for csv_name, df in csv_dict.items():
                # Filter out outliers if 'is_outlier' column exists
                if "is_outlier" in df.columns:
                    df_clean = df[~df["is_outlier"]].copy()
                else:
                    df_clean = df.copy()
                formation_groups_without_outliers[formation_name][csv_name] = df_clean

        # === PHASE 4: INVESTIGATION SERIES PLOT GENERATION ===
        logger.info("")
        parameter_display_name = CONFIG["parameter"]["display_name"]

        generate_investigation_series_plots(
            formation_groups,
            param_mappings,
            parameter_name,
            parameter_display_name,
            output_folder,
        )

        logger.info("")
        logger.info("=" * 80)
        logger.info(
            "✅ Phase 4 Complete: Investigation-series plots generated successfully"
        )
        logger.info("=" * 80)

        # === PHASE 5: INVESTIGATION SOURCE TRACKING ===
        logger.info("")
        parameter_output_folder = Path(output_folder) / parameter_name

        generate_investigation_summary(
            formation_groups,
            formation_groups_without_outliers,
            param_mappings,
            parameter_name,
            parameter_output_folder,
        )

        logger.info("")
        logger.info("=" * 80)
        logger.info(
            "✅ Phase 5 Complete: Investigation source tracking finished successfully"
        )
        logger.info("=" * 80)

        # === PHASE 6: EXCEL EXPORT WITH HIGHLIGHTED OUTLIERS ===
        logger.info("")

        generate_excel_exports(
            formation_groups,
            param_mappings,
            parameter_name,
            parameter_output_folder,
        )

        logger.info("")
        logger.info("=" * 80)
        logger.info(
            "✅ Phase 6 Complete: Excel exports with outlier highlighting finished successfully"
        )
        logger.info("=" * 80)

        # === MANUAL OUTLIER EXCLUSION SUMMARY (FINAL OUTPUT) ===
        # Print manual outlier summary table at the end
        print_manual_outlier_summary(
            manual_outliers_df, formation_groups, param_mappings
        )

        logger.info("")
        logger.info(
            "🎉 ALL PHASES COMPLETE: Multi-source parameter plotting finished successfully"
        )

    except Exception as e:
        logger.error(f"❌ EXECUTION FAILED: {e}")
        raise

    except Exception as e:
        logger.error(f"❌ EXECUTION FAILED: {e}")
        raise


if __name__ == "__main__":
    main()

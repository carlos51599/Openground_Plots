#!/usr/bin/env python3
"""
Multi-Source Parameter Plotting System v1
AI-Optimized Monolith Implementation - All Phases Complete

LEGEND COUNT FEATURE (2025-10-31):
Added data point counts to legend entries in HTML interactive plots.
Each investigation in the legend now displays as "Investigation Name (n=x)"
where x is the total number of data points for that investigation across
all test types and formations. This provides immediate visibility into
sample size for each investigation. A total count also appears at the
bottom of the legend as "Total n=xxx".

IMPLEMENTATION:
- Line ~4276: Calculate investigation_counts dictionary
- Line ~5033: Add count to regular trace legend names
- Line ~5121: Add count to dummy circle trace legend names
- Line ~5143: Add total count trace to legend

Architectural Overview:

Responsibility:
Generates depth vs. parameter scatter plots by consolidating data from multiple CSV sources
(test types) for geotechnical parameters. The system is configurable and parameter-agnostic,
automatically identifying and combining all relevant test types for any parameter defined in
the global parameter mapping CSV. Creates investigation-series plots that color by
investigation while using marker shapes for test types. Features comprehensive output
control system to manage large output volumes (matching cu_analysis_v20 architecture).

Key Interactions:
- Input: Global parameter mapping CSV + geological data CSVs + Location Details CSV
- Configuration: Parameter selection, color schemes, geological mappings (reused from v27)
- Processing: Mapping extraction → CSV loading → formation grouping → outlier filtering
  → investigation-series plot generation (colors by investigation, shapes by test type)
- Output: Investigation-series scatter plots in Output/[Parameter_Name]/investigation_series/
- Output Control: Three-level hierarchy (Master → Category → Individual) for selective output

Navigation Guide:
Data flows: Parameter mapping extraction (PHASE 1) → CSV data loading (PHASE 2) →
Formation grouping (PHASE 3) → Outlier filtering (PHASE 3b) →
Manual outlier marking (PHASE 3c) → Investigation-series plots (PHASE 4) →
Investigation tracking (PHASE 5) → Excel export with highlighted outliers (PHASE 6)
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
- Plots: investigation_series_plots_with_outliers, investigation_series_plots_without_outliers,
  investigation_series_plots_manually_identified
- Data: investigation_summary_csv, excel_with_highlighted_outliers

Helper Functions:
- should_generate_output(master, category, item): Core logic for three-level checks
- should_generate_plot(plot_name): Convenience wrapper for plot outputs
- should_generate_data_export(export_name): Convenience wrapper for data exports

Integration Points:
- Phase 4 investigation-series: New plot type with investigation-based coloring
- Phase 5 CSV export: Wraps export_investigation_csv() calls

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
- Phase 3c: Manual Outlier Marking ✅
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
- Enables Phase 5 (investigation tracking) to track outliers correctly
- Required for Phase 6 (Excel export) outlier highlighting

Phase 3c Implementation Details:
- Loads manually identified outliers from Excel spreadsheet (Identified Outliers.xlsx)
- Sheet name: "Undrained Shear Stength" (with spaces as in original Excel)
- Matches outliers by Location ID, parameter value, and depth value
- Adds 'is_manual_outlier' boolean column to formation dataframes
- Uses floating-point tolerance for value matching (configurable in CONFIG)
- Generates summary table showing which outliers were successfully excluded
- Enables investigation_series_plots_manually_identified output type
- Configurable via CONFIG["manual_outlier_exclusion"]["enabled"]

Phase 4 Implementation Details:
- Generates plots with investigation-based coloring and test-type marker shapes
- Uses _add_investigation_column() logic to map Location IDs to investigations
- Color palette rotates through CONFIG["investigation_series"]["investigation_colors"]
- Marker shapes inherited from CONFIG["test_type_settings"] per test type
- Dual legend: investigation colors + test type shapes
- Creates three versions: with-outliers, without-outliers, and manually-identified-excluded
- Publication-quality scatter plots (300 DPI, 4:5 aspect ratio)
- X-axis at top (parameter values), Y-axis inverted (depth increases downward)
- Output: {output_folder}/{parameter_name}/investigation_series/{folder}/{formation_name}.png
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
- Organizes by test type: {test_type}.xlsx (e.g., SPT.xlsx, CPT.xlsx, Triaxial_Total_Stress.xlsx)
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
from scipy import odr
from scipy.spatial import ConvexHull
from scipy.interpolate import UnivariateSpline, splprep, splev
from scipy.signal import savgol_filter
from scipy.stats import gaussian_kde
from sklearn.decomposition import PCA
import plotly.graph_objects as go
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows

# ═══════════════════════════════════════════════════════════════════════════
# 🏗️ INITIALIZATION & CONFIGURATION SECTION
# ═══════════════════════════════════════════════════════════════════════════

# Logging Configuration
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
        "PHASE3c": "📍 PHASE 3c: MANUAL OUTLIER MARKING",
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
        "load_manual_outliers",
        "mark_manual_outliers",
        "generate_investigation_series_plots",
        "generate_investigation_summary",
        "generate_excel_exports",
    ],
}

# MODIFICATION POINT: Consolidated Configuration Dictionary
# Single source of truth for all configuration settings
CONFIG = {
    # ═══════════════════════════════════════════════════════════════════════
    # PLOTTING CONFIGURATION - Visual Output Settings
    # ═══════════════════════════════════════════════════════════════════════
    "plotting": {
        "figure": {
            "width": 9.5,  # Increased by 1/12 (8 * 13/12 = 8.67) for wider plot area
            "height": 12,  # 2:3 aspect ratio (taller than wider)
            "dpi": 300,
        },
    },
    # ═══════════════════════════════════════════════════════════════════════
    # PLOT TITLE CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════
    "plot_title": {
        "enabled": True,  # MODIFICATION POINT: Set to True to show plot title
        "font_size": 16,
        "font_weight": "bold",
        "font_family": "Arial",
        "pad": 20,  # Spacing between title and plot area (matplotlib)
        # Auto-generated from formation name if not specified
        # Format: "{formation_name} - {parameter_display_name}"
    },
    # ═══════════════════════════════════════════════════════════════════════
    # AXIS TITLE CONFIGURATION (separate from axis labels)
    # ═══════════════════════════════════════════════════════════════════════
    "axis_title": {
        "x_axis": {
            "enabled": False,  # MODIFICATION POINT: Set to True to show X-axis title
            "text": None,  # Auto-generated from parameter_display_name if None
            "font_size": 14,
            "font_weight": "normal",
            "font_family": "Arial",
        },
        "y_axis": {
            "enabled": False,  # MODIFICATION POINT: Set to True to show Y-axis title
            "text": "Depth (m)",  # Default Y-axis title
            "font_size": 14,
            "font_weight": "normal",
            "font_family": "Arial",
        },
        # Spacing settings for axis titles
        "label_pad": 15,  # Spacing between axis labels and plot area (matplotlib)
        "standoff": 20,  # Spacing for axis titles in HTML plots (plotly)
    },
    # ═══════════════════════════════════════════════════════════════════════
    # AXES CONFIGURATION
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
    # LEGEND CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════
    "legend": {
        "location": "upper center",
        "bbox_to_anchor": (
            0.5,
            -0.05,
        ),  # Position legend below plot area, centered horizontally
        "edgecolor": "black",
        "framealpha": 0.9,  # Legend background transparency
        "ncol": 3,  # Multiple columns to match plot width
        "show_sample_count": True,  # Append sample count to legend labels e.g., "SPT (n=45)"
        "fixed_width": True,  # Match legend box width to plot area width
    },
    # ═══════════════════════════════════════════════════════════════════════
    # SAVE CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════
    "save": {
        "bbox_inches": "tight",
    },
    # ═══════════════════════════════════════════════════════════════════════
    # HTML OUTPUT CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════
    # ═══════════════════════════════════════════════════════════════════════
    # DEFAULT TEST TYPE SETTINGS - Fallback for Unmapped Test Types
    # Used when a test type (CSV source) is not in test_type_settings
    # ═══════════════════════════════════════════════════════════════════════
    "default_test_type_settings": {
        "plotted": True,  # Include unmapped test types in processing
        "plot_points": True,  # Plot individual data points by default
        "marker": "o",  # Circle
        # Marker options: 'o' (circle), 's' (square), '^' (triangle-up), 'v' (triangle-down),
        # '<' (triangle-left), '>' (triangle-right), 'D' (diamond), 'd' (thin diamond),
        # 'p' (pentagon), '*' (star), 'h' (hexagon1), 'H' (hexagon2), '+' (plus), 'x' (x)
        "marker_size": 50,
        "alpha": 0.7,
        # Regression settings (uses global regression config from CONFIG["regression"])
        "regression_enabled": False,  # Disable regression by default for unmapped test types
        # Outlier detection settings (IQR method)
        "iqr_multiplier": 1.5,  # MODIFICATION POINT: Standard IQR multiplier (1.5 for standard, 3.0 for extreme outliers)
        # Legend name for test type (will be auto-generated from CSV name if not specified)
        "legend_name": None,  # Auto-generate from CSV name
    },
    # ═══════════════════════════════════════════════════════════════════════
    # MARKERS CONFIGURATION - Global Marker Settings
    # Applied to all data points in investigation series plots
    # ═══════════════════════════════════════════════════════════════════════
    "markers": {
        "edgecolors": "black",
        "linewidths": 0.5,
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
    # REGRESSION CONFIGURATION - Global Technical Parameters
    # Note: Visual styling (linestyle, linewidth, alpha, color) moved to per-source settings
    # ═══════════════════════════════════════════════════════════════════════
    "regression": {
        "type": "reverse_linear",  # MODIFICATION POINT: 'linear', 'reverse_linear', 'deming', or 'pca'
        "bias": 8.0,  # MODIFICATION POINT: Regression bias (-10 to +10) - only for 'deming' type
        # Bias controls the assumed error distribution (deming regression only):
        # +10: Error primarily in Y-variable (depth) → δ→0 → sy→0 (steep/vertical slope)
        #   0: Equal error in X and Y variables (standard ODR) → δ=1 (balanced)
        # -10: Error primarily in X-variable (parameter) → δ→∞ → sy→∞ (shallow/horizontal slope)
        # Recommended: -10 for geotechnical data (parameter has measurement error, depth is precise)
        "bias_scale": 0.5,  # Logarithmic scale factor for delta calculation (deming only)
        # Regression type comparison:
        # 'linear': OLS - minimizes vertical distances (assumes error in Y only)
        # 'reverse_linear': Minimizes horizontal distances (assumes error in X only)
        # 'deming': Adjustable error weighting via bias parameter (controlled balance)
        # 'pca': Principal Component Analysis - finds line of maximum variance (symmetric)
        "min_points": 3,  # Minimum points required for regression
    },
    # ═══════════════════════════════════════════════════════════════════════
    # OUTLIER DETECTION CONFIGURATION (Reused from v27)
    # ═══════════════════════════════════════════════════════════════════════
    "outlier_detection": {
        "enabled": True,
        "method": "standard_iqr",  # Using standard IQR for plotting
        "min_samples_for_detection": 4,
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
    # PARAMETER CONFIGURATION - User Modification Point
    # ═══════════════════════════════════════════════════════════════════════
    "parameter": {
        "name": "UndrainedShearStrength",  # MODIFICATION POINT: Change to any parameter
        "display_name": "Undrained Shear Strength Cu (kPa)",  # For axis labels
        "mapping_csv": "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv",
        "csv_source_folder": "Openground CSVs",
        "output_base_folder": "Output",
    },
    # ═══════════════════════════════════════════════════════════════════════
    # TEST TYPE SETTINGS - Investigation Series Plots
    # MODIFICATION POINT: Configure test type appearance (markers/shapes)
    # NOTE: Colors are assigned by investigation, not test type
    # ═══════════════════════════════════════════════════════════════════════
    "test_type_settings": {
        # Vane Tests (Field measurements)
        "Vane Tests by Geology.csv": {
            "plotted": False,  # Include this test type in processing
            "order": 4,  # Display order in legend (1=first, higher numbers later)
            "plot_points": True,  # Plot individual data points
            "marker": "o",  # Circle
            # Marker options: 'o' (circle), 's' (square), '^' (triangle-up), 'v' (triangle-down),
            # '<' (triangle-left), '>' (triangle-right), 'D' (diamond), 'd' (thin diamond),
            # 'p' (pentagon), '*' (star), 'h' (hexagon1), 'H' (hexagon2), '+' (plus), 'x' (x)
            "marker_size": 60,
            "alpha": 1,
            # Regression settings (uses global regression config from CONFIG["regression"])
            "regression_enabled": True,  # MODIFICATION POINT: Enable/disable regression for this test type
            "regression_linestyle": ":",  # MODIFICATION POINT: Linestyle for regression line (dotted)
            "regression_linewidth": 2.0,  # MODIFICATION POINT: Line width for regression line
            "regression_alpha": 0.8,  # MODIFICATION POINT: Transparency for regression line
            "regression_linecolor": "green",  # MODIFICATION POINT: Color for regression line
            # Outlier detection settings (IQR method)
            "iqr_multiplier": 1.5,  # MODIFICATION POINT: IQR multiplier for outlier detection (1.5 standard, 3.0 extreme)
            # Legend name for test type shape
            "legend_name": "Vane Tests",  # Name shown in legend for this test type marker
        },
        # CPT (Continuous profiling - special density features enabled)
        "CPT by Geology.csv": {
            "plotted": True,  # Include this source in processing
            "order": 2,  # Display order in legend (1=first, higher numbers later)
            "plot_points": False,  # Don't plot individual data points (too dense)
            # MODIFICATION POINT: Auto-plot points if count < threshold
            # (overrides plot_points=False for sparse CPT data)
            "cpt_auto_plot_threshold": 50,
            # Disable density line when auto-plot threshold is triggered
            # (since individual points provide better visualization for sparse data)
            "cpt_auto_plot_disable_density": True,
            "marker": "s",  # Square marker for CPT test type
            # Marker options: 'o' (circle), 's' (square), '^' (triangle-up), 'v' (triangle-down),
            # '<' (triangle-left), '>' (triangle-right), 'D' (diamond), 'd' (thin diamond),
            # 'p' (pentagon), '*' (star), 'h' (hexagon1), 'H' (hexagon2), '+' (plus), 'x' (x)
            "marker_size": 40,
            "alpha": 1,
            # Regression settings (uses global regression config from CONFIG["regression"])
            "regression_enabled": True,  # MODIFICATION POINT: Enable/disable regression for this test type (density line used instead)
            "regression_linestyle": "-.",  # MODIFICATION POINT: Linestyle for regression line (dash-dot)
            "regression_linewidth": 2.0,  # MODIFICATION POINT: Line width for regression line
            "regression_alpha": 0.8,  # MODIFICATION POINT: Transparency for regression line
            "regression_linecolor": "purple",  # MODIFICATION POINT: Color for regression line
            # Outlier detection settings (IQR method)
            "iqr_multiplier": 1.5,  # MODIFICATION POINT: IQR multiplier for outlier detection (1.5 standard, 3.0 extreme)
            # ─────────────────────────────────────────────────────────────
            # CPT-SPECIFIC DENSITY FEATURES (Per Investigation)
            # NOTE: Colors are assigned by investigation, not by test type
            # ─────────────────────────────────────────────────────────────
            # Density Line: Traces through high-density CPT regions for each investigation
            "density_line": {
                "enabled": True,  # MODIFICATION POINT: Enable density line tracing per investigation
                "linewidth": 1.0,
                "linestyle": "-",  # Solid line
                "alpha": 1.0,  # Full opacity for visibility
            },
            # Legend name for test type shape
            "legend_name": "CPT",  # Name shown in legend for CPT test type marker
        },
        # SPT (Correlation-based)
        "SPT by Geology.csv": {
            "plotted": True,  # Include this test type in processing
            "order": 1,  # Display order in legend (1=first, higher numbers later)
            "plot_points": True,  # Plot individual data points
            "marker": "x",
            # Marker options: 'o' (circle), 's' (square), '^' (triangle-up), 'v' (triangle-down),
            # '<' (triangle-left), '>' (triangle-right), 'D' (diamond), 'd' (thin diamond),
            # 'p' (pentagon), '*' (star), 'h' (hexagon1), 'H' (hexagon2), '+' (plus), 'x' (x)
            "marker_size": 55,
            "marker_thickness": 2,  # MODIFICATION POINT: Line thickness for 'x' marker (controls stroke width)
            "alpha": 1,
            # Regression settings (uses global regression config from CONFIG["regression"])
            "regression_enabled": True,  # MODIFICATION POINT: Enable/disable regression for this test type
            "regression_linestyle": "-",  # MODIFICATION POINT: Linestyle for regression line (solid)
            "regression_linewidth": 2.0,  # MODIFICATION POINT: Line width for regression line
            "regression_alpha": 0.8,  # MODIFICATION POINT: Transparency for regression line
            "regression_linecolor": "red",  # MODIFICATION POINT: Color for regression line (fallback to "auto" uses marker color)
            # Outlier detection settings (IQR method)
            "iqr_multiplier": 1.5,  # MODIFICATION POINT: IQR multiplier for outlier detection (1.5 standard, 3.0 extreme)
            # Legend name for test type shape
            "legend_name": "SPT",  # Name shown in legend for SPT test type marker
        },
        # Triaxial Total Stress (Lab tests)
        "Triaxial Total Stress by Geology.csv": {
            "plotted": True,  # Include this test type in processing
            "order": 3,  # Display order in legend (1=first, higher numbers later)
            "plot_points": True,  # Plot individual data points
            "marker": "D",  # Diamond marker for Triaxial test type
            # Marker options: 'o' (circle), 's' (square), '^' (triangle-up), 'v' (triangle-down),
            # '<' (triangle-left), '>' (triangle-right), 'D' (diamond), 'd' (thin diamond),
            # 'p' (pentagon), '*' (star), 'h' (hexagon1), 'H' (hexagon2), '+' (plus), 'x' (x)
            "marker_size": 65,
            "alpha": 1,
            # Regression settings (uses global regression config from CONFIG["regression"])
            "regression_enabled": True,  # MODIFICATION POINT: Enable/disable regression for this test type
            "regression_linestyle": "--",  # MODIFICATION POINT: Linestyle for regression line (dashed)
            "regression_linewidth": 2.0,  # MODIFICATION POINT: Line width for regression line
            "regression_alpha": 0.8,  # MODIFICATION POINT: Transparency for regression line
            "regression_linecolor": "blue",  # MODIFICATION POINT: Color for regression line (fallback to "auto" uses marker color)
            # Outlier detection settings (IQR method)
            "iqr_multiplier": 1.5,  # MODIFICATION POINT: IQR multiplier for outlier detection (1.5 standard, 3.0 extreme)
            # Legend name for test type shape
            "legend_name": "Triaxial Total Stress",  # Name shown in legend for Triaxial test type marker
        },
        # Pressuremeter Tests (In-situ measurements)
        "Pressuremeter Test Results - General.csv": {
            "plotted": True,  # Include this test type in processing
            "order": 5,  # Display order in legend (1=first, higher numbers later)
            "plot_points": True,  # Plot individual data points
            "marker": "^",  # Triangle-up marker for Pressuremeter test type
            # Marker options: 'o' (circle), 's' (square), '^' (triangle-up), 'v' (triangle-down),
            # '<' (triangle-left), '>' (triangle-right), 'D' (diamond), 'd' (thin diamond),
            # 'p' (pentagon), '*' (star), 'h' (hexagon1), 'H' (hexagon2), '+' (plus), 'x' (x)
            "marker_size": 60,
            "alpha": 1,
            # Regression settings (uses global regression config from CONFIG["regression"])
            "regression_enabled": True,  # MODIFICATION POINT: Enable/disable regression for this test type
            "regression_linestyle": "-.",  # MODIFICATION POINT: Linestyle for regression line (dash-dot)
            "regression_linewidth": 2.0,  # MODIFICATION POINT: Line width for regression line
            "regression_alpha": 0.8,  # MODIFICATION POINT: Transparency for regression line
            "regression_linecolor": "orange",  # MODIFICATION POINT: Color for regression line (fallback to "auto" uses marker color)
            # Outlier detection settings (IQR method)
            "iqr_multiplier": 1.5,  # MODIFICATION POINT: IQR multiplier for outlier detection (1.5 standard, 3.0 extreme)
            # Legend name for test type shape
            "legend_name": "Pressuremeter",  # Name shown in legend for Pressuremeter test type marker
        },
    },
    # ═══════════════════════════════════════════════════════════════════════
    # DENSITY TRACING CONFIGURATION (CPT-only feature)
    # Only activates for "CPT by Geology.csv" data
    # Visual styling (enabled, color, linewidth, linestyle, alpha) in per-source CPT settings
    # ═══════════════════════════════════════════════════════════════════════
    "density_tracing": {
        "segment_detection": {
            "gap_threshold": 0.5,  # meters - defines segment boundaries
            "min_segment_length": 0.20,  # REDUCED from 0.25m to 0.20m for sparse data
        },
        "moving_window": {
            "base_window_size": 0.30,  # REDUCED from 0.6m to 0.30m for short segments
            "adaptive_sensitivity": 0.5,  # k factor in adaptive formula
            "step_size_ratio": 0.2,  # step = window * ratio
            "min_points_per_window": 5,  # REDUCED from 50 to 5 for sparse data
        },
        "mode_estimation": {
            "bin_strategy": "fd",  # Freedman-Diaconis rule
            "fallback_bins": 30,  # if FD fails
        },
        "smoothing": {
            "savgol_window": 11,  # must be odd
            "savgol_polyorder": 2,  # quadratic polynomial
            "min_points_for_smoothing": 20,  # skip smoothing for short segments
            "smoothness": 1,  # Unified smoothness parameter (1-10)
            # 1 = minimal smoothing (most accurate, jagged)
            # 5 = moderate smoothing (balanced accuracy/smoothness)
            # 10 = maximum smoothing (smoothest, least accurate)
            # This parameter post-processes the precise density line calculation
            # TECHNICAL PARAMETERS (for linear escalation from smoothness 2→10):
            "vertex_reduction": {
                "min_fraction": 0.10,  # At smoothness=10, keep 10% of vertices (arc-length sampled)
                "max_fraction": 0.95,  # At smoothness=2, keep 95% of vertices (arc-length sampled)
                # Arc-length sampling: vertices distributed based on curve geometry
                # - High-curvature regions: more vertices (preserve detail)
                # - Straight sections: fewer vertices (reduce redundancy)
            },
            "max_smoothing_factor": 500,  # Maximum spline smoothing factor at smoothness=10
            "min_smoothing_factor": 0.5,  # Minimum spline smoothing factor at smoothness=2
        },
        "cv_zones": {  # Depth-dependent CV values for adaptive windowing
            "depth_ranges": [4, 7, 12, 16, 20],  # zone boundaries
            "cv_values": [45, 50, 45, 20],  # typical CV per zone
            "cv_min": 18,  # minimum CV for adaptive formula
            "cv_max": 58,  # maximum CV for adaptive formula
        },
    },
    # ═══════════════════════════════════════════════════════════════════════
    # DENSITY POLYGON TECHNICAL PARAMETERS (Algorithm settings only)
    # Visual styling (enabled, color, linewidth, linestyle, alpha, fill, fill_alpha, density_percentage)
    # has been moved to per-test-type CPT settings in test_type_settings["CPT by Geology.csv"]["density_polygon"]
    # ═══════════════════════════════════════════════════════════════════════
    "density_polygon": {
        "grid_resolution": 150,  # Grid points per axis for KDE evaluation (100-300)
        "bandwidth_method": "scott",  # KDE bandwidth: 'scott', 'silverman', or float
        "min_points": 10,  # Minimum points required to generate polygon
        "smoothness": 1,  # Unified smoothness parameter (1-10)
        # 1 = minimal smoothing (most accurate, follows KDE contour precisely)
        # 5 = moderate smoothing (balanced accuracy/smoothness)
        # 10 = maximum smoothing (smoothest polygon, may lose detail)
        # This parameter post-processes the precise KDE polygon calculation
        # TECHNICAL PARAMETERS (for linear escalation from smoothness 2→10):
        # Vertex reduction: Uses arc-length sampling from density_tracing.smoothing.vertex_reduction
        # - Same adaptive sampling strategy as density curves for consistency
        # - High-curvature corners receive more vertices, straight edges receive fewer
        "max_spline_smoothing": 200,  # Maximum parametric spline smoothing at smoothness=10
        "min_spline_smoothing": 0.5,  # Minimum parametric spline smoothing at smoothness=2
        # Gaussian fallback removed - now uses robust multi-level retry strategy:
        # 1. Cubic spline with arc-length sampled vertices
        # 2. Retry with 50% vertex reduction
        # 3. Fallback to linear spline (k=1)
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
                "Depth",
            ],
        },
    },
    # ═══════════════════════════════════════════════════════════════════════
    # EMPIRICAL CALCULATIONS CONFIGURATION (Reused from v27)
    # ═══════════════════════════════════════════════════════════════════════
    "empirical_calculations": {
        # MODIFICATION POINT: SPT N-value to Undrained Shear Strength conversion factors
        # Formation-specific f1 factors for cu = f1 × N calculation
        "spt_to_cu_factors": {
            # Clay formations
            "KC": 4.5,
            "GF": 4.5,
            "LG": 4.5,
            "RTD": 4.5,
            "HD": 4.5,
            "AMKC": 4.5,
            "AC": 4.5,
            "AL": 4.5,
            "CG": 4.5,
            "MG": 4.5,
            "TS": 4.5,
            # Weathered/unweathered variants
            "KC_W": 4.5,
            "KC_UW": 4.5,
            "GF_W": 4.5,
            "GF_UW": 4.5,
            # Undefined formations
            "KC_undefined": 4.5,
            "GF_undefined": 4.5,
            # RTD sub-formations
            "RTD_1": 4.5,
            "RTD_2": 4.5,
            "RTD_3": 4.5,
            "RTD_Undefined": 4.5,
            # Default fallback
            "default_f1_factor": 4.5,
        }
    },
    # ═══════════════════════════════════════════════════════════════════════
    # INVESTIGATION SOURCE TRACKING CONFIGURATION (Phase 5)
    # ═══════════════════════════════════════════════════════════════════════
    "investigation_tracking": {
        "enabled": True,  # MODIFICATION POINT: Enable/disable investigation tracking
        "location_details_csv": "Location Details.csv",  # CSV with Location ID -> Investigation mapping
        "output": {
            "data_folder_name": "data",  # Subfolder within parameter output folder
            "summary_filename": "investigation_summary.csv",  # Output CSV filename
        },
        "output_columns": [
            "Formation",
            "Test Type",
            "Investigation",
            "Value Count",
        ],  # Column order in output CSV
        # Per-Investigation Plot Settings
        "per_investigation_plots": {
            "enabled": True,  # MODIFICATION POINT: Enable/disable per-investigation plot generation
            "output_folder": "per_investigation",  # Folder name for investigation-specific plots
            "fallback_investigation_name": "Unknown Investigation",  # Default name when investigation missing
            "location_id_column_variants": [
                "Location ID",
                "LocationID",
                "Location_ID",
            ],  # Column name variations
            "investigation_column_variants": [
                "Investigation",
                "Investigation Name",
                "Investigation_Name",
            ],  # Column name variations
        },
    },
    # ═══════════════════════════════════════════════════════════════════════
    # INVESTIGATION SERIES CONFIGURATION (NEW FEATURE)
    # Colors data by investigation, shapes by test type
    # CPT plot behavior (plot_points, cpt_auto_plot_threshold, cpt_auto_plot_disable_density)
    # is controlled by CONFIG["test_type_settings"]["CPT by Geology.csv"]
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
            "force_circle_markers": True,  # If True, forces legend markers to display as circles (actual plot markers remain unchanged)
        },
    },
    # ═══════════════════════════════════════════════════════════════════════
    # MANUAL OUTLIER EXCLUSION CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════
    "manual_outlier_exclusion": {
        "enabled": True,  # MODIFICATION POINT: Enable/disable manual outlier exclusion
        "excel_file": "Identified Outliers.xlsx",  # Excel file with manually identified outliers
        "sheets": {
            # Maps parameter name to sheet name in Excel file
            "UndrainedShearStrength": "Undrained Shear Strength",  # Corrected: 'Strength' not 'Stength'
        },
        "match_tolerance": {
            # Tolerance for matching parameter and depth values (floating-point comparison)
            "parameter": 1e-5,  # Tolerance for matching parameter value (x-coordinate)
            "depth": 1e-5,  # Tolerance for matching depth value (y-coordinate)
        },
        "output_folder": "manually_identified_excluded",  # Subfolder name for plots with manual outliers excluded
    },
    # ═══════════════════════════════════════════════════════════════════════
    # OUTPUT CONTROL CONFIGURATION
    # Three-level hierarchy: Master → Category → Individual Item
    # ═══════════════════════════════════════════════════════════════════════
    "output_control": {
        "enabled": True,  # MODIFICATION POINT: Master toggle - disables ALL output if False
        "plots": {
            "enabled": True,  # MODIFICATION POINT: Category toggle - disables ALL plots if False
            # Individual plot type toggles (only investigation series plots supported)
            "investigation_series_plots_with_outliers": False,  # Investigation-series plots (with_outliers folder)
            "investigation_series_plots_without_outliers": False,  # Investigation-series plots (without_outliers folder)
            "investigation_series_plots_manually_identified": True,  # Investigation-series plots (manually_identified_excluded folder)
            "investigation_series_plots_plotly_with_outliers": True,  # Plotly HTML interactive plots (with_outliers folder only)
        },
        "data": {
            "enabled": False,  # MODIFICATION POINT: Category toggle - disables ALL data exports if False
            # Individual data export toggles
            "investigation_summary_csv": True,  # Investigation tracking summary CSV
            "excel_with_highlighted_outliers": True,  # MODIFICATION POINT: Export Excel files with outliers highlighted in red
        },
    },
    # ═══════════════════════════════════════════════════════════════════════
    # EXCEL EXPORT CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════
    "excel_export": {
        "output_folder": "excel_highlighted",  # Subfolder within data folder
        "outlier_highlight_color": "FFFF0000",  # Red fill (ARGB format)
        "include_all_columns": True,  # Export all columns from source CSV
        "freeze_header_row": True,  # Freeze first row for easier navigation
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# 🔍 OUTLIER DETECTION FUNCTIONS (Reused from v27)
# ═══════════════════════════════════════════════════════════════════════════


def detect_outliers_standard_iqr(
    values_clean: pd.Series,
    method_settings: Dict[str, Any],
    iqr_override: Optional[float] = None,
) -> Tuple[pd.Series, pd.Series, float, float]:
    """
    Detect outliers using the standard Tukey boxplot method.

    Based on: Tukey (1977) "Exploratory Data Analysis"
    Implementation: Outliers beyond Q1 - 1.5*IQR and Q3 + 1.5*IQR

    Args:
        values_clean: Clean numerical data (no NaNs)
        method_settings: Method-specific configuration settings
        iqr_override: Optional test-type-specific IQR multiplier (overrides method_settings)

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

    # Get method-specific settings (use override if provided)
    iqr_multiplier = (
        iqr_override
        if iqr_override is not None
        else method_settings.get("iqr_multiplier", 1.5)
    )
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


def _collect_outlier_filtered_data(
    formation_name: str,
    csv_dict: Dict[str, pd.DataFrame],
    outlier_results: Dict[str, Dict[str, Any]],
    parameter_mappings: pd.DataFrame,
) -> Dict[str, pd.DataFrame]:
    """
    Create outlier-filtered version of formation data.

    Helper function for generate_formation_plots. Removes outlier rows from
    each CSV's dataframe based on detected outlier indices. Preserves original
    data if no outliers detected for a CSV.

    Args:
        formation_name: Formation being processed (for logging)
        csv_dict: Original CSV data {csv_name: dataframe}
        outlier_results: Outlier detection results per CSV
                        {csv_name: {"outlier_indices": set, ...}}
        parameter_mappings: Parameter mapping dataframe

    Returns:
        dict: Filtered data {csv_name: filtered_dataframe} with same structure
              as input but with outlier rows removed

    Type Hints: Complete ✅
    CONFIG Access: 0 (business logic) ✅
    Lines: ~25 lines ✅
    """
    filtered_dict = {}

    for csv_name, df in csv_dict.items():
        # Check if outlier detection was performed for this CSV
        if csv_name in outlier_results:
            outlier_indices = outlier_results[csv_name]["outlier_indices"]

            if outlier_indices:
                # Filter out outlier rows
                filtered_df = df[~df.index.isin(outlier_indices)].copy()
                logger.debug(
                    f"  🔍 {formation_name}/{csv_name}: Removed {len(outlier_indices)} outlier rows"
                )
            else:
                # No outliers detected - use original data
                filtered_df = df.copy()
        else:
            # Outlier detection not performed - use original data
            filtered_df = df.copy()

        filtered_dict[csv_name] = filtered_df

    return filtered_dict


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

        # Get test-type-specific IQR multiplier (overrides global setting)
        test_type_settings = CONFIG["test_type_settings"]
        default_settings = CONFIG["default_test_type_settings"]

        # Use test-type-specific iqr_multiplier if available, otherwise use default, fallback to global
        if (
            csv_name in test_type_settings
            and "iqr_multiplier" in test_type_settings[csv_name]
        ):
            iqr_override = test_type_settings[csv_name]["iqr_multiplier"]
        elif "iqr_multiplier" in default_settings:
            iqr_override = default_settings["iqr_multiplier"]
        else:
            iqr_override = None  # Use global setting from method_settings

        mild_outliers, _, lower_bound, upper_bound = detect_outliers_standard_iqr(
            values_clean, method_settings, iqr_override
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


def filter_outliers_from_formations(
    formation_groups: Dict[str, Dict[str, pd.DataFrame]],
    parameter_mappings: pd.DataFrame,
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Filter outliers from all formations without generating plots (orchestrator).

    Lightweight alternative to generate_formation_plots for when only outlier-filtered
    data is needed (e.g., for Phase 5 investigation tracking) without plot generation.

    Args:
        formation_groups: Nested dictionary from group_data_by_formation()
                         Structure: {formation_name: {csv_name: dataframe}}
        parameter_mappings: DataFrame with columns [csv_file, column_name, priority_rank, quality_score]

    Returns:
        dict: Outlier-filtered data with same structure as input
              {formation_name: {csv_name: filtered_dataframe}}

    Type Hints: Complete ✅
    CONFIG Access: 1 (outlier_detection) ✅
    Lines: ~30 lines ✅
    """
    logger.info(f"🔍 Filtering outliers from {len(formation_groups)} formations")

    # Extract outlier detection config (coordination boundary)
    outlier_config = CONFIG["outlier_detection"]

    grouped_without_outliers = {}

    for formation_name in sorted(formation_groups.keys()):
        csv_dict = formation_groups[formation_name]

        # Detect outliers per CSV
        outlier_results = detect_outliers_per_csv(
            csv_dict,
            parameter_mappings,
            formation_name,
            outlier_config,
        )

        # Collect filtered data
        filtered_csv_dict = _collect_outlier_filtered_data(
            formation_name,
            csv_dict,
            outlier_results,
            parameter_mappings,
        )
        grouped_without_outliers[formation_name] = filtered_csv_dict

    logger.info(
        f"✅ Filtered data ready for {len(grouped_without_outliers)} formations"
    )
    return grouped_without_outliers


# ═══════════════════════════════════════════════════════════════════════════
# � PHASE 3c: MANUAL OUTLIER MARKING
# ═══════════════════════════════════════════════════════════════════════════


def load_manual_outliers(
    parameter_name: str, excel_file: str, sheet_mapping: Dict[str, str]
) -> Optional[pd.DataFrame]:
    """
    Load manually identified outliers from Excel spreadsheet.

    Reads the Excel file specified in CONFIG and extracts manually identified
    outliers for the current parameter. These outliers are matched against
    data points by Location ID, parameter value, and depth.

    Args:
        parameter_name: Parameter name (e.g., "UndrainedShearStrength")
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
    total_outliers = len(results)
    successful_exclusions = sum(1 for r in results if "✅ Yes" in r["Excluded?"])
    failed_exclusions = total_outliers - successful_exclusions

    logger.info(
        f"{'Entry #':<10} {'Location ID':<15} {'x (Param)':<12} {'y (Depth)':<12} {'Test Type':<25} {'Excluded?':<12} {'Reason':<50} {'Notes':<30}"
    )
    logger.info("=" * 150)

    for result in results:
        logger.info(
            f"{result['Entry #']:<10} {result['Location ID']:<15} {result['x (Param)']:<12} {result['y (Depth)']:<12} {result['Test Type']:<25} {result['Excluded?']:<12} {result['Reason']:<50} {result['Notes']:<30}"
        )

    logger.info("")
    logger.info("=" * 150)
    logger.info(f"📊 SUMMARY STATISTICS")
    logger.info(f"   Total Manual Outliers: {total_outliers}")
    logger.info(f"   ✅ Successfully Excluded: {successful_exclusions}")
    logger.info(f"   ❌ Failed to Exclude: {failed_exclusions}")
    if failed_exclusions > 0:
        logger.warning(
            f"   ⚠️ {failed_exclusions} outliers were not found - check Location IDs, parameter values, and depth values"
        )
    logger.info("=" * 150)
    logger.info("")


# ═══════════════════════════════════════════════════════════════════════════
# �🔄 HELPER FUNCTIONS (Reused from v27)
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
    """Apply formation splitting logic to DataFrame for both weathering and RTD classifications.

    Note: geology_code2_desc_col is optional - classification uses only geology_code2 column.
    """
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
        # Get geology_code2_desc if column exists, otherwise None (optional column)
        geology_code2_desc = (
            row.get(geology_code2_desc_col)
            if geology_code2_desc_col and geology_code2_desc_col in df_copy.columns
            else None
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

    # Check if Geology Code2 column exists
    if geology_code2_col is None or geology_code2_col not in df_enhanced.columns:
        logger.debug(
            f"INFO {csv_name}: No Geology Code 2 column found, using standard strata"
        )
        return df_enhanced

    # Note: Geology Code 2 Description column is optional - classification uses only Code 2
    if (
        geology_code2_desc_col is not None
        and geology_code2_desc_col in df_enhanced.columns
    ):
        logger.debug(
            f"INFO {csv_name}: Found Geology Code 2 Description column '{geology_code2_desc_col}'"
        )
    else:
        logger.debug(
            f"INFO {csv_name}: No Geology Code 2 Description column found (optional - not required for classification)"
        )

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
# 🎨 CPT DENSITY CALCULATION FUNCTIONS
# These functions only execute for "CPT by Geology.csv" data
# ═══════════════════════════════════════════════════════════════════════════


def calculate_arc_length_samples(
    x_values: np.ndarray,
    y_values: np.ndarray,
    num_samples: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Sample curve at uniform arc-length intervals.

    Uses cumulative arc length to distribute sample points adaptively based on
    curve geometry. High-curvature regions receive more samples than straight sections.

    Mathematical Foundation:
    - Arc length between points: s_i = sqrt((x_i - x_{i-1})^2 + (y_i - y_{i-1})^2)
    - Cumulative arc length: S_i = sum(s_1 ... s_i)
    - Sample at equal intervals along S (every S_total/num_samples)

    This ensures:
    - High-curvature regions get more vertices (preserve detail)
    - Low-curvature (straight) regions get fewer vertices (reduce redundancy)
    - Total vertex count controlled by num_samples parameter

    Args:
        x_values: X-coordinates of curve
        y_values: Y-coordinates of curve
        num_samples: Target number of sample points

    Returns:
        Tuple of (sampled_x, sampled_y)

    Example:
        >>> x = np.array([0, 1, 2, 3, 4])
        >>> y = np.array([0, 0, 0, 1, 2])  # Straight then curved
        >>> x_sampled, y_sampled = calculate_arc_length_samples(x, y, 3)
        # More samples in curved region (3-4) than straight region (0-2)
    """
    # Edge cases
    if len(x_values) < 2:
        return x_values, y_values

    if num_samples >= len(x_values):
        return x_values, y_values

    # Calculate distances between consecutive points
    dx = np.diff(x_values)
    dy = np.diff(y_values)
    segment_lengths = np.sqrt(dx**2 + dy**2)

    # Cumulative arc length
    cumulative_length = np.zeros(len(x_values))
    cumulative_length[1:] = np.cumsum(segment_lengths)

    total_length = cumulative_length[-1]

    # Handle degenerate case (all points identical)
    if total_length < 1e-10:
        logger.warning(
            "   Arc-length sampling: degenerate curve (total length ≈ 0), using linear downsampling"
        )
        indices = np.linspace(0, len(x_values) - 1, num_samples, dtype=int)
        return x_values[indices], y_values[indices]

    # Sample at uniform arc-length intervals
    sample_lengths = np.linspace(0, total_length, num_samples)

    # Interpolate x and y at sample arc lengths
    sampled_x = np.interp(sample_lengths, cumulative_length, x_values)
    sampled_y = np.interp(sample_lengths, cumulative_length, y_values)

    return sampled_x, sampled_y


def calculate_arc_length_samples_closed(
    x_values: np.ndarray,
    y_values: np.ndarray,
    num_samples: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Sample closed polygon at uniform arc-length intervals.

    Adapted version of arc-length sampling for closed polygons. Key difference:
    the arc length calculation includes the closing edge from last point back
    to first point.

    Mathematical Foundation:
    - Same as calculate_arc_length_samples(), but with closing edge included
    - Total arc length includes distance from last point to first point
    - Samples distributed uniformly along entire closed perimeter

    This ensures:
    - Polygon closure is maintained
    - No bias toward any particular region of the polygon
    - High-curvature regions receive more vertices
    - Straight edges receive fewer vertices

    Args:
        x_values: X-coordinates of polygon vertices (not closed - no duplicate first/last)
        y_values: Y-coordinates of polygon vertices (not closed - no duplicate first/last)
        num_samples: Target number of sample points

    Returns:
        Tuple of (sampled_x, sampled_y) - sampled polygon vertices (not closed)

    Example:
        >>> x = np.array([0, 1, 1, 0])  # Square
        >>> y = np.array([0, 0, 1, 1])
        >>> x_sampled, y_sampled = calculate_arc_length_samples_closed(x, y, 8)
        # 8 samples distributed uniformly around square perimeter
    """
    # Edge cases
    if len(x_values) < 3:
        return x_values, y_values

    if num_samples >= len(x_values):
        return x_values, y_values

    # Close the polygon temporarily for arc-length calculation
    x_closed = np.append(x_values, x_values[0])
    y_closed = np.append(y_values, y_values[0])

    # Calculate distances between consecutive points (including closing edge)
    dx = np.diff(x_closed)
    dy = np.diff(y_closed)
    segment_lengths = np.sqrt(dx**2 + dy**2)

    # Cumulative arc length
    cumulative_length = np.zeros(len(x_closed))
    cumulative_length[1:] = np.cumsum(segment_lengths)

    total_length = cumulative_length[-1]

    # Handle degenerate case (all points identical)
    if total_length < 1e-10:
        logger.warning(
            "   Arc-length sampling (closed): degenerate polygon (perimeter ≈ 0), using linear downsampling"
        )
        indices = np.linspace(0, len(x_values) - 1, num_samples, dtype=int)
        return x_values[indices], y_values[indices]

    # Sample at uniform arc-length intervals
    # Important: We want num_samples points, so we sample from 0 to just before total_length
    # to avoid duplicating the first point (since polygon is closed)
    sample_lengths = np.linspace(
        0, total_length * (num_samples - 1) / num_samples, num_samples
    )

    # Interpolate x and y at sample arc lengths
    sampled_x = np.interp(sample_lengths, cumulative_length, x_closed)
    sampled_y = np.interp(sample_lengths, cumulative_length, y_closed)

    return sampled_x, sampled_y


def apply_line_smoothness(
    x_values: np.ndarray,
    y_values: np.ndarray,
    smoothness: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply post-processing smoothness to density tracing line.

    Uses arc-length sampling to adaptively reduce vertices based on curve geometry,
    followed by optional spline smoothing.

    KEY SMOOTHING STRATEGY:
    1. **Arc-Length Sampling**: Distribute vertices based on cumulative curve length
       - High-curvature regions get more vertices (preserve detail)
       - Straight sections get fewer vertices (reduce redundancy)
       - More natural vertex distribution than uniform linear spacing

    2. **Spline Smoothing**: Apply mathematical smoothing to sampled points
       - Creates smooth curves between reduced vertices
       - Smoothing factor escalates with smoothness parameter

    IMPROVEMENT OVER PREVIOUS METHOD:
    - BEFORE: Uniform linear downsampling (np.linspace) treated all regions equally
    - AFTER: Arc-length sampling adapts to curve geometry
    - BENEFIT: Better preservation of sharp features while reducing straight-line redundancy

    Strategy:
    - Smoothness 1: No sampling or smoothing (total accuracy)
    - Smoothness 2-10: Linear escalation of arc-length reduction + spline smoothing
    - Smoothness 10: Heavy reduction (10% of vertices) + strong smoothing (s=500)

    Args:
        x_values: X-coordinates of density line (depth)
        y_values: Y-coordinates of density line (parameter values)
        smoothness: Smoothness level (1-10)

    Returns:
        Tuple of (smoothed_x, smoothed_y)
    """
    from scipy.interpolate import UnivariateSpline

    logger.info(f"🚀 Applying line smoothness level {smoothness}/10...")

    # Clamp smoothness to valid range
    smoothness = int(np.clip(smoothness, 1, 10))

    # Short lines don't need smoothing
    if len(x_values) < 5:
        logger.info("   Line too short - skipping smoothness")
        return x_values, y_values

    # === SMOOTHNESS LEVEL 1: NO SMOOTHING (Total Accuracy) ===
    if smoothness == 1:
        logger.info("   No smoothing - total accuracy mode")
        return x_values, y_values

    # === SMOOTHNESS LEVEL 2-10: ARC-LENGTH SAMPLING + SPLINE SMOOTHING ===
    # Extract CONFIG parameters
    min_fraction = CONFIG["density_tracing"]["smoothing"]["vertex_reduction"][
        "min_fraction"
    ]
    max_fraction = CONFIG["density_tracing"]["smoothing"]["vertex_reduction"][
        "max_fraction"
    ]
    min_smooth = CONFIG["density_tracing"]["smoothing"]["min_smoothing_factor"]
    max_smooth = CONFIG["density_tracing"]["smoothing"]["max_smoothing_factor"]

    # Step 1: Arc-length sampling for adaptive vertex reduction
    point_reduction_factor = max_fraction - (smoothness - 2) * (
        (max_fraction - min_fraction) / (10 - 2)
    )
    target_points = max(20, int(len(x_values) * point_reduction_factor))

    # Apply arc-length sampling
    x_sampled, y_sampled = calculate_arc_length_samples(
        x_values, y_values, target_points
    )

    logger.info(
        f"   Arc-length sampling: {len(x_values)} → {len(x_sampled)} points "
        f"(reduction factor: {point_reduction_factor:.2f})"
    )

    # Step 2: Apply spline smoothing
    # Linear mapping: smoothness 2 -> min_smooth, smoothness 10 -> max_smooth
    smoothing_factor = min_smooth + (smoothness - 2) * (
        (max_smooth - min_smooth) / (10 - 2)
    )

    try:
        # Sort by x for spline (required for univariate spline)
        sort_idx = np.argsort(x_sampled)
        x_sorted = x_sampled[sort_idx]
        y_sorted = y_sampled[sort_idx]

        # Fit spline
        spline = UnivariateSpline(x_sorted, y_sorted, s=smoothing_factor, k=3)
        y_smooth = spline(x_sorted)

        # Restore original order
        unsort_idx = np.argsort(sort_idx)
        y_smooth = y_smooth[unsort_idx]

        logger.info(f"   Spline smoothing applied (s={smoothing_factor:.2f})")
        return x_sampled, y_smooth

    except Exception as e:
        logger.warning(f"   Spline failed: {e}, using arc-length sampled points")
        return x_sampled, y_sampled


def apply_polygon_smoothness(
    polygon_x: np.ndarray,
    polygon_y: np.ndarray,
    smoothness: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply post-processing smoothness to density polygon vertices.

    This function takes the precisely calculated KDE polygon and applies
    adaptive smoothing based on the smoothness parameter (1-10).

    KEY POLYGON SMOOTHING STRATEGY:
    Uses UNIFIED approach with density line smoothing:
    1. Arc-length sampling for adaptive vertex reduction
    2. Spline smoothing applied to those vertices (preserves vertex count)

    UNIFIED WITH DENSITY LINE:
    Both density lines and polygons now use the same two-step process:
    - Step 1: Arc-length sampling reduces vertices based on geometry
    - Step 2: Spline smoothing smooths those vertices (no re-sampling)
    - Result: Vertex count controlled by arc-length sampling only

    This ensures:
    - Consistent behavior between lines and polygons
    - Predictable vertex counts
    - Clear separation: arc-length = reduction, spline = smoothing

    ROBUST SPLINE FITTING:
    Parametric spline fitting with multi-level retry strategy:
    1. Try cubic spline (k=3) with arc-length sampled vertices
    2. If fails, retry with 50% vertex reduction
    3. If fails, retry with linear spline (k=1)
    4. If all fail, return arc-length sampled vertices

    ESCALATION:
    - Smoothness 1: No smoothing (total accuracy, precise KDE contour)
    - Smoothness 2-10: Linear escalation of vertex reduction AND smoothing intensity
    - Smoothness 10: Heavy reduction (10% vertices) + strong smoothing (s=200)

    Args:
        polygon_x: X-coordinates of polygon vertices
        polygon_y: Y-coordinates of polygon vertices
        smoothness: Smoothness level (1-10)

    Returns:
        Tuple of (smoothed_polygon_x, smoothed_polygon_y)
    """
    from scipy.interpolate import splprep, splev

    logger.info(f"🚀 Applying polygon smoothness level {smoothness}/10...")

    # Clamp smoothness to valid range
    smoothness = int(np.clip(smoothness, 1, 10))

    original_vertex_count = len(polygon_x)

    # === SMOOTHNESS LEVEL 1: NO SMOOTHING (Total Accuracy) ===
    if smoothness == 1:
        logger.info(
            f"   No smoothing - keeping {original_vertex_count} vertices (total accuracy)"
        )
        # Ensure polygon is closed even at smoothness 1
        if not (
            np.allclose(polygon_x[0], polygon_x[-1])
            and np.allclose(polygon_y[0], polygon_y[-1])
        ):
            polygon_x = np.append(polygon_x, polygon_x[0])
            polygon_y = np.append(polygon_y, polygon_y[0])
        return polygon_x, polygon_y

    # === SMOOTHNESS LEVEL 2-10: ARC-LENGTH SAMPLING ===
    # Extract CONFIG parameters for vertex reduction
    min_fraction = CONFIG["density_tracing"]["smoothing"]["vertex_reduction"][
        "min_fraction"
    ]
    max_fraction = CONFIG["density_tracing"]["smoothing"]["vertex_reduction"][
        "max_fraction"
    ]

    # Calculate vertex fraction using linear interpolation
    vertex_fraction = max_fraction - (smoothness - 2) * (
        (max_fraction - min_fraction) / (10 - 2)
    )
    num_samples = max(
        12, int(len(polygon_x) * vertex_fraction)
    )  # Minimum 12 for cubic spline
    logger.info(
        f"   DEBUG: Smoothness={smoothness}, vertex_fraction={vertex_fraction:.3f}, calculated num_samples={int(len(polygon_x) * vertex_fraction)}, actual num_samples={num_samples}"
    )

    # Apply arc-length sampling for adaptive vertex reduction
    reduced_x, reduced_y = calculate_arc_length_samples_closed(
        polygon_x, polygon_y, num_samples
    )
    logger.info(f"   DEBUG: After arc-length sampling: {len(reduced_x)} vertices")

    # Extract CONFIG parameters for spline smoothing
    min_spline = CONFIG["density_polygon"]["min_spline_smoothing"]
    max_spline = CONFIG["density_polygon"]["max_spline_smoothing"]

    # Spline smoothness scales linearly with smoothness parameter
    # Linear mapping: smoothness 2 -> min_spline, smoothness 10 -> max_spline
    spline_smoothness = min_spline + (smoothness - 2) * (
        (max_spline - min_spline) / (10 - 2)
    )

    # Remove duplicate consecutive points that can cause spline fitting to fail
    unique_mask = np.ones(len(reduced_x), dtype=bool)
    for i in range(1, len(reduced_x)):
        if np.allclose(reduced_x[i], reduced_x[i - 1]) and np.allclose(
            reduced_y[i], reduced_y[i - 1]
        ):
            unique_mask[i] = False

    if unique_mask.sum() < 4:
        logger.warning(
            f"   Too few unique vertices ({unique_mask.sum()}), using arc-length sampled polygon"
        )
        # Ensure polygon is closed before returning
        closed_x = np.append(reduced_x, reduced_x[0])
        closed_y = np.append(reduced_y, reduced_y[0])
        return closed_x, closed_y

    reduced_x = reduced_x[unique_mask]
    reduced_y = reduced_y[unique_mask]

    # Close polygon by appending first point
    x_closed = np.append(reduced_x, reduced_x[0])
    y_closed = np.append(reduced_y, reduced_y[0])
    logger.info(f"   DEBUG: After closing polygon: {len(x_closed)} vertices")

    # === ROBUST SPLINE FITTING WITH MULTI-LEVEL RETRY ===
    # NOTE: Evaluates spline at ORIGINAL parameter values (same as density line approach)
    # This preserves the arc-length vertex count - spline only smooths, doesn't re-sample

    # Try 1: Cubic spline with arc-length sampled vertices
    try:
        tck, u = splprep(
            [x_closed, y_closed],
            s=spline_smoothness,
            per=False,  # Don't use periodic mode - we manually closed the polygon
            k=min(3, len(x_closed) - 1),  # Cubic spline if enough points
        )
        logger.info(f"   DEBUG: Parameter array u length: {len(u)}")
        # Evaluate at ORIGINAL parameter values (preserves vertex count)
        smooth_x, smooth_y = splev(u, tck)
        logger.info(
            f"   DEBUG: After splev: {len(smooth_x)} vertices (type: {type(smooth_x)})"
        )

        # Ensure polygon closure: explicitly set last point equal to first point
        smooth_x = np.array(smooth_x)
        smooth_y = np.array(smooth_y)
        smooth_x[-1] = smooth_x[0]
        smooth_y[-1] = smooth_y[0]

        logger.info(
            f"   Arc-length + cubic spline: {original_vertex_count} → {len(smooth_x)} vertices (s={spline_smoothness:.2f})"
        )
        return smooth_x, smooth_y

    except ValueError as e:
        logger.warning(
            f"   Cubic spline failed: {str(e)}, retrying with 50% reduction..."
        )

    # Try 2: Retry with 50% vertex reduction
    try:
        half_samples = max(8, len(reduced_x) // 2)
        x_half, y_half = calculate_arc_length_samples_closed(
            reduced_x, reduced_y, half_samples
        )
        x_half_closed = np.append(x_half, x_half[0])
        y_half_closed = np.append(y_half, y_half[0])

        tck, u = splprep(
            [x_half_closed, y_half_closed],
            s=spline_smoothness,
            per=False,
            k=min(3, len(x_half_closed) - 1),
        )
        # Evaluate at original parameter values (preserves vertex count)
        smooth_x, smooth_y = splev(u, tck)

        # Ensure polygon closure: explicitly set last point equal to first point
        smooth_x = np.array(smooth_x)
        smooth_y = np.array(smooth_y)
        smooth_x[-1] = smooth_x[0]
        smooth_y[-1] = smooth_y[0]

        logger.info(
            f"   Arc-length + cubic spline (50% reduction): {original_vertex_count} → {len(smooth_x)} vertices"
        )
        return smooth_x, smooth_y

    except ValueError as e:
        logger.warning(
            f"   50% reduction failed: {str(e)}, retrying with linear spline..."
        )

    # Try 3: Linear spline (k=1) - always succeeds for valid polygons
    try:
        tck, u = splprep(
            [x_closed, y_closed],
            s=0,  # No smoothing for linear interpolation
            per=False,
            k=1,  # Linear spline
        )
        # Evaluate at original parameter values (preserves vertex count)
        smooth_x, smooth_y = splev(u, tck)

        # Ensure polygon closure: explicitly set last point equal to first point
        smooth_x = np.array(smooth_x)
        smooth_y = np.array(smooth_y)
        smooth_x[-1] = smooth_x[0]
        smooth_y[-1] = smooth_y[0]

        logger.info(
            f"   Arc-length + linear spline: {original_vertex_count} → {len(smooth_x)} vertices (fallback)"
        )
        return smooth_x, smooth_y

    except Exception as e:
        logger.warning(
            f"   All spline methods failed: {str(e)}, using arc-length sampled polygon"
        )
        # Ensure polygon is closed before returning
        closed_x = np.append(reduced_x, reduced_x[0])
        closed_y = np.append(reduced_y, reduced_y[0])
        return closed_x, closed_y


# === DENSITY TRACING HELPER FUNCTIONS ===


def detect_segments(
    depth_array: np.ndarray, gap_threshold: float, min_length: float
) -> List[Tuple[int, int]]:
    """
    Identify continuous segments separated by gaps.

    Args:
        depth_array: 1D numpy array of depths (sorted)
        gap_threshold: minimum gap size (m) to define new segment
        min_length: minimum segment length (m) to retain

    Returns:
        List of (start_idx, end_idx) tuples
    """
    logger.info(f"🔍 SEGMENT DETECTION - Analyzing {len(depth_array)} depth points")
    logger.info(
        f"   Config: gap_threshold={gap_threshold}m, "
        f"min_segment_length={min_length}m"
    )
    logger.info(f"   Depth range: {depth_array.min():.2f}m to {depth_array.max():.2f}m")

    depth_diffs = np.diff(depth_array)
    gap_indices = np.where(depth_diffs > gap_threshold)[0]

    logger.info(f"   Found {len(gap_indices)} gaps > {gap_threshold}m threshold")
    if len(gap_indices) > 0:
        for idx in gap_indices:
            logger.info(
                f"      Gap at index {idx}: {depth_diffs[idx]:.3f}m "
                f"(between {depth_array[idx]:.2f}m and {depth_array[idx+1]:.2f}m)"
            )

    segment_starts = [0] + list(gap_indices + 1)
    segment_ends = list(gap_indices + 1) + [len(depth_array)]

    segments = []
    rejected_segments = []
    for i, (start, end) in enumerate(zip(segment_starts, segment_ends), 1):
        segment_depth_range = depth_array[end - 1] - depth_array[start]
        num_points = end - start

        if segment_depth_range >= min_length:
            segments.append((start, end))
            logger.info(
                f"   ✅ Segment {i} ACCEPTED: {depth_array[start]:.2f}m to "
                f"{depth_array[end-1]:.2f}m (length={segment_depth_range:.3f}m, "
                f"{num_points} points)"
            )
        else:
            rejected_segments.append((start, end, segment_depth_range))
            logger.info(
                f"   ❌ Segment {i} REJECTED: {depth_array[start]:.2f}m to "
                f"{depth_array[end-1]:.2f}m (length={segment_depth_range:.3f}m < "
                f"min_length={min_length}m, {num_points} points)"
            )

    logger.info(
        f"📊 SEGMENT DETECTION SUMMARY: {len(segments)} segments accepted, "
        f"{len(rejected_segments)} rejected"
    )

    if len(segments) == 0:
        logger.warning(
            f"⚠️ NO SEGMENTS MET CRITERIA - All segments < "
            f"min_segment_length={min_length}m"
        )

    return segments


def calculate_mode_histogram(
    data: np.ndarray, bin_strategy: str = "fd", fallback_bins: int = 30
) -> float:
    """
    Calculate mode using histogram with robust binning.

    Args:
        data: Array of values
        bin_strategy: Binning strategy ('fd' for Freedman-Diaconis)
        fallback_bins: Number of bins if strategy fails

    Returns:
        Mode value
    """
    if len(data) < 10:
        return float(np.median(data))

    try:
        counts, bin_edges = np.histogram(data, bins=bin_strategy)
    except Exception:
        counts, bin_edges = np.histogram(data, bins=fallback_bins)

    if np.sum(counts) == 0:
        return float(np.median(data))

    modal_bin_idx = np.argmax(counts)
    mode_value = (bin_edges[modal_bin_idx] + bin_edges[modal_bin_idx + 1]) / 2

    return float(mode_value)


def estimate_local_cv(
    depth: np.ndarray, strength: np.ndarray, center_depth: float, window: float = 1.0
) -> float:
    """
    Estimate coefficient of variation in a local depth window.

    Args:
        depth: Array of depth values
        strength: Array of strength values
        center_depth: Center of window
        window: Window size (m)

    Returns:
        CV percentage
    """
    mask = np.abs(depth - center_depth) <= window / 2
    local_strength = strength[mask]

    if len(local_strength) < 10:
        return 30.0

    cv = (np.std(local_strength) / np.mean(local_strength)) * 100
    return float(cv)


def adaptive_window_size(
    center_depth: float,
    depth_array: np.ndarray,
    strength_array: np.ndarray,
    base_window: float = 0.6,
    sensitivity: float = 0.5,
    cv_min: float = 18.0,
    cv_max: float = 58.0,
) -> float:
    """
    Calculate adaptive window size based on local variability.
    """
    cv_local = estimate_local_cv(depth_array, strength_array, center_depth)

    if cv_local <= cv_min:
        return base_window * 1.5
    elif cv_local >= cv_max:
        return base_window * 0.6
    else:
        cv_ratio = (cv_local - cv_min) / (cv_max - cv_min)
        adjustment = (1 + sensitivity * cv_ratio) ** (-1)
        return base_window * adjustment


def trace_density_line_segment(
    depth: np.ndarray,
    strength: np.ndarray,
    density_config: Dict[str, Any],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Trace density line through a single continuous segment.

    Args:
        depth: Depth values for segment
        strength: Strength values for segment
        density_config: Configuration dictionary

    Returns:
        Tuple of (mode_depths, mode_strengths)
    """
    logger.info(
        f"   🎯 TRACE DENSITY LINE - Processing segment with {len(depth)} points"
    )

    min_depth = depth.min()
    max_depth = depth.max()

    base_window = density_config["moving_window"]["base_window_size"]
    step_size = base_window * density_config["moving_window"]["step_size_ratio"]
    min_points = density_config["moving_window"]["min_points_per_window"]

    logger.info(
        f"      Segment depth range: {min_depth:.2f}m to {max_depth:.2f}m "
        f"(span={max_depth - min_depth:.2f}m)"
    )
    logger.info(
        f"      Window config: base_window={base_window}m, step_size={step_size}m, "
        f"min_points={min_points}"
    )

    window_centers = np.arange(
        min_depth + base_window / 2,
        max_depth - base_window / 2 + step_size,
        step_size,
    )

    logger.info(f"      Created {len(window_centers)} window positions to analyze")

    mode_depths = []
    mode_strengths = []
    skipped_windows = 0

    cv_min = density_config["cv_zones"]["cv_min"]
    cv_max = density_config["cv_zones"]["cv_max"]

    for idx, center in enumerate(window_centers):
        window_size = adaptive_window_size(
            center,
            depth,
            strength,
            base_window=base_window,
            sensitivity=density_config["moving_window"]["adaptive_sensitivity"],
            cv_min=cv_min,
            cv_max=cv_max,
        )

        half_window = window_size / 2
        mask = (depth >= center - half_window) & (depth <= center + half_window)
        window_strength = strength[mask]

        if (
            len(window_strength)
            < density_config["moving_window"]["min_points_per_window"]
        ):
            skipped_windows += 1
            if idx < 3 or idx >= len(window_centers) - 3:  # Log first/last few
                logger.debug(
                    f"         Window {idx+1} at {center:.2f}m SKIPPED: "
                    f"{len(window_strength)} points < {min_points} required"
                )
            continue

        mode_val = calculate_mode_histogram(
            window_strength,
            bin_strategy=density_config["mode_estimation"]["bin_strategy"],
        )

        mode_depths.append(center)
        mode_strengths.append(mode_val)

    logger.info(
        f"      ✅ Calculated {len(mode_depths)} mode points, "
        f"skipped {skipped_windows} windows (insufficient points)"
    )

    if len(mode_depths) == 0:
        logger.warning(
            f"      ⚠️ NO MODE POINTS GENERATED - All {len(window_centers)} windows "
            f"had < {min_points} points"
        )
        return np.array([]), np.array([])

    mode_depths_arr = np.array(mode_depths)
    mode_strengths_arr = np.array(mode_strengths)

    # === APPLY SMOOTHNESS POST-PROCESSING ===
    # Use unified smoothness parameter instead of hardcoded Savitzky-Golay
    if "smoothness" in density_config["smoothing"]:
        smoothness_level = density_config["smoothing"]["smoothness"]
        logger.info(
            f"      🎨 Applying smoothness level {smoothness_level} to "
            f"{len(mode_depths_arr)} points"
        )
        mode_depths_arr, mode_strengths_arr = apply_line_smoothness(
            mode_depths_arr, mode_strengths_arr, smoothness_level
        )
        logger.info(f"      ✅ After smoothing: {len(mode_depths_arr)} points remain")
    else:
        # Fallback to legacy Savitzky-Golay if smoothness not configured
        if (
            len(mode_strengths_arr)
            >= density_config["smoothing"]["min_points_for_smoothing"]
        ):
            from scipy.signal import savgol_filter

            window_length = min(
                density_config["smoothing"]["savgol_window"], len(mode_strengths_arr)
            )
            if window_length % 2 == 0:
                window_length -= 1
            if window_length >= 3:
                mode_strengths_arr = savgol_filter(
                    mode_strengths_arr,
                    window_length,
                    density_config["smoothing"]["savgol_polyorder"],
                )

    return mode_depths_arr, mode_strengths_arr


def generate_density_traces(
    depth_array: np.ndarray,
    strength_array: np.ndarray,
    density_config: Dict[str, Any],
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Generate density traces for multi-segment CPT data.

    Args:
        depth_array: Array of all depth values
        strength_array: Array of all strength values
        density_config: Configuration dictionary

    Returns:
        List of (segment_depths, segment_strengths) tuples
    """
    logger.info("=" * 80)
    logger.info("🎯 DENSITY TRACE GENERATION - Starting analysis")
    logger.info("=" * 80)

    sort_idx = np.argsort(depth_array)
    depth = depth_array[sort_idx]
    strength = strength_array[sort_idx]

    logger.info(f"📊 Input data: {len(depth)} points total")
    logger.info(f"   Depth range: {depth.min():.2f}m to {depth.max():.2f}m")
    logger.info(f"   Strength range: {strength.min():.1f} to {strength.max():.1f} kPa")

    segments = detect_segments(
        depth,
        gap_threshold=density_config["segment_detection"]["gap_threshold"],
        min_length=density_config["segment_detection"]["min_segment_length"],
    )

    if len(segments) == 0:
        logger.error(
            "❌ DENSITY TRACE ABORTED - No valid segments detected. "
            "Check min_segment_length configuration."
        )
        return []

    logger.info(f"✅ Proceeding with {len(segments)} valid segments")

    density_traces = []

    for i, (start_idx, end_idx) in enumerate(segments, 1):
        seg_depth = depth[start_idx:end_idx]
        seg_strength = strength[start_idx:end_idx]

        logger.info(
            f"📍 Processing Segment {i}/{len(segments)}: "
            f"{seg_depth.min():.2f}m - {seg_depth.max():.2f}m ({len(seg_depth)} points)"
        )

        mode_depths, mode_strengths = trace_density_line_segment(
            seg_depth, seg_strength, density_config
        )

        if len(mode_depths) > 0:
            density_traces.append((mode_depths, mode_strengths))
            logger.info(
                f"   ✅ Segment {i} trace complete: {len(mode_depths)} trace points"
            )
        else:
            logger.warning(
                f"   ⚠️ Segment {i} produced no trace points - "
                "likely insufficient data in windows"
            )

    logger.info("=" * 80)
    logger.info(
        f"🏁 DENSITY TRACE GENERATION COMPLETE: {len(density_traces)} traces "
        f"generated from {len(segments)} segments"
    )
    logger.info("=" * 80)

    return density_traces


def plot_cpt_density_lines(
    ax: Any,
    depth_array: np.ndarray,
    strength_array: np.ndarray,
    color: str,
    density_config: Dict[str, Any],
    legend_label: Optional[str] = None,
    linewidth: float = 2.5,
    linestyle: str = "-",
    alpha: float = 0.9,
    zorder: int = 10,
) -> bool:
    """
    Generate and plot CPT density traces on a Matplotlib axes.

    Shared function for plotting CPT density lines in both formation plots
    and investigation-series plots. Accepts explicit parameters instead of
    reading from CONFIG to maintain separation of concerns.

    Args:
        ax: Matplotlib axes to plot on
        depth_array: Array of CPT depth values
        strength_array: Array of CPT parameter (strength) values
        color: Line color for density traces
        density_config: Configuration dict for generate_density_traces
        legend_label: Optional label for legend (first trace only)
        linewidth: Line width for traces
        linestyle: Line style for traces
        alpha: Alpha transparency for traces
        zorder: Z-order for layering

    Returns:
        True if density lines were plotted, False otherwise
    """
    if depth_array.size == 0 or strength_array.size == 0:
        logger.debug("  ⏭️ No CPT data to plot density lines")
        return False

    try:
        logger.info(
            f"  🎨 Calculating density traces for {len(depth_array)} CPT points"
        )

        density_traces = generate_density_traces(
            depth_array=depth_array,
            strength_array=strength_array,
            density_config=density_config,
        )

        if not density_traces:
            logger.warning("  ⚠️ No density traces generated")
            return False

        logger.info(f"  ✅ Drawing {len(density_traces)} density line segment(s)")

        for idx, (trace_depths, trace_strengths) in enumerate(density_traces):
            if len(trace_depths) > 0:
                label = legend_label if (idx == 0 and legend_label) else None

                ax.plot(
                    trace_strengths,
                    trace_depths,
                    color=color,
                    linewidth=linewidth,
                    linestyle=linestyle,
                    alpha=alpha,
                    label=label,
                    zorder=zorder,
                )
                logger.debug(f"    Segment {idx+1}: {len(trace_depths)} points plotted")

        return True

    except Exception as e:
        logger.error(f"  ❌ Density line plotting failed: {str(e)}", exc_info=True)
        return False


def calculate_density_polygon(
    param_values: np.ndarray,
    depth_values: np.ndarray,
    density_percentage: float,
    grid_resolution: int,
    bandwidth_method: str,
    smoothness: int = 5,
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Calculate density-based bounding polygon using KDE.

    Implements Kernel Density Estimation (KDE) with contour extraction to
    create a smooth polygon that captures the specified percentage of points
    in the highest density regions.

    Args:
        param_values: Parameter values (x-coordinates, e.g., Cu)
        depth_values: Depth values (y-coordinates)
        density_percentage: Percentage of points to capture (0-100)
        grid_resolution: Grid points per axis (100-300)
        bandwidth_method: KDE bandwidth ('scott', 'silverman', or float)
        smoothness: Post-processing smoothness level (1-10, default 5)

    Returns:
        Tuple of (polygon_x, polygon_y) arrays of vertices, or (None, None) if failed
    """
    logger.info(f"🚀 Calculating {density_percentage}% density polygon (KDE method)...")

    try:
        # === PREPARE DATA ===
        data = np.vstack([param_values, depth_values])

        # === COMPUTE KDE ===
        kde = gaussian_kde(data, bw_method=bandwidth_method)
        logger.info(f"📊 KDE computed with bandwidth method: {bandwidth_method}")

        # === EVALUATE KDE AT ORIGINAL POINTS ===
        point_densities = kde(data)

        # === FIND DENSITY THRESHOLD ===
        # Lower percentile = excludes lowest density points, keeps highest
        percentile_threshold = 100 - density_percentage
        density_threshold = np.percentile(point_densities, percentile_threshold)
        logger.info(
            f"📊 Density threshold at {percentile_threshold}th percentile: {density_threshold:.6f}"
        )

        # === CREATE GRID ===
        x_min, x_max = param_values.min(), param_values.max()
        y_min, y_max = depth_values.min(), depth_values.max()

        # Add 10% margin
        x_margin = (x_max - x_min) * 0.1
        y_margin = (y_max - y_min) * 0.1

        xx, yy = np.mgrid[
            x_min - x_margin : x_max + x_margin : complex(0, grid_resolution),
            y_min - y_margin : y_max + y_margin : complex(0, grid_resolution),
        ]

        # === EVALUATE KDE ON GRID ===
        positions = np.vstack([xx.ravel(), yy.ravel()])
        density_grid = np.reshape(kde(positions).T, xx.shape)
        logger.info(f"📊 Evaluated KDE on {grid_resolution}x{grid_resolution} grid")

        # === GENERATE CONTOUR ===
        fig_temp, ax_temp = plt.subplots()
        cs = ax_temp.contour(xx, yy, density_grid, levels=[density_threshold])
        plt.close(fig_temp)

        # === EXTRACT VERTICES ===
        contour_paths = cs.allsegs[0]

        if not contour_paths:
            logger.warning("⚠️ No contour paths found at density threshold")
            return None, None

        # Select largest polygon (handles multi-island distributions)
        main_polygon = max(contour_paths, key=len)
        logger.info(f"📊 Extracted polygon with {len(main_polygon)} vertices")

        polygon_x = main_polygon[:, 0]
        polygon_y = main_polygon[:, 1]

        # === VERIFY PERCENTAGE ===
        from matplotlib.path import Path

        polygon_path = Path(np.column_stack([polygon_x, polygon_y]))
        points_inside = polygon_path.contains_points(
            np.column_stack([param_values, depth_values])
        )
        actual_percentage = (points_inside.sum() / len(param_values)) * 100
        logger.info(
            f"✅ Polygon captures {actual_percentage:.1f}% of points (target: {density_percentage}%)"
        )

        # === DEBUG: OUTPUT VERTEX COORDINATES (BEFORE SMOOTHING) ===
        logger.info(f"📍 Precise polygon vertices ({len(polygon_x)} points):")
        logger.info("   X (Cu, kPa)  |  Y (Depth, m)")
        logger.info("   " + "-" * 35)
        for i in range(min(10, len(polygon_x))):  # Show first 10 only
            logger.info(f"   {polygon_x[i]:>10.2f}  |  {polygon_y[i]:>10.2f}")
        if len(polygon_x) > 10:
            logger.info(f"   ... ({len(polygon_x) - 10} more vertices)")
        logger.info("   " + "-" * 35)
        logger.info(f"   Min X: {polygon_x.min():.2f}, Max X: {polygon_x.max():.2f}")
        logger.info(f"   Min Y: {polygon_y.min():.2f}, Max Y: {polygon_y.max():.2f}")

        # === APPLY SMOOTHNESS POST-PROCESSING ===
        polygon_x, polygon_y = apply_polygon_smoothness(
            polygon_x, polygon_y, smoothness
        )

        return polygon_x, polygon_y

    except Exception as e:
        logger.error(f"❌ Failed to calculate density polygon: {e}")
        return None, None


# ═══════════════════════════════════════════════════════════════════════════
# 🎛️ CONFIGURATION EXTRACTION HELPERS
# Orchestrator-level functions to extract CONFIG bundles for primitive injection
# ═══════════════════════════════════════════════════════════════════════════


def extract_plot_config() -> Dict[str, Any]:
    """
    Extract all plotting configuration as a primitive dict bundle.

    This is a COORDINATION BOUNDARY function called by orchestrators to
    extract CONFIG values once and inject them as primitives to business logic.

    Returns:
        Dictionary containing all plot configuration values as primitives
    """
    return {
        # Figure settings
        "fig_width": CONFIG["plotting"]["figure"]["width"],
        "fig_height": CONFIG["plotting"]["figure"]["height"],
        "fig_dpi": CONFIG["plotting"]["figure"]["dpi"],
        # Marker settings (legacy fallback)
        "marker_edgecolors": CONFIG["markers"]["edgecolors"],
        "marker_linewidths": CONFIG["markers"]["linewidths"],
        # Axis settings
        "x_label_position": CONFIG["axes"]["x_label_position"],
        "x_label_size": CONFIG["axes"]["x_label_size"],
        "x_label_weight": CONFIG["axes"]["x_label_weight"],
        "y_label": CONFIG["axes"]["y_label"],
        "y_label_size": CONFIG["axes"]["y_label_size"],
        "y_label_weight": CONFIG["axes"]["y_label_weight"],
        "x_limit_left": CONFIG["axes"]["x_limit_left"],
        "y_margin": CONFIG["axes"]["y_margin"],
        "invert_y": CONFIG["axes"]["invert_y"],
        # Grid settings
        "grid_enabled": CONFIG["axes"]["grid"],
        "grid_which": CONFIG["axes"]["grid_which"],
        "grid_style": CONFIG["axes"]["grid_style"],
        "grid_width": CONFIG["axes"]["grid_width"],
        "grid_color": CONFIG["axes"]["grid_color"],
        "grid_alpha": CONFIG["axes"]["grid_alpha"],
        # Legend settings
        "legend_location": CONFIG["legend"]["location"],
        "legend_edgecolor": CONFIG["legend"]["edgecolor"],
        "legend_ncol": CONFIG["legend"].get("ncol", 1),
        "legend_framealpha": CONFIG["legend"]["framealpha"],
        "legend_fixed_width": CONFIG["legend"].get("fixed_width", False),
        "legend_bbox_anchor": CONFIG["legend"].get("bbox_to_anchor", None),
        "legend_show_sample_count": CONFIG["legend"].get("show_sample_count", False),
        # Plot title settings
        "plot_title_enabled": CONFIG["plot_title"]["enabled"],
        "plot_title_font_size": CONFIG["plot_title"]["font_size"],
        "plot_title_font_weight": CONFIG["plot_title"]["font_weight"],
        "plot_title_font_family": CONFIG["plot_title"]["font_family"],
        "plot_title_pad": CONFIG["plot_title"]["pad"],
        # Axis title settings
        "axis_title_x_enabled": CONFIG["axis_title"]["x_axis"]["enabled"],
        "axis_title_x_text": CONFIG["axis_title"]["x_axis"]["text"],
        "axis_title_y_enabled": CONFIG["axis_title"]["y_axis"]["enabled"],
        "axis_title_y_text": CONFIG["axis_title"]["y_axis"]["text"],
        "axis_title_label_pad": CONFIG["axis_title"]["label_pad"],
        # Save settings
        "save_bbox_inches": CONFIG["save"]["bbox_inches"],
        # Regression settings
        "regression_type": CONFIG["regression"].get("type", "deming"),
        "regression_bias": CONFIG["regression"].get("bias", 8.0),
        "regression_bias_scale": CONFIG["regression"].get("bias_scale", 0.5),
        "regression_min_points": CONFIG["regression"]["min_points"],
        # Test type settings (for investigation series plots)
        "test_type_settings": CONFIG["test_type_settings"],
        "default_test_type_settings": CONFIG["default_test_type_settings"],
    }


def extract_output_control_config() -> Dict[str, Any]:
    """
    Extract output control configuration as a primitive dict bundle.

    This is a COORDINATION BOUNDARY function called by orchestrators.

    Returns:
        Dictionary containing output control settings as primitives
    """
    return {
        "master_enabled": CONFIG["output_control"]["enabled"],
        "plots_enabled": CONFIG["output_control"]["plots"]["enabled"],
        "data_enabled": CONFIG["output_control"]["data"]["enabled"],
        "investigation_series_plots_with_outliers": CONFIG["output_control"]["plots"][
            "investigation_series_plots_with_outliers"
        ],
        "investigation_series_plots_without_outliers": CONFIG["output_control"][
            "plots"
        ]["investigation_series_plots_without_outliers"],
        "investigation_series_plots_manually_identified": CONFIG["output_control"][
            "plots"
        ]["investigation_series_plots_manually_identified"],
        "investigation_series_plots_plotly_with_outliers": CONFIG["output_control"][
            "plots"
        ]["investigation_series_plots_plotly_with_outliers"],
        "investigation_summary_csv": CONFIG["output_control"]["data"][
            "investigation_summary_csv"
        ],
        "excel_with_highlighted_outliers": CONFIG["output_control"]["data"][
            "excel_with_highlighted_outliers"
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════
# 🎛️ OUTPUT CONTROL SECTION
# ═══════════════════════════════════════════════════════════════════════════


def should_generate_output(
    master_enabled: bool, category_enabled: bool, item_enabled: bool
) -> bool:
    """
    Check if a specific output should be generated based on three-level hierarchy.

    Three-level hierarchy:
    1. Master toggle (output_control.enabled) - disables ALL output if False
    2. Category toggle (plots.enabled or data.enabled) - disables category if False
    3. Individual item toggle (specific plot/data export) - disables item if False

    All three levels must be True for output to be generated.

    Args:
        master_enabled: CONFIG["output_control"]["enabled"]
        category_enabled: CONFIG["output_control"]["plots"]["enabled"] or
                         CONFIG["output_control"]["data"]["enabled"]
        item_enabled: Specific item flag (e.g., CONFIG["output_control"]["plots"]["investigation_series_plots_without_outliers"])

    Returns:
        True if output should be generated, False otherwise

    Example:
        >>> should_generate_output(True, True, True)
        True
        >>> should_generate_output(True, False, True)
        False
        >>> should_generate_output(False, True, True)
        False
    """
    return master_enabled and category_enabled and item_enabled


def should_generate_plot(plot_name: str, output_control: Dict[str, Any]) -> bool:
    """
    Convenience function to check if a specific plot should be generated.

    Args:
        plot_name: Key in output_control dict for plots
                  (e.g., "investigation_series_plots_without_outliers")
        output_control: Output control configuration dict from extract_output_control_config()

    Returns:
        True if plot should be generated, False otherwise

    Example:
        >>> output_config = extract_output_control_config()
        >>> should_generate_plot("investigation_series_plots_without_outliers", output_config)
        True  # If all levels enabled
    """
    return should_generate_output(
        output_control["master_enabled"],
        output_control["plots_enabled"],
        output_control.get(plot_name, False),
    )


def should_generate_data_export(
    export_name: str, output_control: Dict[str, Any]
) -> bool:
    """
    Convenience function to check if a specific data export should be generated.

    Args:
        export_name: Key in output_control dict for data exports
                    (e.g., "investigation_summary_csv")
        output_control: Output control configuration dict from extract_output_control_config()

    Returns:
        True if data export should be generated, False otherwise

    Example:
        >>> output_config = extract_output_control_config()
        >>> should_generate_data_export("investigation_summary_csv", output_config)
        True  # If all levels enabled
    """
    return should_generate_output(
        output_control["master_enabled"],
        output_control["data_enabled"],
        output_control.get(export_name, False),
    )


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


# ═══════════════════════════════════════════════════════════════════════════
# 📊 PHASE 1: PARAMETER MAPPING EXTRACTION
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
    color_palette: List[str],
) -> Dict[str, str]:
    """
    Create a global color mapping dictionary for all test types.

    This ensures consistent color assignment across all formations, even when
    some test types are missing from individual formations.

    Args:
        parameter_mappings: DataFrame with columns [csv_file, column_name, priority_rank, quality_score]
        color_palette: List of hex color codes for assignment

    Returns:
        dict: {csv_name: color_hex_code} mapping for all test types
    """
    logger.info("🎨 Creating global color mapping for all test types...")

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
# 📈 PHASE 4: INVESTIGATION SERIES PLOT GENERATION
# Colors by investigation, shapes by test type
# ═══════════════════════════════════════════════════════════════════════════

# 🎨 INVESTIGATION SERIES PLOT GENERATION (NEW FEATURE)
# Colors by investigation, shapes by test type
# ═══════════════════════════════════════════════════════════════════════════


def calculate_linear_regression(
    x_values: np.ndarray,
    y_values: np.ndarray,
    regression_type: str = "deming",
    regression_bias: float = 8.0,
    bias_scale: float = 0.5,
    min_points: int = 3,
) -> Optional[Tuple[float, float, float]]:
    """
    Calculate linear regression with adjustable bias control.

    Supports four regression methods:
    1. 'linear': Ordinary Least Squares (OLS) - minimizes vertical distances
    2. 'reverse_linear': Reverse regression - minimizes horizontal distances
    3. 'deming': Deming regression with adjustable delta parameter (RECOMMENDED)
    4. 'pca': Principal Component Analysis - finds line of maximum variance (symmetric)

    Deming regression generalizes OLS and ODR by allowing user control over the
    relative weighting of errors in X vs Y through the delta parameter.

    PCA regression finds the first principal component (line of maximum variance),
    treating X and Y symmetrically without bias toward either axis.

    Args:
        x_values: Array of parameter values (plotted on x-axis)
        y_values: Array of depth values (plotted on y-axis)
        regression_type: Type of regression ('linear', 'reverse_linear', 'deming', or 'pca')
        regression_bias: Bias control for Deming regression (-10 to +10)
            Controls assumed error distribution:
            +10: Error primarily in Y-variable (depth) → δ→0 → sy→0 (results in steep/vertical slope)
              0: Equal error in X and Y variables → δ=1 (standard ODR, balanced slope)
            -10: Error primarily in X-variable (parameter) → δ→∞ → sy→∞ (results in shallow/horizontal slope)
            Recommended: -10 for geotechnical data (parameter has measurement error, depth is precise)
        bias_scale: Logarithmic scale factor for delta calculation (default: 0.5)
        min_points: Minimum number of data points required for regression

    Returns:
        Tuple of (slope, intercept, r_squared) if successful, None otherwise
        - slope: Rate of change (depth per parameter unit) in y=mx+b form
        - intercept: Y-intercept (depth at parameter=0) in y=mx+b form
        - r_squared: Coefficient of determination (0-1, quality metric)

    Returns None if:
        - Insufficient data points (< min_points)
        - All x or y values are identical (vertical/horizontal line)
        - Regression calculation fails due to numerical issues

    Mathematical Background:
        Deming regression delta parameter: δ = 10^(-bias × bias_scale)
        - Relates to error variances: δ = σ_y² / σ_x²
        - Controls regression line verticality
        - Implemented via scipy.odr with sx=1.0, sy=sqrt(delta)

        PCA regression finds the first principal component (direction of maximum variance)
        - Treats X and Y symmetrically without assuming which has error
        - Line passes through the data centroid (mean_x, mean_y)
        - Implemented via sklearn.decomposition.PCA

    Example:
        >>> x = np.array([10, 20, 30, 40])  # Parameter values
        >>> y = np.array([5, 10, 15, 20])   # Depth values
        >>> # Using Deming regression
        >>> slope, intercept, r2 = calculate_linear_regression(
        ...     x, y, regression_type='deming', regression_bias=8.0
        ... )
        >>> # Using PCA regression (symmetric treatment of X and Y)
        >>> slope, intercept, r2 = calculate_linear_regression(
        ...     x, y, regression_type='pca'
        ... )
    """
    # === VALIDATION SECTION ===
    if len(x_values) < min_points:
        return None

    # Check for sufficient variance in both x and y values
    if np.std(x_values) < 1e-10:
        logger.warning("⚠️ All parameter values identical (vertical line)")
        return None

    if np.std(y_values) < 1e-10:
        logger.warning("⚠️ All depth values identical (horizontal line)")
        return None

    # === REGRESSION CALCULATION SECTION ===
    try:
        if regression_type == "linear":
            # === ORDINARY LEAST SQUARES (OLS) ===
            # Minimizes vertical distances (assumes all error in Y)
            slope, intercept = np.polyfit(x_values, y_values, deg=1)

            # Calculate R-squared
            y_pred = slope * x_values + intercept
            ss_res = np.sum((y_values - y_pred) ** 2)
            ss_tot = np.sum((y_values - np.mean(y_values)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 1e-10 else 0.0
            r_squared = max(0.0, min(1.0, r_squared))

            logger.debug(
                f"  📐 OLS regression: y = {slope:.4f}x + {intercept:.4f}, R²={r_squared:.3f}"
            )

        elif regression_type == "reverse_linear":
            # === REVERSE LINEAR REGRESSION ===
            # Minimizes horizontal distances (assumes all error in X)
            # Equivalent to regressing X on Y and inverting
            x_on_y_slope, x_on_y_intercept = np.polyfit(y_values, x_values, deg=1)

            # Invert to get y = mx + b form
            slope = 1.0 / x_on_y_slope if abs(x_on_y_slope) > 1e-10 else 0.0
            intercept = (
                -x_on_y_intercept / x_on_y_slope if abs(x_on_y_slope) > 1e-10 else 0.0
            )

            # Calculate R-squared
            y_pred = slope * x_values + intercept
            ss_res = np.sum((y_values - y_pred) ** 2)
            ss_tot = np.sum((y_values - np.mean(y_values)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 1e-10 else 0.0
            r_squared = max(0.0, min(1.0, r_squared))

            logger.debug(
                f"  📐 Reverse regression: y = {slope:.4f}x + {intercept:.4f}, R²={r_squared:.3f}"
            )

        elif regression_type == "deming":
            # === DEMING REGRESSION WITH ADJUSTABLE DELTA ===
            # Generalizes ODR by allowing user-controlled error weighting

            # Clamp bias to valid range
            regression_bias = np.clip(regression_bias, -10, 10)

            # Map bias to delta parameter: δ = 10^(-bias × bias_scale)
            delta = 10 ** (-regression_bias * bias_scale)

            # Calculate error weights for scipy.odr
            # Relationship: delta = sy² / sx²
            sx = 1.0
            sy = np.sqrt(delta)

            # Get initial parameter estimates using OLS
            initial_slope, initial_intercept = np.polyfit(x_values, y_values, deg=1)

            # Define linear model: y = beta[0] * x + beta[1]
            def linear_func(beta, x):
                return beta[0] * x + beta[1]

            linear_model = odr.Model(linear_func)

            # Create weighted ODR data object (Deming regression)
            data = odr.RealData(x_values, y_values, sx=sx, sy=sy)

            # Create and run ODR object
            odr_obj = odr.ODR(
                data, linear_model, beta0=[initial_slope, initial_intercept]
            )
            output = odr_obj.run()

            # Extract fitted parameters
            slope = output.beta[0]
            intercept = output.beta[1]

            # Calculate R-squared
            y_pred = slope * x_values + intercept
            ss_res = np.sum((y_values - y_pred) ** 2)
            ss_tot = np.sum((y_values - np.mean(y_values)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 1e-10 else 0.0
            r_squared = max(0.0, min(1.0, r_squared))

            logger.debug(
                f"  📐 Deming regression (bias={regression_bias:.1f}, δ={delta:.2e}): "
                f"y = {slope:.4f}x + {intercept:.4f}, R²={r_squared:.3f}"
            )

        elif regression_type == "pca":
            # === PCA REGRESSION ===
            # Principal Component Analysis - finds line of maximum variance
            # Treats X and Y symmetrically (no bias toward either axis)

            # Standardize data for PCA
            X = np.column_stack([x_values, y_values])

            # Apply PCA to find principal component (line of maximum variance)
            pca = PCA(n_components=1)
            pca.fit(X)

            # Extract principal component direction vector
            # components_[0] is the first principal component: [vx, vy]
            pc = pca.components_[0]

            # Calculate slope from principal component direction
            # Slope m = vy / vx (rise over run)
            slope = pc[1] / pc[0] if abs(pc[0]) > 1e-10 else 0.0

            # Calculate intercept by ensuring line passes through centroid
            # Centroid: (mean_x, mean_y)
            # Line equation: y - mean_y = slope * (x - mean_x)
            # Rearranged: y = slope * x + (mean_y - slope * mean_x)
            mean_x = np.mean(x_values)
            mean_y = np.mean(y_values)
            intercept = mean_y - slope * mean_x

            # Calculate R-squared
            y_pred = slope * x_values + intercept
            ss_res = np.sum((y_values - y_pred) ** 2)
            ss_tot = np.sum((y_values - np.mean(y_values)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 1e-10 else 0.0
            r_squared = max(0.0, min(1.0, r_squared))

            # Calculate explained variance ratio from PCA
            explained_var = pca.explained_variance_ratio_[0]

            logger.debug(
                f"  📐 PCA regression (variance explained={explained_var:.3f}): "
                f"y = {slope:.4f}x + {intercept:.4f}, R²={r_squared:.3f}"
            )

        else:
            logger.error(f"❌ Unknown regression type: {regression_type}")
            return None

        return slope, intercept, r_squared

    except Exception as e:
        logger.warning(f"⚠️ {regression_type} regression calculation failed: {e}")
        return None


def generate_investigation_series_plot(
    formation_name: str,
    csv_dict: Dict[str, pd.DataFrame],
    parameter_mappings: pd.DataFrame,
    parameter_display_name: str,
    output_folder: Path,
    location_details: pd.DataFrame,
    fallback_investigation_name: str,
    outlier_results: Optional[Dict[str, Dict[str, Any]]] = None,
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
        outlier_results: Optional outlier detection results
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

        # Apply outlier filtering (IQR-based outliers)
        if outlier_results and csv_name in outlier_results:
            outlier_indices = outlier_results[csv_name]["outlier_indices"]
            df_filtered = df[~df.index.isin(outlier_indices)]
        else:
            df_filtered = df.copy()

        # Apply additional filter column if specified (e.g., manual outliers)
        if filter_column and filter_column in df_filtered.columns:
            df_filtered = df_filtered[~df_filtered[filter_column]].copy()

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

    # === PLOTTING SECTION ===
    # Sort by test type order
    sorted_csv_items = sorted(
        csv_data_with_investigations.items(),
        key=lambda x: CONFIG["test_type_settings"].get(x[0], {}).get("order", 999),
    )

    # Track legend entries to avoid duplicates
    plotted_investigations = set()
    plotted_test_types = set()

    # === PLOT DATA POINTS BY TEST TYPE ===
    # Each test type uses its own plot_points setting from test_type_settings
    # CPT data uses additional threshold-based auto-plot logic

    for csv_name, data_info in sorted_csv_items:
        df_with_inv = data_info["df"]
        column_name = data_info["column_name"]

        # Get test type settings
        test_type_settings = CONFIG["test_type_settings"].get(
            csv_name, CONFIG["default_test_type_settings"]
        )

        if not test_type_settings["plotted"]:
            continue

        marker_style = test_type_settings["marker"]
        marker_size = test_type_settings["marker_size"]
        plot_alpha = test_type_settings["alpha"]

        # Get clean test type name for legend
        clean_test_name = csv_name.replace(" by Geology.csv", "").replace(".csv", "")

        # Plot each investigation within this test type
        for investigation in sorted(df_with_inv["Investigation"].unique()):
            inv_data = df_with_inv[df_with_inv["Investigation"] == investigation]

            param_values = inv_data[column_name].values
            depth_values = inv_data["Top Depth"].values

            if len(param_values) == 0:
                continue

            # Get investigation color
            inv_color = investigation_color_map[investigation]

            # Track investigations for legend (don't add label to scatter plot directly)
            if investigation not in plotted_investigations:
                plotted_investigations.add(investigation)

            # === PLOT POINTS DECISION LOGIC ===
            # Use per-test-type plot_points setting
            plot_points = test_type_settings.get("plot_points", True)

            # CPT Auto-Plot Override: If CPT data has fewer points than threshold, force plotting
            if csv_name == "CPT by Geology.csv" and not plot_points:
                cpt_threshold = test_type_settings.get("cpt_auto_plot_threshold", 50)
                if len(param_values) < cpt_threshold:
                    plot_points = True
                    logger.info(
                        f"  🔄 CPT Auto-Plot Override ({investigation}): {len(param_values)} points "
                        f"< {cpt_threshold} threshold - plotting enabled"
                    )

            # Plot scatter points if enabled (no label here - added separately with circle marker)
            if plot_points:
                # Get marker thickness from config (for markers like 'x' that have line thickness)
                marker_thickness = test_type_settings.get("marker_thickness", 1.0)

                ax.scatter(
                    param_values,
                    depth_values,
                    c=inv_color,
                    marker=marker_style,
                    s=marker_size,
                    alpha=plot_alpha,
                    edgecolors=marker_edgecolors,
                    linewidths=(
                        marker_thickness
                        if marker_style in ["x", "+"]
                        else marker_linewidths
                    ),
                )

            all_parameter_values.extend(param_values)
            all_depth_values.extend(depth_values)

    # === CPT DENSITY LINES BY INVESTIGATION ===
    # Process CPT data separately to add density lines per investigation
    logger.info(
        f"🔍 DEBUG: Checking CPT density lines - CSV files available: {list(csv_data_with_investigations.keys())}"
    )
    logger.info(
        f"🔍 DEBUG: Looking for 'CPT by Geology.csv' in dict: {'CPT by Geology.csv' in csv_data_with_investigations}"
    )

    if "CPT by Geology.csv" in csv_data_with_investigations:
        cpt_data = csv_data_with_investigations["CPT by Geology.csv"]
        cpt_df = cpt_data["df"]
        cpt_column = cpt_data["column_name"]

        logger.info(
            f"🔍 DEBUG: CPT data found - {len(cpt_df)} rows, column: {cpt_column}"
        )
        logger.info(
            f"🔍 DEBUG: CPT investigations: {sorted(cpt_df['Investigation'].unique())}"
        )

        # Get CPT test type settings for density line configuration
        cpt_test_type_settings = CONFIG["test_type_settings"].get(
            "CPT by Geology.csv", CONFIG["default_test_type_settings"]
        )
        density_line_settings = cpt_test_type_settings.get("density_line", {})

        logger.info(
            f"🔍 DEBUG: Density line settings: enabled={density_line_settings.get('enabled', False)}"
        )

        # Check if density lines are enabled for CPT data
        if density_line_settings.get("enabled", False):
            logger.info("🎨 Processing CPT density lines by investigation")

            # Extract styling parameters from config
            line_width = density_line_settings.get("linewidth", 2.5)
            line_style = density_line_settings.get("linestyle", "-")
            line_alpha = density_line_settings.get("alpha", 0.9)

            # Get auto-plot threshold and disable settings
            cpt_threshold = cpt_test_type_settings.get("cpt_auto_plot_threshold", 50)
            disable_density = cpt_test_type_settings.get(
                "cpt_auto_plot_disable_density", True
            )

            # Process each investigation's CPT data
            for investigation in sorted(cpt_df["Investigation"].unique()):
                inv_cpt_data = cpt_df[cpt_df["Investigation"] == investigation]

                cpt_param_values = inv_cpt_data[cpt_column].values
                cpt_depth_values = inv_cpt_data["Top Depth"].values

                if (
                    len(cpt_param_values)
                    < CONFIG["density_tracing"]["segment_detection"][
                        "min_segment_length"
                    ]
                ):
                    logger.debug(
                        f"  ⏭️ {investigation}: Insufficient CPT points for density line "
                        f"({len(cpt_param_values)} points)"
                    )
                    continue

                # === CPT AUTO-PLOT DENSITY DISABLE LOGIC ===
                # Skip density line if points were below threshold and disable_density is True
                if len(cpt_param_values) < cpt_threshold and disable_density:
                    logger.info(
                        f"  ⏭️ {investigation}: Density line disabled (auto-plot triggered: "
                        f"{len(cpt_param_values)} points < {cpt_threshold} threshold, "
                        f"cpt_auto_plot_disable_density=True)"
                    )
                    continue

                # Get investigation color
                inv_color = investigation_color_map[investigation]

                # No legend label needed - investigation color already shown with circle marker
                legend_label = None

                logger.info(
                    f"  🎨 Generating density line for {investigation}: "
                    f"{len(cpt_param_values)} CPT points"
                )

                # Use shared function to plot density lines
                density_plotted = plot_cpt_density_lines(
                    ax=ax,
                    depth_array=cpt_depth_values,
                    strength_array=cpt_param_values,
                    color=inv_color,
                    density_config=CONFIG["density_tracing"],
                    legend_label=legend_label,
                    linewidth=line_width,
                    linestyle=line_style,
                    alpha=line_alpha,
                    zorder=10,
                )

                if density_plotted:
                    logger.info(f"  ✅ Density line added for {investigation}")
                else:
                    logger.warning(f"  ⚠️ No density line generated for {investigation}")

    # === REGRESSION LINES PER TEST TYPE (Combining All Investigations) ===
    # Plot regression lines for test types where regression is enabled
    # Each regression line aggregates data from ALL investigations for that test type
    logger.info("� Checking regression settings for test types...")

    # Get global regression settings from CONFIG
    regression_type = CONFIG["regression"]["type"]
    regression_bias = CONFIG["regression"]["bias"]
    regression_bias_scale = CONFIG["regression"]["bias_scale"]
    regression_min_points = CONFIG["regression"]["min_points"]

    # Aggregate data by test type (combining all investigations)
    test_type_aggregated_data = {}

    for csv_name, data_info in csv_data_with_investigations.items():
        df_with_inv = data_info["df"]
        column_name = data_info["column_name"]

        # Get test type settings
        test_type_settings = CONFIG["test_type_settings"].get(
            csv_name, CONFIG["default_test_type_settings"]
        )

        # Check if regression is enabled for this test type
        if not test_type_settings.get("regression_enabled", False):
            continue

        # Aggregate all investigations' data for this test type
        param_values = df_with_inv[column_name].values
        depth_values = df_with_inv["Top Depth"].values

        test_type_aggregated_data[csv_name] = {
            "param_values": param_values,
            "depth_values": depth_values,
            "settings": test_type_settings,
            "column_name": column_name,
        }

        logger.info(
            f"  ✅ {csv_name}: Aggregated {len(param_values)} points from all investigations"
        )

    # Plot regression lines for each test type
    for csv_name, agg_data in test_type_aggregated_data.items():
        param_values = agg_data["param_values"]
        depth_values = agg_data["depth_values"]
        test_type_settings = agg_data["settings"]

        # Check if enough points for regression
        if len(param_values) < regression_min_points:
            logger.info(
                f"  ⏭️ {csv_name}: Insufficient points for regression "
                f"({len(param_values)} < {regression_min_points} min)"
            )
            continue

        logger.info(f"📈 Calculating regression for {csv_name}...")

        # Calculate regression using global settings
        regression_result = calculate_linear_regression(
            x_values=param_values,
            y_values=depth_values,
            regression_type=regression_type,
            regression_bias=regression_bias,
            bias_scale=regression_bias_scale,
            min_points=regression_min_points,
        )

        if regression_result is None:
            logger.warning(f"  ⚠️ {csv_name}: Regression calculation failed")
            continue

        slope, intercept, r_squared = regression_result

        # Generate regression line points using min/max y-values (depth) of source data
        # This ensures regression line only extends to the actual data extent
        y_min = np.min(depth_values)
        y_max = np.max(depth_values)
        y_reg = np.array([y_min, y_max])
        x_reg = (
            (y_reg - intercept) / slope
            if abs(slope) > 1e-10
            else np.array([np.mean(param_values), np.mean(param_values)])
        )

        # Extract regression line styling from per-test-type settings
        reg_linestyle = test_type_settings.get("regression_linestyle", "--")
        reg_linecolor = test_type_settings.get("regression_linecolor", "black")
        reg_linewidth = test_type_settings.get("regression_linewidth", 2.0)
        reg_alpha = test_type_settings.get("regression_alpha", 0.8)

        # Get clean test type name for legend
        clean_test_name = csv_name.replace(" by Geology.csv", "").replace(".csv", "")

        # Plot regression line with test type-specific color and style
        ax.plot(
            x_reg,
            y_reg,
            color=reg_linecolor,
            linestyle=reg_linestyle,
            linewidth=reg_linewidth,
            alpha=reg_alpha,
            label=f"{clean_test_name} (Regression)",
            zorder=5,  # Plot above scatter points but below legends
        )

        logger.info(
            f"  ✅ {csv_name}: Regression plotted (slope={slope:.4f}, intercept={intercept:.2f}, R²={r_squared:.3f})"
        )

    # === ADD INVESTIGATION COLOR LEGEND (with circle markers) ===
    # Add legend entries for investigation colors using simple circle markers
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
    # Create dummy invisible points for test type shapes (only if test type shapes legend is enabled)
    if CONFIG["investigation_series"]["legend"]["show_test_type_shapes"]:
        for csv_name, data_info in sorted_csv_items:
            test_type_settings = CONFIG["test_type_settings"].get(
                csv_name, CONFIG["default_test_type_settings"]
            )

            if not test_type_settings["plotted"]:
                continue

            # Only add shape legend if this test type actually plots something
            # (respects plot_points setting and CPT auto-plot threshold)
            test_plots_points = test_type_settings.get("plot_points", True)
            if not test_plots_points:
                # CPT has special handling: show legend if density lines OR points are plotted
                if csv_name == "CPT by Geology.csv":
                    cpt_threshold = test_type_settings.get(
                        "cpt_auto_plot_threshold", 50
                    )
                    density_enabled = test_type_settings.get("density_line", {}).get(
                        "enabled", False
                    )

                    # Check if any investigation has CPT data
                    cpt_df = csv_data_with_investigations.get(
                        "CPT by Geology.csv", {}
                    ).get("df")
                    if cpt_df is not None:
                        # Show CPT legend if:
                        # 1. Any investigation plots points (below threshold), OR
                        # 2. Density lines are enabled (for investigations above threshold)
                        any_below_threshold = any(
                            len(cpt_df[cpt_df["Investigation"] == inv]) < cpt_threshold
                            for inv in cpt_df["Investigation"].unique()
                        )
                        if not (any_below_threshold or density_enabled):
                            continue  # Skip only if no points plotted AND no density lines
                    else:
                        continue  # No CPT data at all
                else:
                    continue  # Skip non-CPT test types with plot_points=False

            marker_style = test_type_settings["marker"]
            marker_size = test_type_settings["marker_size"]
            clean_test_name = csv_name.replace(" by Geology.csv", "").replace(
                ".csv", ""
            )

            # For CPT, determine whether to show line or marker based on what's actually plotted
            if csv_name == "CPT by Geology.csv":
                cpt_threshold = test_type_settings.get("cpt_auto_plot_threshold", 50)
                cpt_df = csv_data_with_investigations.get("CPT by Geology.csv", {}).get(
                    "df"
                )

                # Check if any investigation plots points (below threshold) or lines (above threshold)
                any_points_plotted = False
                any_lines_plotted = False

                if cpt_df is not None:
                    for inv in cpt_df["Investigation"].unique():
                        inv_points = len(cpt_df[cpt_df["Investigation"] == inv])
                        if inv_points < cpt_threshold:
                            any_points_plotted = True
                        else:
                            any_lines_plotted = True

                # Show line and/or marker based on what's actually plotted
                # Always use specific labels "CPT Line" and "CPT Points" for clarity
                if any_lines_plotted:
                    # Density lines are drawn
                    density_line_settings = test_type_settings.get("density_line", {})
                    line_width = density_line_settings.get("linewidth", 2)
                    line_style = density_line_settings.get("linestyle", "-")

                    ax.plot(
                        [],
                        [],
                        color="gray",
                        linewidth=line_width,
                        linestyle=line_style,
                        alpha=0.7,
                        label=f"{clean_test_name} Line (shape)",
                    )

                if any_points_plotted:
                    # Scatter points are plotted
                    ax.scatter(
                        [],
                        [],
                        c="gray",
                        marker=marker_style,
                        s=marker_size,
                        alpha=0.7,
                        edgecolors=marker_edgecolors,
                        linewidths=marker_linewidths,
                        label=f"{clean_test_name} Points (shape)",
                    )
            else:
                # Add invisible marker with label for shape legend (non-CPT test types)
                ax.scatter(
                    [],
                    [],
                    c="gray",
                    marker=marker_style,
                    s=marker_size,
                    alpha=0.7,
                    edgecolors=marker_edgecolors,
                    linewidths=marker_linewidths,
                    label=f"{clean_test_name} (shape)",
                )

    # === AXIS CONFIGURATION ===
    if all_parameter_values and all_depth_values:
        x_max = max(all_parameter_values) * 1.1
        y_max = max(all_depth_values) + y_margin

        ax.set_xlim(left=x_limit_left, right=x_max)

        # Set y-axis limits based on invert_y setting (consistent with formation plots)
        if invert_y:
            # For inverted axis: top value is 0, bottom value is maximum (deepest)
            ax.set_ylim(top=0, bottom=y_max)
        else:
            # For normal axis: bottom is 0, top is maximum
            ax.set_ylim(bottom=0, top=y_max)

    # Set axis labels
    ax.set_xlabel(
        parameter_display_name,
        fontsize=x_label_size,
        weight=x_label_weight,
    )
    ax.set_ylabel(y_label, fontsize=y_label_size, weight=y_label_weight)

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

    # === PLOT TITLE ===
    if CONFIG["plot_title"]["enabled"]:
        title_text = f"{formation_name}"
        ax.set_title(
            title_text,
            fontsize=CONFIG["plot_title"]["font_size"],
            weight=CONFIG["plot_title"]["font_weight"],
            family=CONFIG["plot_title"]["font_family"],
            pad=CONFIG["plot_title"]["pad"],
        )

    # === LEGEND ===
    # Check if fixed-width legend is enabled
    legend_fixed_width = CONFIG["legend"].get("fixed_width", False)

    # Get legend handles and labels to calculate optimal layout
    handles, labels = ax.get_legend_handles_labels()
    num_entries = len(labels)

    # Calculate optimal number of columns to prevent text overlap
    # Max 3 columns, but reduce if fewer entries
    optimal_ncol = min(3, max(1, num_entries // 2))

    # Reduced font size for investigation series plots (many entries)
    legend_fontsize = 8

    if legend_fixed_width:
        # ABSOLUTE WIDTH MATCHING: Make legend exactly equal to axes width
        # Get axes position in figure coordinates
        fig.canvas.draw()  # Force draw to get accurate renderer
        ax_bbox = ax.get_position()  # Returns Bbox object with axes position

        # Calculate absolute bbox coordinates in axes coordinates
        # Legend will span from left edge (0) to right edge (1) of axes
        # Position further below plot to prevent overlap
        bbox_expand = (0, -0.15, 1, 0)  # (x_left, y, width, height) - more space below

        legend = ax.legend(
            loc="lower left",  # Anchor at bottom-left of bbox
            bbox_to_anchor=bbox_expand,
            bbox_transform=ax.transAxes,  # Use axes coordinate system
            edgecolor=legend_edgecolor,
            framealpha=0.9,
            ncol=optimal_ncol,  # Dynamic column count
            mode="expand",  # Expand legend to fill bbox width
            borderaxespad=0,  # No padding between legend and anchor point
            labelspacing=0.5,  # Reduced vertical space between entries
            borderpad=0.5,  # Reduced internal padding
            fontsize=legend_fontsize,  # Smaller font for many entries
            columnspacing=1.0,  # Horizontal space between columns
        )
    else:
        # Standard legend (auto-sized)
        legend = ax.legend(
            loc=legend_location,
            bbox_to_anchor=(0.5, -0.15),  # More space below plot
            edgecolor=legend_edgecolor,
            framealpha=0.9,
            ncol=optimal_ncol,  # Dynamic column count
            fontsize=legend_fontsize,  # Smaller font
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
    - Test-type marker shapes (from CONFIG test_type_settings)
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
        key=lambda x: CONFIG["test_type_settings"].get(x[0], {}).get("order", 999),
    )

    # Track which investigations have been added to legend (color-only legend)
    legend_investigations = set()

    # Track test types for checkbox generation
    test_types_in_formation = set()

    # Collect outlier data grouped by test type AND investigation (for later trace generation)
    # Structure: {csv_name: {investigation: {x: [], y: [], hover_text: [], marker_symbol: str}}}
    outliers_by_test_type_and_investigation = {}

    # === ADD DATA TRACES ===
    for csv_name, data_info in sorted_csv_items:
        df_with_inv = data_info["df"]
        param_column = data_info["param_column"]

        # Get test type settings
        test_type_settings = CONFIG["test_type_settings"].get(
            csv_name, CONFIG["default_test_type_settings"]
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
                # Initialize test type in outlier dict if not exists
                if csv_name not in outliers_by_test_type_and_investigation:
                    outliers_by_test_type_and_investigation[csv_name] = {}

                # Initialize investigation within test type if not exists
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

                # Add outlier data to this test type + investigation's collection
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

    # === ADD OUTLIER TRACES (BY TEST TYPE AND INVESTIGATION) ===
    # Outliers now maintain their test type association and marker symbols
    # They will be controlled by the test type checkboxes like regular data points
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
        test_type_settings = CONFIG["test_type_settings"].get(
            csv_name, CONFIG["default_test_type_settings"]
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

    # === OUTPUT CONTROL CONFIGURATION EXTRACTION ===
    # Extract output control settings as primitives (coordination boundary)
    output_control = extract_output_control_config()

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
                outlier_results=None,  # No filtering
            )
            plot_count += 1

        # Generate WITHOUT outliers plot
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
                outlier_results=outlier_results,  # Apply filtering
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
                outlier_results=outlier_results,  # Apply IQR filtering
                filter_column="is_manual_outlier",  # Also filter manual outliers
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
# � PHASE 4c: PER-INVESTIGATION PLOT GENERATION
# ═══════════════════════════════════════════════════════════════════════════


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


def _group_formation_data_by_investigation(
    formation_data: Dict[str, pd.DataFrame],
    location_details: pd.DataFrame,
    fallback_name: str,
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Split formation data by investigation source.

    Takes formation data (dict of CSV DataFrames for one formation) and groups
    it by investigation source, creating separate plot datasets for each
    investigation.

    Args:
        formation_data: Dict mapping CSV names to DataFrames for single formation
        location_details: DataFrame with Location ID -> Investigation mapping
        fallback_name: Default investigation name for missing/unmatched IDs

    Returns:
        Nested dict: {investigation_name: {csv_name: dataframe}}
        Empty dict if no data available
    """
    investigation_groups = {}

    for csv_name, csv_df in formation_data.items():
        if csv_df.empty:
            continue

        # Add investigation column to this CSV's data
        csv_with_inv = _add_investigation_column(
            csv_df, location_details, fallback_name
        )

        # Group by investigation
        for investigation, inv_group in csv_with_inv.groupby("Investigation"):
            if investigation not in investigation_groups:
                investigation_groups[investigation] = {}

            # Remove Investigation column before storing (not needed for plotting)
            inv_group_clean = inv_group.drop(columns=["Investigation"])
            investigation_groups[investigation][csv_name] = inv_group_clean

    return investigation_groups


# ═══════════════════════════════════════════════════════════════════════════
# �📋 PHASE 5: INVESTIGATION SOURCE TRACKING
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


def export_all_csvs_with_outliers(
    formation_groups: Dict[str, Dict[str, pd.DataFrame]],
    outlier_results_by_formation: Dict[str, Dict[str, Dict[str, Any]]],
    parameter_name: str,
    parameter_output_folder: Path,
    highlight_color: str,
    freeze_header: bool,
    output_control: Dict[str, Any],
) -> None:
    """
    Export all CSV data sources as Excel files with outlier highlighting.
    Creates ONE Excel file per test type (CSV source) containing ALL formations.

    Args:
        formation_groups: Nested dict of formation → CSV → DataFrame
        outlier_results_by_formation: Nested dict of formation → CSV → outlier results
        parameter_name: Name of parameter being analyzed
        parameter_output_folder: Base output folder for parameter
        highlight_color: ARGB color code for outlier highlighting
        freeze_header: Whether to freeze header row
        output_control: Output control configuration
    """
    # Check if output is enabled
    if not should_generate_data_export(
        "excel_with_highlighted_outliers", output_control
    ):
        logger.info("⏭️ Skipping Excel export (disabled in output_control)")
        return

    logger.info("🚀 Starting Excel export with highlighted outliers...")

    # Extract excel config from CONFIG
    excel_config = CONFIG["excel_export"]
    excel_folder = (
        parameter_output_folder
        / CONFIG["investigation_tracking"]["output"]["data_folder_name"]
        / excel_config["output_folder"]
    )
    excel_folder.mkdir(parents=True, exist_ok=True)

    # Reorganize data: Group by CSV source instead of formation
    # Structure: {csv_name: [(formation_name, df, outlier_indices), ...]}
    csv_source_data = defaultdict(list)

    for formation_name, csv_dict in formation_groups.items():
        formation_outliers = outlier_results_by_formation.get(formation_name, {})

        for csv_name, df in csv_dict.items():
            if df.empty:
                continue

            # Get outlier indices for this formation-CSV combination
            outlier_data = formation_outliers.get(csv_name, {})
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
            # outlier_indices contains DataFrame index values, not row numbers
            # We need to find the row position for each outlier index
            for outlier_idx in outlier_indices:
                if outlier_idx in df.index:
                    # Get the row position (0-based) within this formation's DataFrame
                    row_position = df.index.get_loc(outlier_idx)
                    # Adjust for combined DataFrame position
                    combined_row_number = row_position + current_row_offset
                    combined_outlier_row_numbers.add(combined_row_number)

            current_row_offset += len(df)

        # Concatenate all formation DataFrames for this test type
        combined_df = pd.concat(combined_df_list, ignore_index=True)

        # Create safe filename for test type
        safe_csv_name = csv_name.replace(" by Geology.csv", "").replace(" ", "_")
        excel_filename = f"{safe_csv_name}.xlsx"
        excel_path = excel_folder / excel_filename

        # Export to Excel with highlighting
        # Note: combined_outlier_row_numbers contains 0-based row positions
        # export_highlighted_excel expects DataFrame index values
        # Since we used ignore_index=True, the DataFrame indices ARE the row positions
        try:
            export_highlighted_excel(
                df=combined_df,
                output_path=excel_path,
                outlier_indices=combined_outlier_row_numbers,
                highlight_color=highlight_color,
                freeze_header=freeze_header,
            )

            outlier_count = len(combined_outlier_row_numbers)
            total_rows = len(combined_df)
            formation_count = len(formation_data_list)

            logger.info(
                f"  ✅ {csv_name}: {outlier_count}/{total_rows} outliers highlighted across {formation_count} formations"
            )
            total_files += 1

        except Exception as e:
            logger.error(f"  ❌ Failed to export {csv_name}: {str(e)}")
            continue

    logger.info(f"✅ Excel export complete: {total_files} files generated")
    logger.info(f"📁 Output folder: {excel_folder}")


def generate_excel_exports(
    formation_groups: Dict[str, Dict[str, pd.DataFrame]],
    parameter_mappings: pd.DataFrame,
    parameter_name: str,
    parameter_output_folder: Path,
) -> None:
    """
    Orchestrator function for Phase 6: Generate Excel exports with outlier highlighting.

    Args:
        formation_groups: Nested dict of formation → CSV → DataFrame
        parameter_mappings: Parameter mapping DataFrame
        parameter_name: Name of parameter being analyzed
        parameter_output_folder: Base output folder for parameter
    """
    logger.info("=" * 80)
    logger.info("📊 PHASE 6: EXCEL EXPORT WITH HIGHLIGHTED OUTLIERS")
    logger.info("=" * 80)

    # Extract configuration
    outlier_config = CONFIG["outlier_detection"]
    excel_config = CONFIG["excel_export"]
    output_control = extract_output_control_config()

    # Detect outliers per formation
    logger.info("🔍 Detecting outliers for all formations...")
    outlier_results_by_formation = {}

    for formation_name, csv_dict in formation_groups.items():
        outlier_results = detect_outliers_per_csv(
            csv_dict,
            parameter_mappings,
            formation_name,
            outlier_config,
        )
        outlier_results_by_formation[formation_name] = outlier_results

    # Export all CSVs with outlier highlighting
    export_all_csvs_with_outliers(
        formation_groups=formation_groups,
        outlier_results_by_formation=outlier_results_by_formation,
        parameter_name=parameter_name,
        parameter_output_folder=parameter_output_folder,
        highlight_color=excel_config["outlier_highlight_color"],
        freeze_header=excel_config["freeze_header_row"],
        output_control=output_control,
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
    - Phase 4: Plot Generation (Combined) ✅ COMPLETE
    - Phase 4c: Per-Investigation Plots ✅ COMPLETE
    - Phase 5: Investigation Tracking ✅ COMPLETE
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

        # === PHASE 3b: OUTLIER FILTERING (for data exports) ===
        logger.info("")
        parameter_display_name = CONFIG["parameter"]["display_name"]

        grouped_without_outliers = filter_outliers_from_formations(
            formation_groups,
            param_mappings,
        )

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ Phase 3b Complete: Outlier filtering complete")
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

        # === PHASE 4: INVESTIGATION SERIES PLOT GENERATION ===
        logger.info("")
        try:
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

        except Exception as phase4_error:
            logger.error(f"❌ Phase 4 failed: {str(phase4_error)}")
            logger.warning("⚠️ Continuing without investigation-series plots...")
            # Don't re-raise - allow workflow to complete without Phase 4

        # === PHASE 5: INVESTIGATION SOURCE TRACKING ===
        logger.info("")
        try:
            parameter_output = Path(output_folder) / parameter_name
            generate_investigation_summary(
                formation_groups,
                grouped_without_outliers,
                param_mappings,
                parameter_name,
                parameter_output,
            )

            logger.info("")
            logger.info("=" * 80)
            logger.info(
                "✅ Phase 5 Complete: Investigation tracking finished successfully"
            )
            logger.info("=" * 80)

        except Exception as phase5_error:
            logger.error(f"❌ Phase 5 failed: {str(phase5_error)}")
            logger.warning("⚠️ Continuing without investigation tracking...")
            # Don't re-raise - allow workflow to complete without Phase 5

        # === PHASE 6: EXCEL EXPORT WITH HIGHLIGHTED OUTLIERS ===
        logger.info("")
        try:
            parameter_output = Path(output_folder) / parameter_name
            generate_excel_exports(
                formation_groups,
                param_mappings,
                parameter_name,
                parameter_output,
            )

            logger.info("")
            logger.info("=" * 80)
            logger.info(
                "✅ Phase 6 Complete: Excel exports with highlighted outliers finished successfully"
            )
            logger.info("=" * 80)

        except Exception as phase6_error:
            logger.error(f"❌ Phase 6 failed: {str(phase6_error)}")
            logger.warning("⚠️ Continuing without Excel exports...")
            # Don't re-raise - allow workflow to complete without Phase 6

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


if __name__ == "__main__":
    main()

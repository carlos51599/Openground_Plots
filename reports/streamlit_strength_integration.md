# Streamlit Integration: Undrained Shear Strength Plots

## Overview

Successfully adapted the Undrained Shear Strength plotting script to work within the Streamlit app interface, matching the pattern used by the A-line plotting script. Users can now select between two plot types:
1. **A-line (Atterberg Limits)** - Plasticity charts
2. **Undrained Shear Strength** - Depth vs strength plots

## Changes Implemented

### 1. Added Streamlit Wrapper Function
**File**: `Plotting Scripts\Streamlit_UndrainedShearStrength.py`

Added `generate_strength_plots()` function at the end of the script (before `if __name__ == "__main__":`):
- Accepts `input_files` dictionary with mapping, location, and test data CSVs
- Accepts `output_dir` Path for output location
- Accepts optional `config_overrides` for UI configuration
- Returns dictionary with success status, plot count, formations processed, parameter name, and output folder
- Implements all 6 phases: parameter mapping extraction, CSV loading, formation grouping, outlier filtering, manual outlier marking (optional), investigation-series plot generation, investigation tracking, and Excel exports
- Handles Phase 3c (manual outlier marking) gracefully if Excel file doesn't exist

### 2. Updated Streamlit UI
**File**: `app.py`

#### Plot Type Selection
Added radio button selector at the top of the app to choose between "A-line" and "Undrained Shear Strength" plot types.

#### Dynamic Sidebar Content
Sidebar description and features list now changes based on selected plot type:
- **A-line**: Shows A-line specific features
- **Strength**: Shows strength plot features including manual outlier exclusion support

#### File Upload Section
Modified to handle different file requirements:
- **A-line**: Requires Classification by Geology CSV + Location Details CSV
- **Strength**: Requires Location Details CSV + multiple test data CSV files (SPT, CPT, Triaxial, etc.)

For strength plots, added multiple file uploader that accepts any number of test data CSV files.

#### Upload Status Display
Updated to show appropriate status based on plot type:
- **A-line**: Shows status for classification and location files
- **Strength**: Shows status for location file and lists all uploaded test data files with count

#### Configuration Options
Added manual outlier exclusion checkbox for strength plots in the Output Control section:
- Only appears when "Undrained Shear Strength" is selected
- Checkbox for "Manually Identified Excluded" plots

#### Results Generation
Modified the generate button and processing logic:
- Button text changes based on plot type
- File validation adapted for different requirements
- Calls appropriate generation function (`generate_aline_plots()` or `generate_strength_plots()`)
- Passes correct input file structure to each function

#### Download Filename
ZIP download filename now reflects plot type:
- **A-line**: `aline_plots.zip`
- **Strength**: `strength_plots.zip`

#### Footer Text
Footer message updates dynamically based on selected plot type.

### 3. Import Statement
Added import for the strength plotting function:
```python
from Streamlit_UndrainedShearStrength import generate_strength_plots
```

## Key Features

### Shared Capabilities
Both plot types support:
- IQR multiplier configuration (slider from 0.0 to 3.0)
- Plot resolution settings (150, 300, or 600 DPI)
- Investigation-based coloring
- Test type marker shapes
- Outlier detection and filtering
- Interactive HTML plots (Plotly)
- Investigation source tracking CSVs
- Excel exports with outlier highlighting

### Strength Plot Specific
- Support for multiple test data CSV files
- Manual outlier exclusion from Excel spreadsheet (optional)
- Three plot versions: with outliers, without outliers, and manually identified excluded

## Testing

The app was successfully launched and tested:
- Streamlit server started without errors
- UI components display correctly
- Plot type selection works as expected
- File upload sections adapt to plot type
- Available at: http://localhost:8502

## Usage Instructions

1. **Select Plot Type**: Choose between "A-line" or "Undrained Shear Strength" at the top
2. **Upload Files Tab**: 
   - Upload Location Details CSV (required for both)
   - For A-line: Upload Classification by Geology CSV
   - For Strength: Upload one or more test data CSV files
3. **Configuration Tab**: Adjust outlier detection, plot settings, and output options
4. **Results Tab**: Click generate button to create plots
5. **Download**: Download all results as a ZIP file

## Architecture Compliance

The implementation follows the modular architecture guidelines:
- **Thin UI Layer**: `app.py` contains only UI logic, no business logic
- **Thick Logic Layer**: All plot generation logic remains in the plotting scripts
- **Configuration Passing**: UI config overrides passed as parameters
- **Flat Structure**: No deep hierarchies, all modules at top level
- **Clear Separation**: Investigation tracking, Excel exports, and plot generation remain in plotting modules

## Output Structure

Both plot types generate organized output folders:
```
Output/
├── ALine/                              (for A-line plots)
│   ├── investigation_series/
│   │   ├── with_outliers/
│   │   ├── without_outliers/
│   │   └── plotly_with_outliers/
│   └── data/
│       ├── investigation_summary/
│       └── excel_highlighted/
└── UndrainedShearStrength/            (for strength plots)
    ├── investigation_series/
    │   ├── with_outliers/
    │   ├── without_outliers/
    │   ├── manually_identified_excluded/
    │   └── plotly_with_outliers/
    └── data/
        ├── investigation_summary/
        └── excel_highlighted/
```

## Future Enhancements

Potential improvements:
1. Add support for more plot types (e.g., other geotechnical parameters)
2. Implement plot preview in the UI before download
3. Add data quality checks and validation warnings
4. Support for custom color schemes per investigation
5. Export configuration to JSON for reproducibility

## Notes

- The parameter mapping CSV (`Global_Parameter_Mapping_Extraction_only_CORRECTED.csv`) must exist in the repo root
- Manual outlier exclusion requires `Identified Outliers.xlsx` in the repo root (optional)
- All configuration follows the same structure as standalone scripts
- Output control system allows selective generation of plots and data exports

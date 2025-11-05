# Geotechnical Plotting - Streamlit Web App

## Overview

This is a modular Streamlit web application for generating A-line (Atterberg Limits) plasticity charts from geotechnical CSV data.

## Architecture

The application follows **AI-Optimized Modular Architecture** with minimal changes to existing code:

```
app/
├── app.py                      # Streamlit UI (361 lines)
├── validation.py               # CSV validation (150 lines)
├── zip_utils.py                # ZIP packaging (63 lines)
├── test_module_structure.py    # Module structure tests
└── Plotting Scripts/
    └── Streamlit_A_line.py     # A-line plotting logic (4,970 lines - existing code)
```

### Design Principles

1. **Minimal Changes**: The existing `Streamlit_A_line.py` plotting script is preserved almost entirely intact
2. **CONFIG Stays Put**: Configuration remains inside the plotting script (not extracted to separate module)
3. **Thin UI Layer**: Streamlit-specific code isolated in `app.py`
4. **Small Support Modules**: Only validation and ZIP utilities extracted (<200 lines each)

## Module Responsibilities

### app.py
- **Responsibility**: Streamlit UI for file uploads, configuration, and results display
- **Delegates to**: Streamlit_A_line.py, validation.py, zip_utils.py
- **NO business logic** - pure UI layer

### Streamlit_A_line.py
- **Responsibility**: A-line plot generation from geotechnical CSV data
- **Changes**: Added `generate_aline_plots()` orchestrator function (wraps existing main())
- **Preserved**: All existing business logic, CONFIG dictionary, helper functions unchanged

### validation.py
- **Responsibility**: CSV file validation for required columns and data structure
- **Functions**: `validate_csv_files()`, `save_uploaded_files()`

### zip_utils.py
- **Responsibility**: Package outputs into downloadable ZIP archives
- **Functions**: `create_zip_archive()`

## Running the Application

### Prerequisites

Ensure you have the required Python packages installed:
```bash
pip install streamlit pandas numpy matplotlib plotly scipy scikit-learn openpyxl
```

### Launch the App

```bash
cd "c:\Users\dea29431\OneDrive - Rsk Group Limited\Documents\Geotech\Figures Streamlit\app"
streamlit run app.py
```

The app will open in your web browser at `http://localhost:8501`

## Using the Application

### Step 1: Upload Files

Upload three required CSV files:
1. **Parameter Mapping CSV**: Global parameter mapping file
2. **Location Details CSV**: Location ID to Investigation mapping
3. **Classification by Geology CSV**: Geology data with LiquidLimit and PlasticityIndex

### Step 2: Configure Settings

Adjust settings as needed:
- **IQR Multiplier**: Outlier detection threshold (default: 1.5)
- **Plot Resolution**: DPI setting (150, 300, or 600)
- **Output Control**: Enable/disable plots and data exports

### Step 3: Generate Plots

Click "Generate A-line Plots" to:
1. Validate all uploaded files
2. Process data with outlier detection
3. Generate investigation-series plots with:
   - Investigation-based coloring
   - Test type marker shapes
   - Geotechnical classification boundaries (A-line, U-line)
   - Soil classification labels
4. Download results as ZIP archive

## Features

### Plotting Features
- **Investigation-series plots**: Color by investigation, shape by test type
- **Outlier detection**: IQR-based filtering with configurable threshold
- **Classification boundaries**: A-line, U-line, plasticity ranges
- **Multiple output formats**: PNG images and interactive HTML plots

### Data Export Features
- **Investigation tracking**: CSV summaries of data sources
- **Excel exports**: Spreadsheets with outlier highlighting

### Output Structure

```
Output/
└── ALine/
    ├── investigation_series/
    │   ├── with_outliers/
    │   │   ├── Formation_1.png
    │   │   ├── Formation_1.html
    │   │   └── ...
    │   └── without_outliers/
    │       ├── Formation_1.png
    │       └── ...
    └── data/
        ├── investigation_summary_with_outliers.csv
        ├── investigation_summary_without_outliers.csv
        └── excel_highlighted/
            └── Classification.xlsx
```

## Testing

Run the module structure test:
```bash
cd "c:\Users\dea29431\OneDrive - Rsk Group Limited\Documents\Geotech\Figures Streamlit\app"
python test_module_structure.py
```

This verifies:
- Module count (<10 limit)
- Module sizes (<1,500 lines for new modules)
- Import integrity (no circular imports)
- Function signatures are correct

## Development Guidelines

### Adding New Plot Types

To add support for additional plot types (e.g., Consolidation, PSD):

1. **Create new plotting script** (e.g., `Streamlit_Consolidation.py`)
   - Copy existing structure from `Streamlit_A_line.py`
   - Keep CONFIG inside the plotting script
   - Add `generate_xxx_plots()` orchestrator function

2. **Update app.py**
   - Add plot type to sidebar selection
   - Import new plotting module
   - Add conditional logic for file uploads and processing

3. **Keep it modular**
   - Each plot type = separate module
   - Shared utilities can go in `validation.py` or `zip_utils.py`
   - NO shared configuration module (keep CONFIG in each plotter)

### Modular Architecture Limits

- ✅ Module count: <10 files
- ✅ New module max: <1,500 lines (existing Streamlit_A_line.py exempt)
- ✅ Function max: <75 lines
- ✅ Folder depth: 1 level (root only)
- ✅ No circular imports
- ✅ Type hints: 100% coverage for new code

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`, ensure you're running from the `app/` directory:
```bash
cd "c:\Users\dea29431\OneDrive - Rsk Group Limited\Documents\Geotech\Figures Streamlit\app"
```

### File Validation Errors

Check that uploaded CSVs have required columns:
- **Mapping CSV**: Parameter, CSV Source, Column Name
- **Location CSV**: LocationID (or Location ID), Investigation
- **Classification CSV**: LiquidLimit, PlasticityIndex, geology columns, depth columns

### Memory Issues

For large datasets:
- Reduce DPI setting (150 instead of 300/600)
- Disable data exports if not needed
- Process formations one at a time

## License

Internal tool for geotechnical data analysis.

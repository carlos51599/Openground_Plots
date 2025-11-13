# Dynamic File Mapping Fix

## Problem

The application was failing with a `KeyError: 'classification'` when users uploaded files and pressed "Generate Plots". The error occurred because the code hardcoded the expectation of a file with the key `"classification"`, but files were being stored with normalized keys based on their original filenames.

**Error:**
```
KeyError: 'classification' at line 1085 in app.py
```

## Root Cause

The issue had two parts:

1. **Hardcoded file expectations**: The plot generation code expected specific file keys like `"classification"`, but uploaded files were stored with normalized keys (e.g., `"classification by geology"`).

2. **Static file mapping**: The code didn't dynamically determine which uploaded files contained which parameters based on the mapping CSV.

## Solution

Implemented a **dynamic file-to-parameter mapping system** that:

1. Reads the `Global_Parameter_Mapping_Extraction_only_CORRECTED.csv` to determine which parameters are needed
2. Matches uploaded files to required parameters based on the mapping CSV
3. Passes the correct files to plot generation functions without hardcoded keys

### Changes Made

#### 1. New Function in `validation.py`

Added `map_uploaded_files_to_parameters()` function that:
- Takes uploaded files, mapping CSV path, and plot types
- Returns a dictionary mapping parameter names to file paths that contain them
- Example output: `{"LiquidLimit": [Path("classification.csv")], "PlasticityIndex": [Path("classification.csv")]}`

```python
def map_uploaded_files_to_parameters(
    uploaded_files: Dict[str, Path],
    mapping_path: Path,
    plot_types: List[str],
) -> Dict[str, List[Path]]:
    """
    Map uploaded files to parameters based on mapping CSV.
    """
```

#### 2. Updated `app.py` Plot Generation

**Before:**
```python
# Hardcoded expectation of 'classification' key
plot_input = {
    "mapping": input_files["mapping"],
    "location": input_files["location"],
    "classification": input_files["classification"],  # ❌ KeyError here
}
```

**After:**
```python
# Dynamic file discovery based on required parameters
param_file_mapping = map_uploaded_files_to_parameters(
    input_files, mapping_path, list(st.session_state.plot_types)
)

# Find files containing A-line parameters
aline_files = set()
for param in ["LiquidLimit", "PlasticityIndex"]:
    if param in param_file_mapping:
        aline_files.update(param_file_mapping[param])

# Build plot_input with discovered files
plot_input = {
    "mapping": input_files["mapping"],
    "location": input_files["location"],
}
for file_path in aline_files:
    file_key = normalize_filename(file_path.name)
    plot_input[file_key] = file_path
```

#### 3. Updated `Streamlit_A_line.py`

**Before:**
```python
# Expected hardcoded 'classification' key
CONFIG["parameter"]["csv_source_folder"] = str(
    input_files["classification"].parent
)
csv_files = [input_files["classification"]]
```

**After:**
```python
# Find CSV source folder from any data file
csv_source_folder = None
for key, file_path in input_files.items():
    if key not in ["mapping", "location"]:
        csv_source_folder = str(file_path.parent)
        break

# Collect all data CSV files dynamically
csv_files = [
    file_path
    for key, file_path in input_files.items()
    if key not in ["mapping", "location"]
]
```

## Benefits

1. **No Hardcoding**: Files are matched dynamically based on the mapping CSV
2. **Flexible**: Works with any file name as long as it contains the required parameters
3. **Scalable**: Easy to add new plot types and parameters
4. **Maintainable**: Single source of truth (mapping CSV) for file requirements
5. **User-Friendly**: Better error messages when required parameters are missing

## Testing

Created comprehensive test suite in `tests/test_dynamic_parameter_mapping.py`:

```
✅ Test: Filename normalization
✅ Test: Parameter mapping for A-line
✅ Test: Parameter mapping for Strength
🎉 All tests passed successfully!
```

## Verification Steps

To verify the fix works:

1. Start the Streamlit app
2. Select "A-line" plot type
3. Upload:
   - Location Details CSV
   - Classification by Geology CSV (or any file containing LiquidLimit and PlasticityIndex)
4. Click "Generate Plots"
5. ✅ Should work without KeyError

## Architecture Compliance

✅ **Modular Guidelines Met:**
- Function max: <75 lines ✅
- Module max: <1,500 lines ✅
- Type hints: 100% ✅
- No circular imports ✅
- Clear module responsibilities ✅

## Files Changed

1. `validation.py`: Added `map_uploaded_files_to_parameters()` and `_find_matching_uploaded_file()`
2. `app.py`: Updated plot generation logic to use dynamic file mapping
3. `Plotting Scripts/Streamlit_A_line.py`: Updated to accept flexible input structure
4. `tests/test_dynamic_parameter_mapping.py`: Added comprehensive test suite

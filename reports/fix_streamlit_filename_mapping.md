# Fix Summary: Streamlit App Not Producing Plots

## Problem

The Streamlit app was failing to generate plots with the error:
```
⚠️ classification.csv: No parameter mapping found, skipping
✅ Grouped data into 0 formations:
❌ No formation groups created
```

## Root Cause

The issue occurred due to a filename mismatch between:
1. **Parameter mappings** (Phase 1) - Referenced original CSV names like `"Classification by Geology.csv"`
2. **Saved files** (from Streamlit uploads) - Were saved with simplified keys like `"classification.csv"`
3. **Formation grouping** (Phase 3) - Could not match `"classification.csv"` against mappings for `"Classification by Geology.csv"`

### Flow of the Problem

```
Phase 1: Extract mappings
  → Mapping CSV lists: "Classification by Geology.csv"

Phase 2: Load CSVs
  → Streamlit saves uploaded file as: "classification.csv"
  → csv_data_dict key becomes: "classification.csv"

Phase 3: Group by formation
  → Tries to match "classification.csv" against mapping "Classification by Geology.csv"
  → No match found → Skip CSV → No formations created → No plots
```

## Solution

Applied a two-part fix:

### Part 1: Preserve Original Filenames (validation.py)

Modified `save_uploaded_files()` to save files with their original names instead of simplified keys:

**Before:**
```python
file_path = temp_dir / f"{key}{extension}"  # Saves as "classification.csv"
```

**After:**
```python
original_name = file_obj.name
file_path = temp_dir / original_name  # Saves as "Classification by Geology.csv"
```

### Part 2: Override CSV Source Folder (Streamlit_A_line.py)

Modified `generate_aline_plots()` to point `csv_source_folder` to the temp directory:

**Added:**
```python
# Override csv_source_folder to temp directory when running from Streamlit
original_csv_folder = CONFIG["parameter"]["csv_source_folder"]
if "classification" in input_files:
    CONFIG["parameter"]["csv_source_folder"] = str(input_files["classification"].parent)
```

**Restored in finally block:**
```python
finally:
    CONFIG["parameter"]["output_base_folder"] = original_output
    CONFIG["parameter"]["csv_source_folder"] = original_csv_folder
```

## How It Works Now

```
Phase 1: Extract mappings
  → Mapping CSV lists: "Classification by Geology.csv"

Phase 2: Load CSVs
  → Streamlit saves uploaded file as: "Classification by Geology.csv" ✅
  → csv_source_folder overridden to temp directory ✅
  → csv_data_dict key becomes: "Classification by Geology.csv" ✅

Phase 3: Group by formation
  → Matches "Classification by Geology.csv" against mapping ✅
  → CSV processed successfully ✅
  → Formations created ✅
  → Plots generated ✅
```

## Testing

Created diagnostic test (`tests/test_filename_mapping.py`) which validates:
1. ✅ Files are saved with original names
2. ✅ csv_source_folder override logic works correctly
3. ✅ Path construction matches mapping references

## Files Modified

1. **validation.py** - `save_uploaded_files()` function
   - Changed to preserve original filenames
   
2. **Plotting Scripts/Streamlit_A_line.py** - `generate_aline_plots()` function
   - Added csv_source_folder override
   - Added cleanup in finally block

## Impact

- ✅ No changes to existing standalone script functionality
- ✅ No changes to plotting logic or data processing
- ✅ Minimal changes - only affects file saving and path resolution
- ✅ Backward compatible - standalone execution unaffected

## Verification

Run the Streamlit app with the standard test files:
1. Upload "Classification by Geology.csv"
2. Upload "Location Details.csv"
3. Click "Generate A-line Plots"
4. Verify plots are generated successfully

Expected log output:
```
✅ Found 1 LiquidLimit + 1 PlasticityIndex mappings
✅ classification.csv: Successfully processed
✅ Grouped data into [N] formations:
✅ Plots generated successfully
```

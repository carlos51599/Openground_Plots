# Streamlit Cloud 'parameter_sources' Error Fix

## Problem Summary

**Error Message:** `Error loading file requirements: 'parameter_sources'`

**Environment:** Works on localhost but fails on Streamlit Cloud

## Root Cause Analysis

The error occurs when `file_requirements["parameter_sources"]` is accessed but the dictionary doesn't contain that key. This happens when:

1. **Missing Required Columns**: The mapping CSV is missing `parameter` or `csv_file` columns
2. **CSV Read Failure**: The CSV file cannot be read due to corruption or encoding issues
3. **File Not Found**: The mapping CSV file is not deployed to Streamlit Cloud
4. **Encoding Issues**: Different line endings or character encoding between Windows (localhost) and Linux (Streamlit Cloud)

## Changes Made

### 1. Enhanced Error Handling in `validation.py`

#### Function: `get_parameter_source_files()`

**Before:**
```python
# Read mapping CSV
mapping_df = pd.read_csv(mapping_path)
```

**After:**
```python
# Read mapping CSV with defensive error handling
try:
    mapping_df = pd.read_csv(mapping_path)
except Exception as e:
    raise ValueError(f"Failed to read mapping CSV: {str(e)}") from e

# Validate required columns exist
required_columns = ["parameter", "csv_file"]
missing_columns = [col for col in required_columns if col not in mapping_df.columns]
if missing_columns:
    raise ValueError(
        f"Mapping CSV missing required columns: {', '.join(missing_columns)}. "
        f"Found columns: {', '.join(mapping_df.columns)}"
    )
```

#### Function: `get_required_files_from_mapping()`

**Added:**
- Error context propagation
- Defensive key checking for `csv_file` in source dictionaries

### 2. Improved Error Messages in `app.py`

#### Tab 1: File Upload Section

**Before:**
```python
except Exception as e:
    st.error(f"Error loading file requirements: {str(e)}")
```

**After:**
```python
# Defensive check for required keys
if "parameter_sources" not in file_requirements:
    st.error(
        "❌ **Error:** Mapping CSV structure is incomplete. "
        "Missing 'parameter_sources' data. "
        "Please check that the mapping CSV has 'parameter' and 'csv_file' columns."
    )
    st.stop()

# Specific exception handlers
except FileNotFoundError as e:
    st.error(f"❌ **File Not Found:** {str(e)}")
    st.info(
        "ℹ️ The mapping CSV file should be in the same directory as app.py. "
        f"Expected location: `{mapping_path}`"
    )
except ValueError as e:
    st.error(f"❌ **Mapping CSV Error:** {str(e)}")
    st.info(
        "ℹ️ Please ensure the mapping CSV has the required columns: "
        "'parameter', 'csv_file', and optionally 'priority_rank'"
    )
except Exception as e:
    st.error(f"❌ **Error loading file requirements:** {str(e)}")
    st.info(
        "ℹ️ This may be due to:\n"
        "- Missing or corrupted mapping CSV file\n"
        "- Invalid CSV format\n"
        "- Missing required columns (parameter, csv_file)\n"
        f"- File path: `{mapping_path}`"
    )
```

### 3. Added File Existence Checks

Added debugging messages to help diagnose Streamlit Cloud issues:

```python
# Get dynamic file requirements from mapping CSV
mapping_path = app_dir / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"

# Add debugging for Streamlit Cloud
if not mapping_path.exists():
    st.error(
        f"❌ **Mapping CSV file not found!**\n\n"
        f"Expected location: `{mapping_path}`\n\n"
        f"App directory: `{app_dir}`\n\n"
        f"Files in app directory: {list(app_dir.glob('*.csv'))}"
    )
    st.stop()
```

## Why It Works on Localhost but Not on Streamlit Cloud

### Possible Reasons:

1. **File Deployment**
   - The mapping CSV might not be included in the git repository
   - Check `.gitignore` to ensure CSV files aren't excluded
   - Verify the file is committed and pushed to the remote repository

2. **Path Resolution**
   - Local development (Windows): `C:\Users\...\app\file.csv`
   - Streamlit Cloud (Linux): `/app/file.csv`
   - Using `Path(__file__).parent` should work correctly on both platforms

3. **CSV Encoding**
   - Windows typically uses `windows-1252` or `cp1252` encoding
   - Linux expects `UTF-8` encoding
   - Pandas usually handles this automatically, but edge cases can occur

4. **Line Endings**
   - Windows: `\r\n` (CRLF)
   - Linux: `\n` (LF)
   - Git should automatically convert these, but check `.gitattributes`

5. **Column Name Issues**
   - Extra whitespace in column names: `" parameter"` vs `"parameter"`
   - Case sensitivity on Linux: `"Parameter"` vs `"parameter"`
   - Our code now validates column names explicitly

## Testing Performed

Created comprehensive test suite in `tests/test_validation_error_handling.py`:

✅ Test 1: Missing 'parameter' column - **PASSED**
✅ Test 2: Missing 'csv_file' column - **PASSED**
✅ Test 3: Corrupted CSV file - **PASSED**
✅ Test 4: Valid CSV file - **PASSED**
✅ Test 5: Missing CSV file - **PASSED**
✅ Test 6: Error propagation in get_required_files_from_mapping - **PASSED**

## Recommendations for Deployment

### 1. Verify File is Committed

```powershell
git status
git add Global_Parameter_Mapping_Extraction_only_CORRECTED.csv
git commit -m "Ensure mapping CSV is included in deployment"
git push
```

### 2. Check File in Repository

Verify the file appears in your GitHub repository at:
`https://github.com/<username>/<repo>/blob/main/Global_Parameter_Mapping_Extraction_only_CORRECTED.csv`

### 3. Streamlit Cloud Logs

After deploying the updated code:
- Check Streamlit Cloud logs for the new error messages
- The enhanced error messages will show:
  - Exact file path being checked
  - List of CSV files actually present in the directory
  - Specific missing columns if applicable

### 4. If File is Missing on Streamlit Cloud

Create a `.gitattributes` file in the repository root:

```
# Ensure CSV files are included and use LF line endings
*.csv text eol=lf
```

Then recommit and push:

```powershell
git add .gitattributes
git commit -m "Add gitattributes for CSV files"
git push
```

## Verification Steps

After deployment:

1. Navigate to the **Upload Files** tab
2. Select a plot type (A-line or Strength)
3. Observe the error message if it still occurs
4. The new error message will show exactly what's missing:
   - File path being checked
   - List of CSV files in the directory
   - Specific column errors if the file exists but is invalid

## Summary

The error occurred because the code attempted to access `file_requirements["parameter_sources"]` without checking if that key exists. When the CSV file cannot be read (missing file, wrong format, missing columns), the dictionary is incomplete.

The fix adds:
1. ✅ Defensive validation of CSV structure
2. ✅ Clear, actionable error messages
3. ✅ File existence checks with debugging info
4. ✅ Proper exception handling with context
5. ✅ Specific error types (FileNotFoundError, ValueError)

This ensures that whether the issue is a missing file, corrupted data, or missing columns, you'll get a clear diagnostic message to resolve the deployment issue.

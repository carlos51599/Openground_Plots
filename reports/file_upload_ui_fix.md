# File Upload UI Fix - Multi-Select Plot Types

## Summary

Fixed the file upload UI to properly display all required files in a single "Required Files" section, regardless of which plot type(s) are selected. Removed the separate "Test Data Files" subsection that was confusing.

## Changes Made

### 1. Updated Upload Section Logic (`app.py` lines 780-838)

**Before:**
- Used if/else logic that only checked for "aline" vs "else"
- Created a separate "Test Data Files" subsection for strength plots
- Didn't properly handle multiple plot types

**After:**
- All required files now appear under "Required Files" section
- Dynamic description based on selected plot types
- Test Data Files uploader appears inline with other required files when strength is selected
- Properly handles single plot type or multiple plot types

### 2. Updated Upload Status Display (`app.py` lines 840-881)

**Before:**
- Used if/else logic that only showed files for one plot type at a time
- Excluded "classification" from test file count in else branch

**After:**
- Shows location status (always required)
- Shows classification status (when A-line selected)
- Shows test data files status (when Strength selected)
- All status indicators appear based on selected plot types
- Properly excludes all system files from test file count

## Behavior by Plot Type Selection

### A-line Only
**Required Files section shows:**
- 📍 Location Details CSV (always required)
- 📊 Classification by Geology CSV (A-line specific)

### Strength Only
**Required Files section shows:**
- 📍 Location Details CSV (always required)
- 📋 Test Data CSV Files (Strength specific, multi-file upload)

### Both A-line and Strength
**Required Files section shows:**
- 📍 Location Details CSV (always required)
- 📊 Classification by Geology CSV (A-line specific)
- 📋 Test Data CSV Files (Strength specific, multi-file upload)

## Testing

Created comprehensive test suite in `tests/test_file_upload_ui.py`:

✅ All validation tests pass:
- Single A-line plot validation
- Single Strength plot validation  
- Multi-select (A-line + Strength) validation
- List format compatibility

## Code Quality

✅ **Modular Guidelines Compliance:**
- Function max: <75 lines ✅
- Module max: <1,500 lines ✅
- Type hints: Present where required ✅
- No circular imports ✅
- Clear section markers maintained ✅
- Nesting depth: ≤4 ✅

## User Impact

**Improved User Experience:**
1. ✅ Clearer UI - all required files in one section
2. ✅ No confusing subsections
3. ✅ Proper multi-select support
4. ✅ Dynamic descriptions based on selections
5. ✅ Upload status shows all relevant files

**No Breaking Changes:**
- Validation logic unchanged
- File storage mechanism unchanged
- Backend processing unchanged

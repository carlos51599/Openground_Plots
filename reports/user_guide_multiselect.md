# User Guide: Multi-Select Plot Type Feature

## Overview

The Geotechnical Plotting Application now supports generating multiple plot types simultaneously! You can select both A-line and Undrained Shear Strength plots in a single operation.

## How to Use

### Step 1: Select Plot Type(s)

At the top of the application, you'll see two checkboxes:

- ☑️ **📊 A-line (Atterberg Limits)** - Generates plasticity classification charts
- ☑️ **📈 Undrained Shear Strength** - Generates strength vs depth plots

**You can:**
- Select one plot type (single-select mode)
- Select both plot types (multi-select mode)
- Deselect all (you'll see a warning to select at least one)

### Step 2: Upload Files

Navigate to the **Upload Files** tab. The required files will change based on your selections:

#### For A-line Only:
- ✅ Location Details CSV (required)
- ✅ Classification by Geology CSV (required)

#### For Strength Only:
- ✅ Location Details CSV (required)
- ✅ Test Data CSVs (at least one):
  - Unconsolidated Undrained Triaxial
  - Consolidated Undrained Triaxial
  - Hand Vane
  - Fall Cone
  - Unconsolidated Undrained (UU)
  - Other Test Types

#### For Both A-line + Strength:
- ✅ Location Details CSV (required)
- ✅ Classification by Geology CSV (required for A-line)
- ✅ Test Data CSVs (required for Strength)

**Note:** The upload section dynamically shows only the file uploaders you need!

### Step 3: Configure Settings

Navigate to the **Configuration** tab:

- **IQR Multiplier** (0.0 - 3.0) - Controls outlier detection sensitivity
- **Plot Resolution** (DPI) - Choose 150, 300, or 600 DPI
- **Output Control:**
  - Generate Plots (with/without outliers, interactive HTML)
  - Generate Data Exports (CSV, Excel with highlighting)

**When multiple plot types are selected**, you'll see a notice that settings apply to all types.

### Step 4: Generate Plots

Navigate to the **Generate Results** tab:

1. Review the upload status summary
2. Click the generate button:
   - Single type: "🚀 Generate A-line Plots" or "🚀 Generate Strength Plots"
   - Both types: "🚀 Generate All Plots"

### Step 5: Download Results

After generation completes, you'll see:

**Results Summary:**
- **Formations Processed** - Total unique formations from all plot types
- **Plots Generated** - Total number of plots created
- **Parameters** - List of parameters analyzed

**Download Options:**
- Single type: Download `aline_plots.zip` or `strength_plots.zip`
- Both types: Download `geotechnical_plots.zip` (contains both plot types in separate folders)

## ZIP Archive Structure

### Single Plot Type:
```
aline_plots.zip
├── investigation_1/
│   ├── plots/
│   └── data/
└── investigation_2/
    ├── plots/
    └── data/
```

### Multiple Plot Types:
```
geotechnical_plots.zip
├── aline/
│   ├── investigation_1/
│   │   ├── plots/
│   │   └── data/
│   └── investigation_2/
│       ├── plots/
│       └── data/
└── strength/
    ├── investigation_1/
    │   ├── plots/
    │   └── data/
    └── investigation_2/
        ├── plots/
        └── data/
```

## Benefits of Multi-Select

### Time Savings
- **Before:** Generate A-line plots → Download → Go back → Select Strength → Upload files again → Generate → Download
- **After:** Select both → Upload all files once → Generate once → Download everything

### Consistency
- Same configuration settings applied to all plot types
- Same formations processed across all types
- Unified results package

### Flexibility
- Still works exactly the same for single plot types
- No need to select both if you only need one
- Easy to switch between modes

## Tips & Tricks

1. **Start with Single Type:** If you're new to the tool, try generating one plot type first to understand the workflow

2. **File Organization:** When selecting both types, upload all required files at once to avoid back-and-forth

3. **Check Upload Status:** The colored status indicators show what's uploaded:
   - 🟢 Green = All required files uploaded
   - 🟡 Yellow = Some files uploaded, more needed
   - 🔴 Red = No files uploaded yet

4. **Configuration Presets:** Set your preferred DPI and outlier settings before generating - they'll apply to all selected plot types

5. **Previous Results:** Your previous generation results are shown at the bottom of the Generate Results tab for reference

## Troubleshooting

### "Please select at least one plot type"
- You haven't checked any plot type checkboxes
- Check at least one box to continue

### "Please upload all required files"
- You're missing required CSV files for the selected plot type(s)
- Check the Upload Files tab for red status indicators

### Generation fails for one plot type but not the other
- When both are selected, if one fails, you'll see which one had the error
- Results from the successful plot type are still available
- Review the error message to fix the failing type

### ZIP file is very large
- High DPI settings create larger files
- Multiple plot types = more content
- Consider reducing DPI if file size is a concern

## Advanced Features

### Selective Generation
If you've uploaded files for both A-line and Strength but only want to generate one:
1. Uncheck the plot type you don't want
2. The app will remember your uploaded files
3. Generate the plot type you want
4. Check the other box later to generate the second type

### Batch Processing
For multiple projects:
1. Select both plot types
2. Upload first project's files
3. Generate and download
4. Clear files (refresh page or click X on file uploaders)
5. Upload next project's files
6. Repeat

## Getting Help

If you encounter issues:
1. Check the error messages in the app - they're designed to be specific and helpful
2. Verify your CSV files match the required format
3. Try generating one plot type at a time to isolate issues
4. Check the logs folder for detailed error information

## What's Next?

Future enhancements planned:
- Progress bars showing generation status for each plot type
- Ability to preview plots before downloading
- Option to download A-line and Strength results separately when both are generated
- Additional plot types (cohesion, unit weight, etc.)

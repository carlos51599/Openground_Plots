"""
MODULE: app.py

RESPONSIBILITY:
    Streamlit UI for geotechnical plotting. Handles file uploads,
    configuration UI, and result display. NO business logic.

DELEGATES TO:
    - Plotting Scripts/Streamlit_A_line.py: A-line plot generation
    - validation.py: CSV file validation
    - zip_utils.py: ZIP archive creation
"""

import streamlit as st
from pathlib import Path
import tempfile
from typing import Dict, Any
import sys

# Add directories to path for imports
app_dir = Path(__file__).parent
plotting_scripts_dir = app_dir / "Plotting Scripts"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(plotting_scripts_dir))

from validation import validate_csv_files, save_uploaded_files
from zip_utils import create_zip_archive
from Streamlit_A_line import generate_aline_plots


# ═════════════════════════════════════════════════════════════════════════
# ═════ PAGE CONFIGURATION ═════
# ═════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Geotechnical Plotting Tool", page_icon="🏗️", layout="wide"
)


# ═════════════════════════════════════════════════════════════════════════
# ═════ SESSION STATE INITIALIZATION ═════
# ═════════════════════════════════════════════════════════════════════════

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}

if "processing_results" not in st.session_state:
    st.session_state.processing_results = None

if "config_overrides" not in st.session_state:
    st.session_state.config_overrides = {}


# ═════════════════════════════════════════════════════════════════════════
# ═════ UI LAYOUT ═════
# ═════════════════════════════════════════════════════════════════════════

st.title("🏗️ Geotechnical Plotting Application")
st.markdown(
    "Generate A-line (Atterberg Limits) plasticity charts from geotechnical data"
)

# Sidebar
with st.sidebar:
    st.header("About")
    st.markdown(
        """
    This tool generates A-line (plasticity) charts from geotechnical CSV data.
    
    **Features:**
    - Investigation-based coloring
    - Test type marker shapes
    - Outlier detection and filtering
    - Interactive HTML plots
    - Excel exports with highlighting
    """
    )

    st.markdown("---")
    st.markdown("**Plot Type:** A-line (Atterberg)")

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📁 Upload Files", "⚙️ Configuration", "📊 Results"])

# ═════════════════════════════════════════════════════════════════════════
# ═════ TAB 1: FILE UPLOAD ═════
# ═════════════════════════════════════════════════════════════════════════

with tab1:
    st.header("Upload Data Files")
    st.markdown("Upload the required CSV files for A-line plot generation")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Required Files")

        st.session_state.uploaded_files["mapping"] = st.file_uploader(
            "📋 Parameter Mapping CSV",
            type=["csv"],
            key="mapping_upload",
            help="Global parameter mapping file (e.g., Global_Parameter_Mapping_Extraction_only_CORRECTED.csv)",
        )

        st.session_state.uploaded_files["location"] = st.file_uploader(
            "📍 Location Details CSV",
            type=["csv"],
            key="location_upload",
            help="Location Details CSV with Location ID and Investigation columns",
        )

        st.session_state.uploaded_files["classification"] = st.file_uploader(
            "🔬 Classification by Geology CSV",
            type=["csv"],
            key="classification_upload",
            help="Classification by Geology CSV with LiquidLimit and PlasticityIndex data",
        )

    with col2:
        st.subheader("Upload Status")

        # Show upload status
        for file_key, file_obj in st.session_state.uploaded_files.items():
            if file_obj:
                st.success(f"✅ {file_key.title()}: {file_obj.name}")
            else:
                st.warning(f"⚠️ {file_key.title()}: Not uploaded")

        # Validation button
        if st.button("🔍 Validate Files", type="secondary"):
            validation_result = validate_csv_files(st.session_state.uploaded_files)

            if validation_result["is_valid"]:
                st.success("✅ All files validated successfully!")
            else:
                st.error("❌ Validation failed:")
                for error in validation_result["errors"]:
                    st.error(f"  • {error}")

            if validation_result["warnings"]:
                st.warning("⚠️ Warnings:")
                for warning in validation_result["warnings"]:
                    st.warning(f"  • {warning}")


# ═════════════════════════════════════════════════════════════════════════
# ═════ TAB 2: CONFIGURATION ═════
# ═════════════════════════════════════════════════════════════════════════

with tab2:
    st.header("Plot Configuration")
    st.markdown("Customize outlier detection and plot appearance settings")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Outlier Detection")

        iqr_multiplier = st.slider(
            "IQR Multiplier",
            min_value=1.0,
            max_value=3.0,
            value=1.5,
            step=0.1,
            help="Multiplier for IQR outlier detection (default: 1.5 per Tukey's method)",
        )

        # Store in config overrides
        if "outlier_detection" not in st.session_state.config_overrides:
            st.session_state.config_overrides["outlier_detection"] = {
                "method_settings": {"standard_iqr": {"iqr_multiplier": iqr_multiplier}}
            }
        else:
            st.session_state.config_overrides["outlier_detection"]["method_settings"][
                "standard_iqr"
            ]["iqr_multiplier"] = iqr_multiplier

        st.info(f"Current IQR multiplier: {iqr_multiplier}")

    with col2:
        st.subheader("Plot Settings")

        dpi = st.selectbox(
            "Plot Resolution (DPI)",
            options=[150, 300, 600],
            index=1,
            help="Higher DPI = better quality but larger file size",
        )

        # Store in config overrides
        if "plotting" not in st.session_state.config_overrides:
            st.session_state.config_overrides["plotting"] = {"figure": {"dpi": dpi}}
        else:
            if "figure" not in st.session_state.config_overrides["plotting"]:
                st.session_state.config_overrides["plotting"]["figure"] = {}
            st.session_state.config_overrides["plotting"]["figure"]["dpi"] = dpi

        st.info(f"Current DPI: {dpi}")

    st.markdown("---")

    # Output control
    st.subheader("Output Control")

    col3, col4 = st.columns(2)

    with col3:
        enable_plots = st.checkbox("Generate Plots", value=True)
        if enable_plots:
            enable_with_outliers = st.checkbox("  • With Outliers", value=True)
            enable_without_outliers = st.checkbox("  • Without Outliers", value=True)
            enable_plotly = st.checkbox("  • Interactive HTML", value=True)

    with col4:
        enable_data = st.checkbox("Generate Data Exports", value=False)
        if enable_data:
            enable_csv = st.checkbox("  • Investigation CSV", value=True)
            enable_excel = st.checkbox("  • Excel with Highlighting", value=True)

    # Store output control in config overrides
    if "output_control" not in st.session_state.config_overrides:
        st.session_state.config_overrides["output_control"] = {}

    st.session_state.config_overrides["output_control"]["enabled"] = True
    st.session_state.config_overrides["output_control"]["plots"] = {
        "enabled": enable_plots,
        "investigation_series_plots_with_outliers": (
            enable_with_outliers if enable_plots else False
        ),
        "investigation_series_plots_without_outliers": (
            enable_without_outliers if enable_plots else False
        ),
        "investigation_series_plots_plotly_with_outliers": (
            enable_plotly if enable_plots else False
        ),
    }
    st.session_state.config_overrides["output_control"]["data"] = {
        "enabled": enable_data,
        "investigation_summary_csv": enable_csv if enable_data else False,
        "excel_with_highlighted_outliers": enable_excel if enable_data else False,
    }


# ═════════════════════════════════════════════════════════════════════════
# ═════ TAB 3: RESULTS ═════
# ═════════════════════════════════════════════════════════════════════════

with tab3:
    st.header("Generate Plots")

    # Check if all files are uploaded
    all_files_uploaded = all(
        st.session_state.uploaded_files.get(key) is not None
        for key in ["mapping", "location", "classification"]
    )

    if not all_files_uploaded:
        st.warning("⚠️ Please upload all required files in the Upload Files tab")
    else:
        # Generate plots button
        if st.button(
            "🚀 Generate A-line Plots", type="primary", use_container_width=True
        ):
            # Validate files first
            validation_result = validate_csv_files(st.session_state.uploaded_files)

            if not validation_result["is_valid"]:
                st.error("❌ Validation failed:")
                for error in validation_result["errors"]:
                    st.error(f"  • {error}")
                st.stop()

            # Show warnings if any
            if validation_result["warnings"]:
                st.warning("⚠️ Warnings:")
                for warning in validation_result["warnings"]:
                    st.warning(f"  • {warning}")

            # Process with progress indicator
            with st.spinner("Processing data and generating plots..."):
                try:
                    # Create temporary directory for processing
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_path = Path(temp_dir)

                        # Save uploaded files
                        input_files = save_uploaded_files(
                            st.session_state.uploaded_files, temp_path
                        )

                        # Create output directory
                        output_dir = temp_path / "output"
                        output_dir.mkdir(exist_ok=True)

                        # Generate plots
                        results = generate_aline_plots(
                            input_files=input_files,
                            output_dir=output_dir,
                            config_overrides=st.session_state.config_overrides,
                        )

                        # Store results in session state
                        st.session_state.processing_results = results

                        if results["success"]:
                            st.success("✅ Plots generated successfully!")

                            # Show results summary
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric(
                                    "Formations Processed",
                                    len(results["formations_processed"]),
                                )
                            with col2:
                                st.metric("Plots Generated", results["plots_generated"])
                            with col3:
                                st.metric("Parameter", results["parameter_name"])

                            # List formations
                            if results["formations_processed"]:
                                st.subheader("Processed Formations")
                                for formation in results["formations_processed"]:
                                    st.write(f"  • {formation}")

                            # Create ZIP for download
                            st.subheader("Download Results")
                            zip_buffer = create_zip_archive(results["output_folder"])

                            st.download_button(
                                label="📦 Download All Results (ZIP)",
                                data=zip_buffer,
                                file_name="aline_plots.zip",
                                mime="application/zip",
                                use_container_width=True,
                            )

                        else:
                            st.error(f"❌ Plot generation failed: {results['error']}")

                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    import traceback

                    with st.expander("Show error details"):
                        st.code(traceback.format_exc())

    # Show previous results if available
    if (
        st.session_state.processing_results
        and st.session_state.processing_results["success"]
    ):
        st.markdown("---")
        st.subheader("Previous Results")
        results = st.session_state.processing_results

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Formations", len(results["formations_processed"]))
        with col2:
            st.metric("Plots", results["plots_generated"])
        with col3:
            st.metric("Parameter", results["parameter_name"])


# ═════════════════════════════════════════════════════════════════════════
# ═════ FOOTER ═════
# ═════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(
    "**Geotechnical Plotting Tool** | A-line (Atterberg Limits) Chart Generator"
)

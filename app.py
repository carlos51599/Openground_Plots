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
from typing import Dict, Any, List
import sys

# Add directories to path for imports
app_dir = Path(__file__).parent
plotting_scripts_dir = app_dir / "Plotting Scripts"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(plotting_scripts_dir))

from validation import (
    validate_csv_files,
    save_uploaded_files,
    get_required_files_from_mapping,
    get_file_upload_label,
    normalize_filename,
    map_uploaded_files_to_parameters,
)
from zip_utils import create_zip_archive
from Streamlit_A_line import generate_aline_plots
from Streamlit_UndrainedShearStrength import generate_strength_plots


# ═════════════════════════════════════════════════════════════════════════
# ═════ UI COLOR CONFIGURATION ═════
# ═════════════════════════════════════════════════════════════════════════

UI_CONFIG = {
    "primary_color": "#17CED4FF",  # Purple - used for selected buttons, active states
    "primary_dark": "#14AC97FF",  # Darker purple for hover states
}


def hex_to_rgb(hex_color: str) -> str:
    """
    Convert hex color to RGB string for use in rgba() CSS.

    Args:
        hex_color: Hex color string (e.g., "#8B5CF6")

    Returns:
        RGB string (e.g., "139, 92, 246")
    """
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"{r}, {g}, {b}"


# ═════════════════════════════════════════════════════════════════════════
# ═════ PAGE CONFIGURATION ═════
# ═════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Geotechnical Plotting Tool", page_icon="🏗️", layout="wide"
)

# ═════════════════════════════════════════════════════════════════════════
# ═════ CUSTOM STYLING ═════
# ═════════════════════════════════════════════════════════════════════════

# Load and encode background image
background_path = app_dir / "assets" / "BackgroundWhite.jpg"
logo_path = app_dir / "assets" / "BinniesLogoDark.png"

if background_path.exists():
    import base64

    with open(background_path, "rb") as f:
        bg_data = base64.b64encode(f.read()).decode()

    # Compute RGB values for CSS
    primary_color_rgb = hex_to_rgb(UI_CONFIG["primary_color"])
    primary_dark_rgb = hex_to_rgb(UI_CONFIG["primary_dark"])

    # Add custom CSS for light theme glassmorphism design
    st.markdown(
        f"""
        <style>
        /* Background image */
        .stApp {{
            background-image: url('data:image/jpg;base64,{bg_data}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        
        /* ═════ TOP HEADER BAR STYLING ═════ */
        /* Styles the Streamlit top toolbar/header (contains hamburger menu, deploy button, etc.) */
        /* The header uses data-testid="stHeader" and can be customized with CSS */
        header[data-testid="stHeader"] {{
            background: rgba(255, 255, 255, 0.85) !important;
            backdrop-filter: blur(20px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
            border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important;
        }}
        
        /* Header toolbar buttons and icons */
        header[data-testid="stHeader"] button {{
            color: #1f2937 !important;
        }}
        
        header[data-testid="stHeader"] svg {{
            fill: #1f2937 !important;
        }}
        
        /* Glassmorphism effect for main container */
        .main .block-container {{
            background: rgba(255, 255, 255, 0.75);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border-radius: 20px;
            border: 1px solid rgba(0, 0, 0, 0.1);
            padding: 2.5rem;
            margin-top: 1rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
        }}
        
        /* Make all text dark for light background */
        .stApp {{
            color: #1f2937;
        }}
        
        /* Headers styling - dark text with subtle shadow */
        h1, h2, h3, h4, h5, h6 {{
            color: #111827 !important;
            font-weight: 700 !important;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        /* Main title styling */
        h1 {{
            font-size: 2.5rem !important;
            margin-bottom: 0.5rem !important;
            letter-spacing: 0.5px;
        }}
        
        /* Radio buttons and checkboxes - light glassmorphic cards */
        .stRadio, .stCheckbox {{
            background: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid rgba(0, 0, 0, 0.1);
        }}
        
        .stRadio label, .stCheckbox label {{
            color: #1f2937 !important;
            font-weight: 500 !important;
        }}
        
        /* All paragraph text */
        p, span, div {{
            color: #1f2937 !important;
        }}
        
        /* Button styling - uses UI_CONFIG colors */
        .stButton button {{
            background: linear-gradient(135deg, {UI_CONFIG['primary_color']}, {UI_CONFIG['primary_dark']}) !important;
            color: #ffffff !important;
            border: 2px solid {UI_CONFIG['primary_color']} !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            backdrop-filter: blur(10px) !important;
            box-shadow: 0 4px 15px rgba({primary_color_rgb}, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
            transition: all 0.3s ease !important;
            min-height: 3rem !important;
            font-size: 1.1rem !important;
        }}
        
        .stButton button:hover {{
            background: linear-gradient(135deg, {UI_CONFIG['primary_dark']}, {UI_CONFIG['primary_dark']}) !important;
            box-shadow: 0 6px 20px rgba({primary_color_rgb}, 0.5),
                        inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
            transform: translateY(-2px) !important;
        }}
        
        /* Plot type selection buttons - extra large and prominent */
        button[key="btn_aline"], button[key="btn_strength"] {{
            min-height: 5rem !important;
            font-size: 1.3rem !important;
            padding: 1.5rem !important;
        }}
        
        /* Primary button (selected state) - uses UI_CONFIG colors */
        button[data-baseweb="button"][kind="primary"],
        button[data-testid="stBaseButton-primary"] {{
            background: linear-gradient(135deg, {UI_CONFIG['primary_color']}, {UI_CONFIG['primary_dark']}) !important;
            color: #ffffff !important;
            box-shadow: 0 8px 25px rgba({primary_color_rgb}, 0.4),
                        inset 0 2px 0 rgba(255, 255, 255, 0.3),
                        0 0 30px rgba({primary_color_rgb}, 0.2) !important;
            border: 3px solid {UI_CONFIG['primary_color']} !important;
            transform: scale(1.02) !important;
        }}
        
        /* Target text inside primary button to ensure white color */
        button[data-testid="stBaseButton-primary"] p,
        button[data-testid="stBaseButton-primary"] span,
        button[data-testid="stBaseButton-primary"] div {{
            color: #ffffff !important;
        }}
        
        /* Secondary button (unselected state) - light gray with dark text */
        button[data-baseweb="button"][kind="secondary"],
        button[data-testid="stBaseButton-secondary"] {{
            background: rgba(243, 244, 246, 0.9) !important;
            color: #6b7280 !important;
            border: 2px solid rgba(209, 213, 219, 1) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
            backdrop-filter: blur(10px) !important;
        }}
        
        /* Target text inside secondary button */
        button[data-testid="stBaseButton-secondary"] p {{
            color: #6b7280 !important;
        }}
        
        button[data-baseweb="button"][kind="secondary"]:hover,
        button[data-testid="stBaseButton-secondary"]:hover {{
            background: rgba(229, 231, 235, 1) !important;
            border-color: rgba({primary_color_rgb}, 0.5) !important;
            box-shadow: 0 4px 12px rgba({primary_color_rgb}, 0.2) !important;
        }}
        
        /* Hover text brightness */
        button[data-testid="stBaseButton-secondary"]:hover p {{
            color: #374151 !important;
        }}
        
        /* File uploader - light glass card */
        .stFileUploader {{
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 1.5rem;
            border: 1px solid rgba(0, 0, 0, 0.1);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}
        
        .stFileUploader label {{
            color: #1f2937 !important;
            font-weight: 600 !important;
        }}
        
        /* File uploader drop zone - light background with purple border */
        .stFileUploader > div > div {{
            background: rgba(249, 250, 251, 1) !important;
            backdrop-filter: blur(15px) !important;
            border: 2px dashed rgba({primary_color_rgb}, 0.6) !important;
            border-radius: 12px !important;
            transition: all 0.3s ease !important;
        }}
        
        .stFileUploader > div > div:hover {{
            background: rgba(243, 244, 246, 1) !important;
            border-color: {UI_CONFIG['primary_color']} !important;
            box-shadow: 0 0 20px rgba({primary_color_rgb}, 0.2) !important;
        }}
        
        /* File uploader drag active state */
        .stFileUploader [data-baseweb="file-uploader"] {{
            background: rgba(249, 250, 251, 1) !important;
            backdrop-filter: blur(15px) !important;
            border-radius: 12px !important;
        }}
        
        /* File uploader text - dark for visibility on light background */
        .stFileUploader [data-baseweb="file-uploader"] span {{
            color: #1f2937 !important;
            font-weight: 500 !important;
        }}
        
        .stFileUploader [data-baseweb="file-uploader"] small {{
            color: #6b7280 !important;
        }}
        
        .stFileUploader [data-baseweb="file-uploader"] p {{
            color: #1f2937 !important;
        }}
        
        /* File uploader section text - dark for visibility */
        section[data-testid="stFileUploader"] span {{
            color: #1f2937 !important;
        }}
        
        section[data-testid="stFileUploader"] small {{
            color: #6b7280 !important;
        }}
        
        /* File uploader button - purple color scheme */
        .stFileUploader [data-baseweb="file-uploader"] button {{
            background: linear-gradient(135deg, {UI_CONFIG['primary_color']}, {UI_CONFIG['primary_dark']}) !important;
            color: #ffffff !important;
            border: 1px solid {UI_CONFIG['primary_color']} !important;
            border-radius: 8px !important;
            backdrop-filter: blur(10px) !important;
            font-weight: 600 !important;
        }}
        
        .stFileUploader [data-baseweb="file-uploader"] button:hover {{
            background: linear-gradient(135deg, {UI_CONFIG['primary_dark']}, {UI_CONFIG['primary_dark']}) !important;
            box-shadow: 0 4px 12px rgba({primary_color_rgb}, 0.3) !important;
        }}
        
        /* Additional file uploader targeting - catch all elements */
        [data-testid="stFileUploader"] {{
            background: transparent !important;
        }}
        
        [data-testid="stFileUploader"] > div {{
            background: transparent !important;
        }}
        
        [data-testid="stFileUploader"] [data-baseweb="file-uploader"] {{
            background: rgba(249, 250, 251, 1) !important;
        }}
        
        [data-testid="stFileUploader"] [data-baseweb="file-uploader"] > div {{
            background: rgba(249, 250, 251, 1) !important;
        }}
        
        /* Catch any remaining backgrounds in file uploader */
        .stFileUploader div[style*="background"] {{
            background: rgba(249, 250, 251, 1) !important;
        }}
        
        /* Ultra-aggressive file uploader styling - override everything */
        section[data-testid="stFileUploader"] div {{
            background-color: rgba(249, 250, 251, 1) !important;
        }}
        
        section[data-testid="stFileUploader"] [data-baseweb="file-uploader"] {{
            background-color: rgba(249, 250, 251, 1) !important;
            border: 2px dashed rgba({primary_color_rgb}, 0.6) !important;
        }}
        
        section[data-testid="stFileUploader"] div[data-baseweb="file-uploader"] > div {{
            background-color: rgba(249, 250, 251, 1) !important;
        }}
        
        /* Override any inline background styles */
        section[data-testid="stFileUploader"] div[style*="background"] {{
            background-color: rgba(249, 250, 251, 1) !important;
            background: rgba(249, 250, 251, 1) !important;
        }}
        
        /* Text color in file uploader */
        section[data-testid="stFileUploader"] span,
        section[data-testid="stFileUploader"] p,
        section[data-testid="stFileUploader"] small,
        section[data-testid="stFileUploader"] div {{
            color: #1f2937 !important;
        }}
        
        /* Highest specificity - target by element and attributes */
        section.main section[data-testid="stFileUploader"] div[data-baseweb="file-uploader"] {{
            background: rgba(249, 250, 251, 1) !important;
            background-color: rgba(249, 250, 251, 1) !important;
        }}
        
        /* Force override Streamlit's default background */
        .stApp section[data-testid="stFileUploader"] > div > div {{
            background: rgba(249, 250, 251, 1) !important;
        }}
        
        .stApp section[data-testid="stFileUploader"] [role="button"] {{
            background: rgba(249, 250, 251, 1) !important;
        }}
        
        /* Target the dropzone specifically */
        section[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"],
        section[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInput"] {{
            background: rgba(249, 250, 251, 1) !important;
            background-color: rgba(249, 250, 251, 1) !important;
        }}
        
        /* NEW: Target the ACTUAL dropzone section directly */
        section[data-testid="stFileUploaderDropzone"] {{
            background: rgba(249, 250, 251, 1) !important;
            background-color: rgba(249, 250, 251, 1) !important;
            border: 2px dashed rgba({primary_color_rgb}, 0.6) !important;
            border-radius: 12px !important;
        }}
        
        /* Target dropzone instructions div */
        [data-testid="stFileUploaderDropzoneInstructions"] {{
            background: transparent !important;
        }}
        
        /* Target text elements inside dropzone */
        section[data-testid="stFileUploaderDropzone"] span,
        section[data-testid="stFileUploaderDropzone"] small,
        section[data-testid="stFileUploaderDropzone"] div {{
            color: #1f2937 !important;
        }}
        
        /* Target the Browse files button specifically */
        section[data-testid="stFileUploaderDropzone"] button[kind="secondary"] {{
            background: linear-gradient(135deg, {UI_CONFIG['primary_color']}, {UI_CONFIG['primary_dark']}) !important;
            color: #ffffff !important;
            border: 1px solid {UI_CONFIG['primary_color']} !important;
        }}
        
        section[data-testid="stFileUploaderDropzone"] button[kind="secondary"]:hover {{
            background: linear-gradient(135deg, {UI_CONFIG['primary_dark']}, {UI_CONFIG['primary_dark']}) !important;
            box-shadow: 0 4px 12px rgba({primary_color_rgb}, 0.3) !important;
        }}
        
        /* Tabs - light glass effect */
        .stTabs [data-baseweb="tab-list"] {{
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(15px);
            border-radius: 15px;
            padding: 0.5rem;
            border: 1px solid rgba(0, 0, 0, 0.1);
            gap: 0.5rem;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            color: #4b5563 !important;
            font-weight: 600 !important;
            border-radius: 10px !important;
            background: transparent !important;
            padding: 0.75rem 1.5rem !important;
            transition: all 0.3s ease !important;
        }}
        
        .stTabs [data-baseweb="tab"]:hover {{
            background: rgba(243, 244, 246, 1) !important;
            color: #1f2937 !important;
        }}
        
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, {UI_CONFIG['primary_color']}, {UI_CONFIG['primary_dark']}) !important;
            color: #ffffff !important;
            box-shadow: 0 4px 12px rgba({primary_color_rgb}, 0.3) !important;
        }}
        
        /* Ensure text inside selected tab is white */
        .stTabs [aria-selected="true"] p,
        .stTabs [aria-selected="true"] span,
        .stTabs [aria-selected="true"] div {{
            color: #ffffff !important;
        }}
        
        /* Metrics - light cards */
        [data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid rgba(0, 0, 0, 0.1);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}
        
        [data-testid="stMetricValue"] {{
            color: #059669 !important;
            font-weight: 700 !important;
            text-shadow: 0 2px 4px rgba(5, 150, 105, 0.2);
        }}
        
        [data-testid="stMetricLabel"] {{
            color: #4b5563 !important;
        }}
        
        /* Logo styling - fully transparent */
        .logo-container {{
            position: fixed;
            top: 100px;
            right: 20px;
            z-index: 999;
            background: transparent;
            padding: 0px;
            border-radius: 0px;
            border: none;
            box-shadow: none;
        }}
        
        .logo-container img {{
            display: block;
            background: transparent;
        }}
        
        /* Success/Error/Warning messages - light theme with color */
        .stSuccess {{
            background: rgba(209, 250, 229, 0.95) !important;
            backdrop-filter: blur(10px) !important;
            color: #065f46 !important;
            border-radius: 12px !important;
            border: 1px solid rgba(16, 185, 129, 0.3) !important;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2) !important;
        }}
        
        .stError {{
            background: rgba(254, 202, 202, 0.95) !important;
            backdrop-filter: blur(10px) !important;
            color: #991b1b !important;
            border-radius: 12px !important;
            border: 1px solid rgba(239, 68, 68, 0.3) !important;
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.2) !important;
        }}
        
        .stWarning {{
            background: rgba(254, 243, 199, 0.95) !important;
            backdrop-filter: blur(10px) !important;
            color: #92400e !important;
            border-radius: 12px !important;
            border: 1px solid rgba(251, 191, 36, 0.3) !important;
            box-shadow: 0 4px 15px rgba(251, 191, 36, 0.2) !important;
        }}
        
        .stInfo {{
            background: rgba(219, 234, 254, 0.95) !important;
            backdrop-filter: blur(10px) !important;
            color: #1e40af !important;
            border-radius: 12px !important;
            border: 1px solid rgba(59, 130, 246, 0.3) !important;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2) !important;
        }}
        
        /* Slider - light glass track */
        .stSlider {{
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid rgba(0, 0, 0, 0.1);
        }}
        
        .stSlider label {{
            color: #1f2937 !important;
            font-weight: 500 !important;
        }}
        
        /* Selectbox - light glass dropdown */
        .stSelectbox {{
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid rgba(0, 0, 0, 0.1);
        }}
        
        .stSelectbox label {{
            color: #1f2937 !important;
            font-weight: 500 !important;
        }}
        
        /* Selectbox dropdown menu */
        .stSelectbox > div > div {{
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(15px) !important;
            border: 1px solid rgba(0, 0, 0, 0.15) !important;
        }}
        
        .stSelectbox [data-baseweb="select"] {{
            background: rgba(249, 250, 251, 1) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(209, 213, 219, 1) !important;
        }}
        
        .stSelectbox [data-baseweb="select"] > div {{
            color: #1f2937 !important;
        }}
        
        /* Selectbox dropdown options */
        [role="option"] {{
            color: #1f2937 !important;
            background: rgba(255, 255, 255, 1) !important;
        }}
        
        [role="option"]:hover {{
            background: rgba(243, 244, 246, 1) !important;
        }}
        
        /* Input fields - light glass */
        input, textarea {{
            background: rgba(249, 250, 251, 1) !important;
            backdrop-filter: blur(10px) !important;
            color: #1f2937 !important;
            border: 1px solid rgba(209, 213, 219, 1) !important;
            border-radius: 10px !important;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05) !important;
        }}
        
        input::placeholder, textarea::placeholder {{
            color: #9ca3af !important;
        }}
        
        /* Number input and text input specific styling */
        .stNumberInput input, .stTextInput input {{
            background: rgba(249, 250, 251, 1) !important;
            color: #1f2937 !important;
        }}
        
        /* Markdown text */
        .stMarkdown {{
            color: #1f2937 !important;
        }}
        
        /* Expander - light glass accordion */
        .streamlit-expanderHeader {{
            background: rgba(255, 255, 255, 0.8) !important;
            backdrop-filter: blur(10px) !important;
            border-radius: 12px !important;
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
        }}
        
        /* Column dividers with subtle borders */
        [data-testid="column"] {{
            background: rgba(255, 255, 255, 0.5);
            backdrop-filter: blur(5px);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid rgba(0, 0, 0, 0.05);
        }}
        
        /* Horizontal rule with subtle gradient */
        hr {{
            border: none;
            height: 1px;
            background: linear-gradient(90deg, 
                transparent, 
                rgba(0, 0, 0, 0.15), 
                transparent);
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# Display logo in top right corner
if logo_path.exists():
    import base64

    with open(logo_path, "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <div class="logo-container">
            <img src="data:image/png;base64,{logo_data}" width="150">
        </div>
        """,
        unsafe_allow_html=True,
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

if "plot_types" not in st.session_state:
    # Initialize as set for multiple selections
    st.session_state.plot_types = {"aline"}


# ═════════════════════════════════════════════════════════════════════════
# ═════ UI LAYOUT ═════
# ═════════════════════════════════════════════════════════════════════════

st.title("🏗️ Geotechnical Plotting Application")

# Plot type selection with button-style pills
st.markdown("### Select Plot Type(s):")
st.markdown("*You can select multiple plot types to generate simultaneously*")

# Create button columns
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button(
        "A-line (Atterberg Limits)",
        key="btn_aline",
        use_container_width=True,
        type="primary" if "aline" in st.session_state.plot_types else "secondary",
    ):
        # Toggle selection
        if "aline" in st.session_state.plot_types:
            st.session_state.plot_types.discard("aline")
        else:
            st.session_state.plot_types.add("aline")
        st.rerun()

with col2:
    if st.button(
        "Undrained Shear Strength",
        key="btn_strength",
        use_container_width=True,
        type="primary" if "strength" in st.session_state.plot_types else "secondary",
    ):
        # Toggle selection
        if "strength" in st.session_state.plot_types:
            st.session_state.plot_types.discard("strength")
        else:
            st.session_state.plot_types.add("strength")
        st.rerun()

# Description based on selected plot types
if len(st.session_state.plot_types) == 0:
    st.warning("⚠️ Please select at least one plot type above")
elif len(st.session_state.plot_types) == 1:
    if "aline" in st.session_state.plot_types:
        st.markdown(
            "Generate A-line (Atterberg Limits) plasticity charts from geotechnical data"
        )
    else:
        st.markdown(
            "Generate Undrained Shear Strength vs Depth plots from geotechnical data"
        )
else:
    st.markdown(
        "Generate **both A-line and Undrained Shear Strength plots** from geotechnical data"
    )

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📁 Upload Files", "⚙️ Configuration", "📊 Results"])

# ═════════════════════════════════════════════════════════════════════════
# ═════ TAB 1: FILE UPLOAD ═════
# ═════════════════════════════════════════════════════════════════════════

with tab1:
    st.header("Upload Data Files")

    # Dynamic description based on selected plot types
    if len(st.session_state.plot_types) == 0:
        st.markdown("Please select at least one plot type above")
    elif len(st.session_state.plot_types) == 1:
        if "aline" in st.session_state.plot_types:
            st.markdown("Upload the required CSV files for A-line plot generation")
        else:
            st.markdown(
                "Upload the required CSV files for Undrained Shear Strength plot generation"
            )
    else:
        st.markdown("Upload the required CSV files for all selected plot types")

    st.subheader("Required Files")

    # Location Details - Always required
    st.session_state.uploaded_files["location"] = st.file_uploader(
        "📍 **Location Details CSV**",
        type=["csv"],
        key="location_upload",
        help="Location Details CSV with Location ID and Investigation columns",
    )

    # Get dynamic file requirements from mapping CSV
    mapping_path = app_dir / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"

    if len(st.session_state.plot_types) > 0 and mapping_path.exists():
        try:
            # Get parameter-aware file requirements from mapping
            file_requirements = get_required_files_from_mapping(
                mapping_path, list(st.session_state.plot_types)
            )
            parameter_sources = file_requirements["parameter_sources"]
            all_files = sorted(file_requirements["all_files"])

            # Display info about parameter-based file requirements
            st.markdown("**📊 Plot-Specific Data Files:**")
            st.info(
                "ℹ️ **Flexible File Upload:** For each parameter below, upload **at least one** "
                "source file. Additional sources are optional but can improve data quality by "
                "providing backup or alternative measurements."
            )

            # Add custom CSS to increase file upload section font sizes
            st.markdown(
                """
                <style>
                /* Increase expander header font size - targeting the strong tags */
                .streamlit-expanderHeader strong,
                .streamlit-expanderHeader {
                    font-size: 22px !important;
                }
                /* Increase file uploader label font size - targeting strong tags in labels */
                .stFileUploader label strong,
                .stFileUploader label {
                    font-size: 20px !important;
                }
                /* Also increase div text inside expanders */
                div[data-testid="stExpander"] strong {
                    font-size: 20px !important;
                }
                /* Make expander summary (header) background less transparent */
                div[data-testid="stExpander"] summary {
                    background-color: rgba(255, 255, 255, 0.95) !important;
                    backdrop-filter: blur(10px) !important;
                }
                /* Make expander details background less transparent */
                div[data-testid="stExpanderDetails"] {
                    background-color: rgba(255, 255, 255, 0.95) !important;
                    backdrop-filter: blur(10px) !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            # Track which files have already been added to avoid duplicates
            files_already_displayed: Dict[str, List[str]] = {}

            # Group files by parameter and display
            for param, sources in sorted(parameter_sources.items()):
                with st.expander(
                    f"📈 **Parameter: {param}** "
                    f"(minimum 1 of {len(sources)} sources required)",
                    expanded=True,
                ):
                    # Use larger font for instruction text
                    st.markdown(
                        f"<p style='font-size: 16px;'><em>Upload at least one source file for {param}.</em></p>",
                        unsafe_allow_html=True,
                    )

                    # Display each source file for this parameter
                    for idx, source in enumerate(sources):
                        csv_filename = source["csv_file"]

                        # Create normalized key for session state
                        normalized_key = normalize_filename(csv_filename)

                        # Check if this file has already been displayed
                        if normalized_key in files_already_displayed:
                            # File already displayed for another parameter - show reference
                            other_params = files_already_displayed[normalized_key]
                            display_label = get_file_upload_label(csv_filename)

                            st.info(
                                f"📎 **{display_label}** is also used for: {', '.join(other_params)}\n\n"
                                f"Upload this file once in the section above."
                            )
                            continue

                        # Track this file for this parameter
                        if normalized_key not in files_already_displayed:
                            files_already_displayed[normalized_key] = []
                        files_already_displayed[normalized_key].append(param)

                        upload_key = f"upload_{normalized_key}"

                        # Get user-friendly label
                        display_label = get_file_upload_label(csv_filename)

                        # Create file uploader
                        st.session_state.uploaded_files[normalized_key] = (
                            st.file_uploader(
                                f"**{display_label}**",
                                type=["csv"],
                                key=upload_key,
                                help=f"Source file for {param}\nFile: {csv_filename}",
                            )
                        )

        except Exception as e:
            st.error(f"Error loading file requirements: {str(e)}")

    # Validation button
    st.markdown("---")
    if st.button("🔍 Validate Files", type="primary"):
        validation_result = validate_csv_files(
            st.session_state.uploaded_files,
            list(st.session_state.plot_types),
            mapping_path,
        )

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

    if len(st.session_state.plot_types) == 0:
        st.warning("⚠️ Please select at least one plot type to configure settings")
    else:
        st.markdown("Customize outlier detection and plot appearance settings")
        if len(st.session_state.plot_types) > 1:
            st.info("ℹ️ These settings will apply to all selected plot types")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Outlier Detection")

            iqr_multiplier = st.slider(
                "IQR Multiplier",
                min_value=0.0,
                max_value=3.0,
                value=1.5,
                step=0.1,
                help="Multiplier for IQR outlier detection (default: 1.5 per Tukey's method)",
            )

            # Store in config overrides
            if "outlier_detection" not in st.session_state.config_overrides:
                st.session_state.config_overrides["outlier_detection"] = {
                    "method_settings": {
                        "standard_iqr": {"iqr_multiplier": iqr_multiplier}
                    }
                }
            else:
                st.session_state.config_overrides["outlier_detection"][
                    "method_settings"
                ]["standard_iqr"]["iqr_multiplier"] = iqr_multiplier

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
            enable_with_outliers = False
            enable_without_outliers = False
            enable_plotly = False
            enable_manually_identified = False

            if enable_plots:
                enable_with_outliers = st.checkbox("  • With Outliers", value=True)
                enable_without_outliers = st.checkbox(
                    "  • Without Outliers", value=False
                )
                enable_plotly = st.checkbox("  • Interactive HTML", value=True)

                if "strength" in st.session_state.plot_types:
                    enable_manually_identified = st.checkbox(
                        "  • Manually Identified Excluded", value=False
                    )

        with col4:
            enable_data = st.checkbox("Generate Data Exports", value=False)
            enable_csv = False
            enable_excel = False

            if enable_data:
                enable_csv = st.checkbox("  • Investigation CSV", value=True)
                enable_excel = st.checkbox("  • Excel with Highlighting", value=True)

        # Store output control in config overrides
        if "output_control" not in st.session_state.config_overrides:
            st.session_state.config_overrides["output_control"] = {}

        st.session_state.config_overrides["output_control"]["enabled"] = True
        st.session_state.config_overrides["output_control"]["plots"] = {
            "enabled": enable_plots,
            "investigation_series_plots_with_outliers": enable_with_outliers,
            "investigation_series_plots_without_outliers": enable_without_outliers,
            "investigation_series_plots_plotly_with_outliers": enable_plotly,
            "investigation_series_plots_manually_identified": enable_manually_identified,
        }
        st.session_state.config_overrides["output_control"]["data"] = {
            "enabled": enable_data,
            "investigation_summary_csv": enable_csv,
            "excel_with_highlighted_outliers": enable_excel,
        }


# ═════════════════════════════════════════════════════════════════════════
# ═════ TAB 3: RESULTS ═════
# ═════════════════════════════════════════════════════════════════════════

with tab3:
    st.header("Generate Plots")

    # Check if all required files are uploaded based on selected plot types
    mapping_path = app_dir / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"
    mapping_exists = mapping_path.exists()

    # Use dynamic validation to check if required files are uploaded
    all_files_uploaded = False
    if len(st.session_state.plot_types) > 0 and mapping_exists:
        try:
            # Get parameter-aware file requirements for selected plot types
            file_requirements = get_required_files_from_mapping(
                mapping_path, list(st.session_state.plot_types)
            )
            parameter_sources = file_requirements["parameter_sources"]

            # Check if location is uploaded (always required)
            loc_uploaded = st.session_state.uploaded_files.get("location") is not None

            # Check if at least one source file per parameter is uploaded
            uploaded_filenames = {
                normalize_filename(f.name): key
                for key, f in st.session_state.uploaded_files.items()
                if f is not None and key != "location"
            }

            # Check each parameter has at least one source file
            has_all_parameters = True
            for param, sources in parameter_sources.items():
                # Check if any source file for this parameter is uploaded
                param_has_source = False
                for source in sources:
                    csv_file = source["csv_file"]
                    normalized_csv = normalize_filename(csv_file)
                    if normalized_csv in uploaded_filenames:
                        param_has_source = True
                        break

                if not param_has_source:
                    has_all_parameters = False
                    break

            all_files_uploaded = loc_uploaded and has_all_parameters
        except Exception as e:
            st.error(f"Error checking file requirements: {str(e)}")
            all_files_uploaded = False

    if len(st.session_state.plot_types) == 0:
        st.warning("⚠️ Please select at least one plot type above")
    elif not all_files_uploaded:
        st.warning("⚠️ Please upload all required files in the Upload Files tab")
    elif not mapping_exists:
        st.error("❌ Parameter mapping file not found in repository")
    else:
        # Generate plots button - dynamic text based on selections
        if len(st.session_state.plot_types) == 0:
            button_text = "🚀 Generate Plots"
        elif len(st.session_state.plot_types) == 1:
            if "aline" in st.session_state.plot_types:
                button_text = "🚀 Generate A-line Plots"
            else:
                button_text = "🚀 Generate Strength Plots"
        else:
            button_text = "🚀 Generate All Plots"

        if st.button(button_text, type="primary", use_container_width=True):
            # Prepare validation files with mapping from repo
            validation_files = st.session_state.uploaded_files.copy()
            with open(mapping_path, "rb") as f:
                from io import BytesIO

                mapping_buffer = BytesIO(f.read())
                mapping_buffer.name = mapping_path.name

                # Create a mock uploaded file object for mapping
                class MockFileMapping:
                    def __init__(self, buffer, name):
                        self._buffer = buffer
                        self.name = name

                    def getvalue(self):
                        return self._buffer.getvalue()

                validation_files["mapping"] = MockFileMapping(
                    mapping_buffer, mapping_path.name
                )

            # Validate files first
            validation_result = validate_csv_files(
                validation_files, list(st.session_state.plot_types)
            )

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

                        # Add mapping file from repo
                        input_files["mapping"] = mapping_path

                        # Get dynamic parameter to files mapping
                        param_file_mapping = map_uploaded_files_to_parameters(
                            input_files, mapping_path, list(st.session_state.plot_types)
                        )

                        # Create output directory
                        output_dir = temp_path / "output"
                        output_dir.mkdir(exist_ok=True)

                        # Initialize combined results
                        combined_results = {
                            "success": True,
                            "formations_processed": set(),
                            "plots_generated": 0,
                            "parameter_names": [],
                            "output_folders": [],
                            "errors": [],
                        }

                        # Generate plots based on selected plot types
                        if "aline" in st.session_state.plot_types:
                            # Find files containing A-line parameters
                            aline_files = set()
                            for param in ["LiquidLimit", "PlasticityIndex"]:
                                if param in param_file_mapping:
                                    aline_files.update(param_file_mapping[param])

                            if not aline_files:
                                combined_results["success"] = False
                                combined_results["errors"].append(
                                    "A-line: No files found containing required parameters (LiquidLimit, PlasticityIndex)"
                                )
                            else:
                                # Map file keys to expected format for generate_aline_plots
                                plot_input = {
                                    "mapping": input_files["mapping"],
                                    "location": input_files["location"],
                                }

                                # Add all files containing A-line parameters
                                for file_path in aline_files:
                                    # Use original filename as key for compatibility
                                    file_key = normalize_filename(file_path.name)
                                    plot_input[file_key] = file_path

                                # Create A-line specific output directory
                                aline_output = output_dir / "aline"
                                aline_output.mkdir(exist_ok=True)

                                # Generate A-line plots
                                aline_results = generate_aline_plots(
                                    input_files=plot_input,
                                    output_dir=aline_output,
                                    config_overrides=st.session_state.config_overrides,
                                )

                                # Accumulate results
                                if aline_results["success"]:
                                    combined_results["formations_processed"].update(
                                        aline_results["formations_processed"]
                                    )
                                    combined_results[
                                        "plots_generated"
                                    ] += aline_results["plots_generated"]
                                    combined_results["parameter_names"].append(
                                        aline_results["parameter_name"]
                                    )
                                    combined_results["output_folders"].append(
                                        aline_results["output_folder"]
                                    )
                                else:
                                    combined_results["success"] = False
                                    combined_results["errors"].append(
                                        f"A-line: {aline_results['error']}"
                                    )

                        if "strength" in st.session_state.plot_types:
                            # Find files containing strength parameters
                            strength_files = set()
                            for param in ["UndrainedShearStrength"]:
                                if param in param_file_mapping:
                                    strength_files.update(param_file_mapping[param])

                            if not strength_files:
                                combined_results["success"] = False
                                combined_results["errors"].append(
                                    "Strength: No files found containing required parameters (UndrainedShearStrength)"
                                )
                            else:
                                # Map file keys to expected format for generate_strength_plots
                                plot_input = {
                                    "mapping": input_files["mapping"],
                                    "location": input_files["location"],
                                }

                                # Add all files containing strength parameters
                                for file_path in strength_files:
                                    file_key = normalize_filename(file_path.name)
                                    plot_input[file_key] = file_path

                                # Create strength specific output directory
                                strength_output = output_dir / "strength"
                                strength_output.mkdir(exist_ok=True)

                                # Generate strength plots
                                strength_results = generate_strength_plots(
                                    input_files=plot_input,
                                    output_dir=strength_output,
                                    config_overrides=st.session_state.config_overrides,
                                )

                                # Accumulate results
                                if strength_results["success"]:
                                    combined_results["formations_processed"].update(
                                        strength_results["formations_processed"]
                                    )
                                    combined_results[
                                        "plots_generated"
                                    ] += strength_results["plots_generated"]
                                    combined_results["parameter_names"].append(
                                        strength_results["parameter_name"]
                                    )
                                    combined_results["output_folders"].append(
                                        strength_results["output_folder"]
                                    )
                                else:
                                    combined_results["success"] = False
                                    combined_results["errors"].append(
                                        f"Strength: {strength_results['error']}"
                                    )

                        # Store results in session state
                        st.session_state.processing_results = combined_results

                        if combined_results["success"]:
                            st.success("✅ Plots generated successfully!")

                            # Show results summary
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric(
                                    "Formations Processed",
                                    len(combined_results["formations_processed"]),
                                )
                            with col2:
                                st.metric(
                                    "Plots Generated",
                                    combined_results["plots_generated"],
                                )
                            with col3:
                                params = ", ".join(combined_results["parameter_names"])
                                st.metric("Parameters", params if params else "N/A")

                            # List formations
                            if combined_results["formations_processed"]:
                                st.subheader("Processed Formations")
                                for formation in sorted(
                                    combined_results["formations_processed"]
                                ):
                                    st.write(f"  • {formation}")

                            # Create ZIP for download
                            st.subheader("Download Results")
                            zip_buffer = create_zip_archive(output_dir)

                            # Dynamic filename based on selections
                            if len(st.session_state.plot_types) == 1:
                                if "aline" in st.session_state.plot_types:
                                    zip_filename = "aline_plots.zip"
                                else:
                                    zip_filename = "strength_plots.zip"
                            else:
                                zip_filename = "geotechnical_plots.zip"

                            st.download_button(
                                label="📦 Download All Results (ZIP)",
                                data=zip_buffer,
                                file_name=zip_filename,
                                mime="application/zip",
                                use_container_width=True,
                            )

                        else:
                            st.error("❌ Plot generation failed:")
                            for error in combined_results["errors"]:
                                st.error(f"  • {error}")

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
            if "parameter_names" in results:
                params = ", ".join(results["parameter_names"])
                st.metric("Parameters", params if params else "N/A")
            else:
                st.metric("Parameter", results.get("parameter_name", "N/A"))


# ═════════════════════════════════════════════════════════════════════════
# ═════ FOOTER ═════
# ═════════════════════════════════════════════════════════════════════════

st.markdown("---")
if len(st.session_state.plot_types) == 0:
    st.markdown("**Geotechnical Plotting Tool** | Select a plot type to begin")
elif len(st.session_state.plot_types) == 1:
    if "aline" in st.session_state.plot_types:
        st.markdown(
            "**Geotechnical Plotting Tool** | A-line (Atterberg Limits) Chart Generator"
        )
    else:
        st.markdown(
            "**Geotechnical Plotting Tool** | Undrained Shear Strength Plot Generator"
        )
else:
    st.markdown(
        "**Geotechnical Plotting Tool** | Multi-Plot Generator (A-line + Undrained Shear Strength)"
    )

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

from validation import (
    validate_csv_files,
    save_uploaded_files,
    get_required_files_from_mapping,
    get_file_upload_label,
    normalize_filename,
)
from zip_utils import create_zip_archive
from Streamlit_A_line import generate_aline_plots
from Streamlit_UndrainedShearStrength import generate_strength_plots


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
background_path = app_dir / "assets" / "BackgroundBlue.jpg"
logo_path = app_dir / "assets" / "BinniesLogo.png"

if background_path.exists():
    import base64

    with open(background_path, "rb") as f:
        bg_data = base64.b64encode(f.read()).decode()

    # Add custom CSS for glassmorphism design
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
            background: rgba(38, 131, 160, 0.3) !important;
            backdrop-filter: blur(20px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.15) !important;
        }}
        
        /* Header toolbar buttons and icons */
        header[data-testid="stHeader"] button {{
            color: #ffffff !important;
        }}
        
        header[data-testid="stHeader"] svg {{
            fill: #ffffff !important;
        }}
        
        /* Glassmorphism effect for main container */
        .main .block-container {{
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            padding: 2.5rem;
            margin-top: 1rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }}
        
        /* Make all text white/light for dark background */
        .stApp {{
            color: #ffffff;
        }}
        
        /* Headers styling - bright white with glow */
        h1, h2, h3, h4, h5, h6 {{
            color: #ffffff !important;
            font-weight: 700 !important;
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.3), 
                         2px 2px 8px rgba(0,0,0,0.5);
        }}
        
        /* Main title styling */
        h1 {{
            font-size: 2.5rem !important;
            margin-bottom: 0.5rem !important;
            letter-spacing: 0.5px;
        }}
        
        /* Radio buttons and checkboxes - glassmorphic cards */
        .stRadio, .stCheckbox {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .stRadio label, .stCheckbox label {{
            color: #ffffff !important;
            font-weight: 500 !important;
        }}
        
        /* All paragraph text */
        p, span, div {{
            color: #ffffff !important;
        }}
        
        /* Button styling - glass button with teal/green glow */
        .stButton button {{
            background: linear-gradient(135deg, rgba(52, 161, 119, 0.9), rgba(42, 141, 99, 0.9)) !important;
            color: #ffffff !important;
            border: 2px solid rgba(255, 255, 255, 0.3) !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            backdrop-filter: blur(10px) !important;
            box-shadow: 0 4px 15px rgba(52, 161, 119, 0.4),
                        inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
            transition: all 0.3s ease !important;
            min-height: 3rem !important;
            font-size: 1.1rem !important;
        }}
        
        .stButton button:hover {{
            background: linear-gradient(135deg, rgba(42, 141, 99, 1), rgba(52, 161, 119, 1)) !important;
            box-shadow: 0 6px 20px rgba(52, 161, 119, 0.6),
                        inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
            transform: translateY(-2px) !important;
        }}
        
        /* Plot type selection buttons - extra large and prominent */
        button[key="btn_aline"], button[key="btn_strength"] {{
            min-height: 5rem !important;
            font-size: 1.3rem !important;
            padding: 1.5rem !important;
        }}
        
        /* Primary button (selected state) - bright teal with glow */
        button[data-baseweb="button"][kind="primary"],
        button[data-testid="stBaseButton-primary"] {{
            background: linear-gradient(135deg, rgba(52, 161, 119, 1), rgba(42, 141, 99, 1)) !important;
            box-shadow: 0 8px 25px rgba(52, 161, 119, 0.6),
                        inset 0 2px 0 rgba(255, 255, 255, 0.4),
                        0 0 30px rgba(52, 161, 119, 0.3) !important;
            border: 3px solid rgba(255, 255, 255, 0.5) !important;
            transform: scale(1.02) !important;
        }}
        
        /* Secondary button (unselected state) - muted glass */
        button[data-baseweb="button"][kind="secondary"],
        button[data-testid="stBaseButton-secondary"] {{
            background: rgba(255, 255, 255, 0.1) !important;
            color: #ffffff !important;
            border: 2px solid rgba(255, 255, 255, 0.2) !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
            backdrop-filter: blur(10px) !important;
        }}
        
        /* Target text inside secondary button */
        button[data-testid="stBaseButton-secondary"] p {{
            color: rgba(255, 255, 255, 0.6) !important;
        }}
        
        button[data-baseweb="button"][kind="secondary"]:hover,
        button[data-testid="stBaseButton-secondary"]:hover {{
            background: rgba(255, 255, 255, 0.15) !important;
            border-color: rgba(52, 161, 119, 0.4) !important;
            box-shadow: 0 6px 20px rgba(52, 161, 119, 0.3) !important;
        }}
        
        /* Hover text brightness */
        button[data-testid="stBaseButton-secondary"]:hover p {{
            color: rgba(255, 255, 255, 0.8) !important;
        }}
        
        /* File uploader - glass card */
        .stFileUploader {{
            background: rgba(255, 255, 255, 0.06);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }}
        
        .stFileUploader label {{
            color: #ffffff !important;
            font-weight: 600 !important;
        }}
        
        /* File uploader drop zone - enhanced glass effect with dark background */
        .stFileUploader > div > div {{
            background: rgba(30, 58, 138, 1) !important;
            backdrop-filter: blur(15px) !important;
            border: 2px dashed rgba(52, 161, 119, 1) !important;
            border-radius: 12px !important;
            transition: all 0.3s ease !important;
        }}
        
        .stFileUploader > div > div:hover {{
            background: rgba(30, 58, 138, 1) !important;
            border-color: rgba(52, 161, 119, 1) !important;
            box-shadow: 0 0 20px rgba(52, 161, 119, 1) !important;
        }}
        
        /* File uploader drag active state */
        .stFileUploader [data-baseweb="file-uploader"] {{
            background: rgba(30, 58, 138, 1) !important;
            backdrop-filter: blur(15px) !important;
            border-radius: 12px !important;
        }}
        
        /* File uploader text - white for visibility */
        .stFileUploader [data-baseweb="file-uploader"] span {{
            color: #ffffff !important;
            font-weight: 500 !important;
        }}
        
        .stFileUploader [data-baseweb="file-uploader"] small {{
            color: rgba(255, 255, 255, 1) !important;
        }}
        
        .stFileUploader [data-baseweb="file-uploader"] p {{
            color: #ffffff !important;
        }}
        
        /* File uploader section text - white for visibility */
        section[data-testid="stFileUploader"] span {{
            color: #ffffff !important;
        }}
        
        section[data-testid="stFileUploader"] small {{
            color: rgba(255, 255, 255, 1) !important;
        }}
        
        /* File uploader button - teal color scheme */
        .stFileUploader [data-baseweb="file-uploader"] button {{
            background: linear-gradient(135deg, rgba(52, 161, 119, 1), rgba(42, 141, 99, 1)) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 1) !important;
            border-radius: 8px !important;
            backdrop-filter: blur(10px) !important;
            font-weight: 600 !important;
        }}
        
        .stFileUploader [data-baseweb="file-uploader"] button:hover {{
            background: linear-gradient(135deg, rgba(42, 141, 99, 1), rgba(52, 161, 119, 1)) !important;
            box-shadow: 0 4px 12px rgba(52, 161, 119, 1) !important;
        }}
        
        /* Additional file uploader targeting - catch all elements */
        [data-testid="stFileUploader"] {{
            background: transparent !important;
        }}
        
        [data-testid="stFileUploader"] > div {{
            background: transparent !important;
        }}
        
        [data-testid="stFileUploader"] [data-baseweb="file-uploader"] {{
            background: rgba(30, 58, 138, 1) !important;
        }}
        
        [data-testid="stFileUploader"] [data-baseweb="file-uploader"] > div {{
            background: rgba(30, 58, 138, 1) !important;
        }}
        
        /* Catch any remaining white backgrounds in file uploader */
        .stFileUploader div[style*="background"] {{
            background: rgba(30, 58, 138, 1) !important;
        }}
        
        /* Ultra-aggressive file uploader styling - override everything */
        section[data-testid="stFileUploader"] div {{
            background-color: rgba(30, 58, 138, 1) !important;
        }}
        
        section[data-testid="stFileUploader"] [data-baseweb="file-uploader"] {{
            background-color: rgba(30, 58, 138, 1) !important;
            border: 2px dashed rgba(52, 161, 119, 1) !important;
        }}
        
        section[data-testid="stFileUploader"] div[data-baseweb="file-uploader"] > div {{
            background-color: rgba(30, 58, 138, 1) !important;
        }}
        
        /* Override any inline background styles */
        section[data-testid="stFileUploader"] div[style*="background"] {{
            background-color: rgba(30, 58, 138, 1) !important;
            background: rgba(30, 58, 138, 1) !important;
        }}
        
        /* Text color in file uploader */
        section[data-testid="stFileUploader"] span,
        section[data-testid="stFileUploader"] p,
        section[data-testid="stFileUploader"] small,
        section[data-testid="stFileUploader"] div {{
            color: #ffffff !important;
        }}
        
        /* Highest specificity - target by element and attributes */
        section.main section[data-testid="stFileUploader"] div[data-baseweb="file-uploader"] {{
            background: rgba(30, 58, 138, 1) !important;
            background-color: rgba(30, 58, 138, 1) !important;
        }}
        
        /* Force override Streamlit's default white background */
        .stApp section[data-testid="stFileUploader"] > div > div {{
            background: rgba(30, 58, 138, 1) !important;
        }}
        
        .stApp section[data-testid="stFileUploader"] [role="button"] {{
            background: rgba(30, 58, 138, 1) !important;
        }}
        
        /* Target the dropzone specifically */
        section[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"],
        section[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInput"] {{
            background: rgba(30, 58, 138, 1) !important;
            background-color: rgba(30, 58, 138, 1) !important;
        }}
        
        /* NEW: Target the ACTUAL dropzone section directly */
        section[data-testid="stFileUploaderDropzone"] {{
            background: rgba(172, 229, 255, 1) !important;
            background-color: rgba(182, 232, 255, 1) !important;
            border: 2px dashed rgba(52, 161, 119, 0) !important;
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
            color: #000000e5 !important;
        }}
        
        /* Target the Browse files button specifically */
        section[data-testid="stFileUploaderDropzone"] button[kind="secondary"] {{
            background: linear-gradient(135deg, rgba(52, 161, 119, 1), rgba(42, 141, 99, 1)) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0) !important;
        }}
        
        section[data-testid="stFileUploaderDropzone"] button[kind="secondary"]:hover {{
            background: linear-gradient(135deg, rgba(42, 141, 99, 1), rgba(52, 161, 119, 1)) !important;
            box-shadow: 0 4px 12px rgba(52, 161, 119, 1) !important;
        }}
        
        /* Tabs - liquid glass effect */
        .stTabs [data-baseweb="tab-list"] {{
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(15px);
            border-radius: 15px;
            padding: 0.5rem;
            border: 1px solid rgba(255, 255, 255, 0.15);
            gap: 0.5rem;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            color: #ffffff !important;
            font-weight: 600 !important;
            border-radius: 10px !important;
            background: transparent !important;
            padding: 0.75rem 1.5rem !important;
            transition: all 0.3s ease !important;
        }}
        
        .stTabs [data-baseweb="tab"]:hover {{
            background: rgba(255, 255, 255, 0.1) !important;
        }}
        
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, rgba(52, 161, 119, 0.9), rgba(42, 141, 99, 0.9)) !important;
            color: #ffffff !important;
            box-shadow: 0 4px 12px rgba(251, 191, 36, 0.4) !important;
        }}
        
        /* Metrics - glowing cards */
        [data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }}
        
        [data-testid="stMetricValue"] {{
            color: #fbbf24 !important;
            font-weight: 700 !important;
            text-shadow: 0 0 10px rgba(251, 191, 36, 0.5);
        }}
        
        [data-testid="stMetricLabel"] {{
            color: rgba(255, 255, 255, 0.9) !important;
        }}
        
        /* Logo styling - transparent with glass effect */
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
        
        /* Sidebar styling - glass panel */
        [data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 1) !important;
            backdrop-filter: blur(20px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        }}
        
        [data-testid="stSidebar"] > div:first-child {{
            background: transparent !important;
        }}
        
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div {{
            color: #111111 !important;
        }}
        
        /* Success/Error/Warning messages - glass cards with color */
        .stSuccess {{
            background: rgba(16, 185, 129, 0.85) !important;
            backdrop-filter: blur(10px) !important;
            color: white !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important;
        }}
        
        .stError {{
            background: rgba(52, 161, 119, 0.767) !important;
            backdrop-filter: blur(10px) !important;
            color: white !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            box-shadow: 0 4px 15px rgba(52, 161, 119, 0.3) !important;
        }}
        
        .stWarning {{
            background: rgba(251, 191, 36, 0.85) !important;
            backdrop-filter: blur(10px) !important;
            color: #1e3a8a !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            box-shadow: 0 4px 15px rgba(251, 191, 36, 0.3) !important;
        }}
        
        .stInfo {{
            background: rgba(59, 130, 246, 0.85) !important;
            backdrop-filter: blur(10px) !important;
            color: #ffffff !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3) !important;
        }}
        
        /* Slider - glass track */
        .stSlider {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .stSlider label {{
            color: #ffffff !important;
            font-weight: 500 !important;
        }}
        
        /* Selectbox - glass dropdown */
        .stSelectbox {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .stSelectbox label {{
            color: #ffffff !important;
            font-weight: 500 !important;
        }}
        
        /* Selectbox dropdown menu */
        .stSelectbox > div > div {{
            background: rgba(255, 99, 71, 0.5) !important;
            backdrop-filter: blur(15px) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }}
        
        .stSelectbox [data-baseweb="select"] {{
            background: rgba(255, 99, 71, 0.5) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
        }}
        
        .stSelectbox [data-baseweb="select"] > div {{
            color: #ffffff !important;
        }}
        
        /* Selectbox dropdown options */
        [role="option"] {{
            color: #ffffff !important;
            background: rgba(255, 99, 71, 0.7) !important;
        }}
        
        [role="option"]:hover {{
            background: rgba(234, 176, 31, 0.9) !important;
        }}
        
        /* Input fields - transparent glass */
        input, textarea {{
            background: rgba(255, 255, 255, 0.15) !important;
            backdrop-filter: blur(10px) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 10px !important;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        }}
        
        input::placeholder, textarea::placeholder {{
            color: rgba(255, 255, 255, 0.6) !important;
        }}
        
        /* Number input and text input specific styling */
        .stNumberInput input, .stTextInput input {{
            background: rgba(255, 255, 255, 0.15) !important;
            color: #ffffff !important;
        }}
        
        /* Markdown text */
        .stMarkdown {{
            color: #ffffff !important;
        }}
        
        /* Expander - glass accordion */
        .streamlit-expanderHeader {{
            background: rgba(255, 255, 255, 0.08) !important;
            backdrop-filter: blur(10px) !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }}
        
        /* Column dividers with subtle glow */
        [data-testid="column"] {{
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(5px);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }}
        
        /* Horizontal rule with glow */
        hr {{
            border: none;
            height: 1px;
            background: linear-gradient(90deg, 
                transparent, 
                rgba(255, 255, 255, 0.3), 
                transparent);
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
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

# Plot type selection with checkboxes for multi-select
st.markdown("### Select Plot Type(s):")
st.markdown("*You can select multiple plot types to generate simultaneously*")

col1, col2 = st.columns(2)

with col1:
    aline_selected = st.checkbox(
        "📊 A-line (Atterberg Limits)",
        value="aline" in st.session_state.plot_types,
        key="check_aline",
    )

with col2:
    strength_selected = st.checkbox(
        "📈 Undrained Shear Strength",
        value="strength" in st.session_state.plot_types,
        key="check_strength",
    )

# Update plot_types set based on checkbox selections
new_plot_types = set()
if aline_selected:
    new_plot_types.add("aline")
if strength_selected:
    new_plot_types.add("strength")

# Update session state if selections changed
if new_plot_types != st.session_state.plot_types:
    st.session_state.plot_types = new_plot_types
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

# Sidebar
with st.sidebar:
    st.header("About")

    # Dynamic sidebar based on selected plot types
    if len(st.session_state.plot_types) == 0:
        st.warning("Please select at least one plot type")
    elif len(st.session_state.plot_types) == 1:
        if "aline" in st.session_state.plot_types:
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
        else:
            st.markdown(
                """
            This tool generates Undrained Shear Strength vs Depth plots from geotechnical CSV data.
            
            **Features:**
            - Investigation-based coloring
            - Multiple test type support (SPT, CPT, Triaxial, etc.)
            - Outlier detection and filtering
            - Interactive HTML plots
            - Manual outlier exclusion support
            - Excel exports with highlighting
            """
            )
            st.markdown("---")
            st.markdown("**Plot Type:** Undrained Shear Strength")
    else:
        # Multiple plot types selected
        st.markdown(
            """
        This tool generates both A-line and Undrained Shear Strength plots from geotechnical CSV data.
        
        **A-line Features:**
        - Plasticity charts with classification boundaries
        - Investigation-based coloring
        
        **Strength Features:**
        - Multiple test type support
        - CPT density analysis
        - Manual outlier exclusion
        
        **Common Features:**
        - Outlier detection and filtering
        - Interactive HTML plots
        - Excel exports with highlighting
        """
        )
        st.markdown("---")
        st.markdown("**Plot Types:** A-line + Undrained Shear Strength")

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

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Required Files")

        # Location Details - Always required
        st.session_state.uploaded_files["location"] = st.file_uploader(
            "📍 Location Details CSV",
            type=["csv"],
            key="location_upload",
            help="Location Details CSV with Location ID and Investigation columns",
        )

        # Get dynamic file requirements from mapping CSV
        mapping_path = (
            app_dir / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"
        )

        if len(st.session_state.plot_types) > 0 and mapping_path.exists():
            try:
                # Get required files from mapping
                file_requirements = get_required_files_from_mapping(
                    mapping_path, list(st.session_state.plot_types)
                )
                required_files = sorted(file_requirements["required_files"])

                # Display info about required files
                st.markdown(
                    f"**📋 Required Data Files ({len(required_files)} file types needed):**"
                )
                st.info(
                    "Upload at least one file containing the required parameters. "
                    "Multiple files may contain the same parameter with different priority ranks."
                )

                # Generate file uploaders dynamically
                for csv_filename in required_files:
                    # Create normalized key for session state
                    normalized_key = normalize_filename(csv_filename)
                    upload_key = f"upload_{normalized_key}"

                    # Get user-friendly label
                    display_label = get_file_upload_label(csv_filename)

                    # Create file uploader
                    st.session_state.uploaded_files[normalized_key] = st.file_uploader(
                        display_label,
                        type=["csv"],
                        key=upload_key,
                        help=f"Upload {csv_filename}",
                    )

            except Exception as e:
                st.error(f"Error loading file requirements: {str(e)}")

    with col2:
        st.subheader("Upload Status")

        # Show mapping file status (from repo)
        if mapping_path.exists():
            st.success(f"✅ Parameter Mapping: {mapping_path.name} (from repo)")
        else:
            st.error("❌ Parameter Mapping file not found in repo")

        # Show location file status (always required)
        loc_file = st.session_state.uploaded_files.get("location")
        if loc_file:
            st.success(f"✅ Location Details: {loc_file.name}")
        else:
            st.warning("⚠️ Location Details: Not uploaded (REQUIRED)")

        # Show dynamically required files status
        if len(st.session_state.plot_types) > 0 and mapping_path.exists():
            try:
                file_requirements = get_required_files_from_mapping(
                    mapping_path, list(st.session_state.plot_types)
                )
                required_files = sorted(file_requirements["required_files"])

                # Count uploaded required files
                uploaded_count = 0
                uploaded_details = []

                for csv_filename in required_files:
                    normalized_key = normalize_filename(csv_filename)
                    file_obj = st.session_state.uploaded_files.get(normalized_key)
                    if file_obj:
                        uploaded_count += 1
                        display_label = get_file_upload_label(csv_filename)
                        uploaded_details.append(f"  • {display_label}: {file_obj.name}")

                if uploaded_count > 0:
                    st.success(
                        f"✅ Required Data Files: {uploaded_count}/{len(required_files)} uploaded"
                    )
                    for detail in uploaded_details:
                        st.info(detail)
                else:
                    st.warning(
                        f"⚠️ Required Data Files: None uploaded ({len(required_files)} types needed)"
                    )

            except Exception as e:
                st.error(f"Error checking upload status: {str(e)}")

        # Validation button
        if st.button("🔍 Validate Files", type="secondary"):
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

    # Check if all required files are uploaded based on plot type
    if "aline" in st.session_state.plot_types:
        all_files_uploaded = all(
            st.session_state.uploaded_files.get(key) is not None
            for key in ["location", "classification"]
        )
    else:
        # For strength plots, need location and at least one test file
        loc_uploaded = st.session_state.uploaded_files.get("location") is not None
        test_files_uploaded = any(
            k not in ["mapping", "location"] and v is not None
            for k, v in st.session_state.uploaded_files.items()
        )
        all_files_uploaded = loc_uploaded and test_files_uploaded

    # Check if mapping file exists in repo
    mapping_path = app_dir / "Global_Parameter_Mapping_Extraction_only_CORRECTED.csv"
    mapping_exists = mapping_path.exists()

    if not all_files_uploaded:
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
                            # Map file keys to expected format for generate_aline_plots
                            plot_input = {
                                "mapping": input_files["mapping"],
                                "location": input_files["location"],
                                "classification": input_files["classification"],
                            }

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
                                combined_results["plots_generated"] += aline_results[
                                    "plots_generated"
                                ]
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
                            # Map file keys to expected format for generate_strength_plots
                            plot_input = {
                                "mapping": input_files["mapping"],
                                "location": input_files["location"],
                            }

                            # Add all test data files
                            for key, value in input_files.items():
                                if key not in ["mapping", "location", "classification"]:
                                    plot_input[key] = value

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
                                combined_results["plots_generated"] += strength_results[
                                    "plots_generated"
                                ]
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

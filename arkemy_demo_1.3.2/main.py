# main.py
import streamlit as st
import os
import glob
import gc

# Import UI functions
from ui import render_dashboard
from ui.parquet_processor import process_parquet_data_from_path

# Set page configuration
st.set_page_config(
    page_title="Arkemy v1.3: Turning Your Project Data Into Gold 🥇",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'csv_loaded' not in st.session_state:
    st.session_state.csv_loaded = False
if 'transformed_df' not in st.session_state:
    st.session_state.transformed_df = None
if 'currency' not in st.session_state:
    st.session_state.currency = 'nok'  # Default to Norwegian krone
if 'currency_selected' not in st.session_state:
    st.session_state.currency_selected = False
if 'planned_csv_loaded' not in st.session_state:
    st.session_state.planned_csv_loaded = False
if 'transformed_planned_df' not in st.session_state:
    st.session_state.transformed_planned_df = None
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0
if 'data_loading_attempted' not in st.session_state:
    st.session_state.data_loading_attempted = False

def find_parquet_file():
    """Find the first Parquet file in /data directory"""
    data_dir = "data"
    if not os.path.exists(data_dir):
        return None
    
    parquet_files = glob.glob(os.path.join(data_dir, "*.parquet")) + glob.glob(os.path.join(data_dir, "*.pq"))
    return parquet_files[0] if parquet_files else None

def is_data_loaded():
    """Check if data is loaded and available for analysis"""
    return (
        st.session_state.csv_loaded and 
        st.session_state.transformed_df is not None and 
        not getattr(st.session_state.transformed_df, 'empty', True)
    )

def auto_load_data():
    """Automatically load data from /data directory on first run"""
    if st.session_state.data_loading_attempted:
        return
    
    st.session_state.data_loading_attempted = True
    
    # Find parquet file
    parquet_path = find_parquet_file()
    if not parquet_path:
        st.error("No Parquet files found in /data directory. Please add a .parquet or .pq file.")
        return
    
    # Show loading message
    with st.spinner(f"Loading data from {os.path.basename(parquet_path)}..."):
        try:
            process_parquet_data_from_path(parquet_path)
            st.success(f"Successfully loaded data from {os.path.basename(parquet_path)}")
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")

def render_currency_setup():
    """Render error message if currency couldn't be auto-detected"""
    st.title('Arkemy: Turn Your Project Data Into Gold 🥇')
    st.markdown("##### v1.3.1 Parquet")
    
    st.error("Currency could not be detected from filename.")
    st.markdown("Please name your file like: `data_NOK.parquet` or `data_USD.parquet`")
    
    # Fallback manual selection
    from utils.currency_formatter import get_currency_selector, get_currency_display_name
    currency_valid, currency_message = get_currency_selector("fallback_currency_selector", required=True)
    
    if currency_valid:
        st.success(f"Selected currency: {get_currency_display_name()}")
        st.session_state.currency_selected = True
        st.rerun()

# Main execution flow
if __name__ == "__main__":
    if not is_data_loaded():
        # Auto-load data on first run
        auto_load_data()
        
        # If data still not loaded after attempt, show error state
        if not is_data_loaded():
            st.title('Arkemy: Turn Your Project Data Into Gold 🥇')
            st.markdown("##### v1.3.1 Parquet")
            st.error("Unable to load data. Please check that a valid Parquet file exists in the /data directory.")
    else:
        # Render the dashboard with data
        render_dashboard()
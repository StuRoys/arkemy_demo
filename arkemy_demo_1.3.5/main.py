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
#sss
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
if 'show_uploader' not in st.session_state:
    st.session_state.show_uploader = False

# Initialize capacity-related session state variables
if 'schedule_loaded' not in st.session_state:
    st.session_state.schedule_loaded = False
if 'schedule_df' not in st.session_state:
    st.session_state.schedule_df = None
if 'absence_loaded' not in st.session_state:
    st.session_state.absence_loaded = False
if 'absence_df' not in st.session_state:
    st.session_state.absence_df = None
if 'capacity_config' not in st.session_state:
    st.session_state.capacity_config = None
if 'capacity_summary_loaded' not in st.session_state:
    st.session_state.capacity_summary_loaded = False
if 'capacity_summary_df' not in st.session_state:
    st.session_state.capacity_summary_df = None

def find_parquet_file():
    """Find the first Parquet file in project root"""
    parquet_files = glob.glob("*.parquet") + glob.glob("*.pq")
    return parquet_files[0] if parquet_files else None

def is_data_loaded():
    """Check if data is loaded and available for analysis"""
    return (
        st.session_state.csv_loaded and 
        st.session_state.transformed_df is not None and 
        not getattr(st.session_state.transformed_df, 'empty', True)
    )

def is_capacity_data_available():
    """Check if capacity data is loaded and available for analysis"""
    return (
        st.session_state.schedule_loaded and 
        st.session_state.schedule_df is not None and 
        not getattr(st.session_state.schedule_df, 'empty', True)
    )

def show_loading_screen():
    """Show a clean loading screen"""
    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 70vh;">
        <h1>🥇 Arkemy</h1>
        <h3>Turn Your Project Data Into Gold</h3>
        <div style="margin: 40px 0;">
            <div class="stSpinner">Loading your data...</div>
        </div>
        <p style="color: #666;">Please wait while we process your project data</p>
    </div>
    """, unsafe_allow_html=True)

def auto_load_data():
    """Automatically load data from project root on first run"""
    if st.session_state.data_loading_attempted:
        return
    
    st.session_state.data_loading_attempted = True
    
    # Find parquet file
    parquet_path = find_parquet_file()
    if not parquet_path:
        # No parquet files found - set flag to show uploader instead
        st.session_state.show_uploader = True
        return
    
    # Process the parquet file (suppress output with empty container)
    with st.empty():
        try:
            process_parquet_data_from_path(parquet_path)
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")

def render_currency_setup():
    """Render error message if currency couldn't be auto-detected"""
    st.title('Arkemy: Turn Your Project Data Into Gold 🥇')
    st.markdown("##### v1.3.5 Parquet (DEMO)")
    
    st.error("Currency could not be detected from filename.")
    st.markdown("Please name your file like: `data_NOK.parquet` or `data_USD.parquet`")
    
    # Fallback manual selection
    from utils.currency_formatter import get_currency_selector, get_currency_display_name
    currency_valid, currency_message = get_currency_selector("fallback_currency_selector", required=True)
    
    if currency_valid:
        st.success(f"Selected currency: {get_currency_display_name()}")
        st.session_state.currency_selected = True
        st.rerun()

def show_data_status():
    """Show data loading status for debugging"""
    if st.sidebar.expander("Debug: Data Status"):
        st.sidebar.write("**Main Data:**")
        st.sidebar.write(f"- CSV loaded: {st.session_state.csv_loaded}")
        st.sidebar.write(f"- Main DF shape: {getattr(st.session_state.transformed_df, 'shape', 'None')}")
        
        st.sidebar.write("**Planned Data:**")
        st.sidebar.write(f"- Planned loaded: {st.session_state.planned_csv_loaded}")
        st.sidebar.write(f"- Planned DF shape: {getattr(st.session_state.transformed_planned_df, 'shape', 'None')}")
        
        st.sidebar.write("**Capacity Data:**")
        st.sidebar.write(f"- Schedule loaded: {st.session_state.schedule_loaded}")
        st.sidebar.write(f"- Schedule DF shape: {getattr(st.session_state.schedule_df, 'shape', 'None')}")
        st.sidebar.write(f"- Absence loaded: {st.session_state.absence_loaded}")
        st.sidebar.write(f"- Absence DF shape: {getattr(st.session_state.absence_df, 'shape', 'None')}")
        st.sidebar.write(f"- Capacity summary loaded: {st.session_state.capacity_summary_loaded}")
        st.sidebar.write(f"- Capacity summary DF shape: {getattr(st.session_state.capacity_summary_df, 'shape', 'None')}")
        st.sidebar.write(f"- Config available: {st.session_state.capacity_config is not None}")

    if st.sidebar.button("View Capacity Data"):
        if st.session_state.get('schedule_df') is not None:
            st.write("**Schedule Data:**")
            st.dataframe(st.session_state.schedule_df.head())
        
        if st.session_state.get('capacity_summary_df') is not None:
            st.write("**Capacity Summary:**")
            st.dataframe(st.session_state.capacity_summary_df.head())

# Main execution flow
if __name__ == "__main__":
    if not is_data_loaded():
        # Auto-load data on first run
        auto_load_data()
        
        # Check if we should show uploader (no parquet files found)
        if st.session_state.show_uploader:
            from ui.uploader import render_upload_interface
            render_upload_interface()
        elif not is_data_loaded():
            # Show loading screen while attempting to load
            show_loading_screen()
    else:
        # Render the dashboard with data
        render_dashboard()

# ui/uploader.py
import streamlit as st
from app_explainer import get_app_explainer_text
from utils.currency_formatter import get_currency_selector, get_currency_display_name

def render_upload_interface():
    """
    Renders the initial data upload interface when no data is loaded.
    """
    # Set page title
    st.title('Arkemy: Turn Your Project Data Into Gold 🥇')
    st.markdown("##### v1.3.1 Parquet")

    # Create a container for all uploaders
    st.markdown("### Data Upload")
    st.markdown("Upload your Parquet file to begin analyzing your project data.")
    
    # Create a 2-column layout
    col1, col2 = st.columns(2)
    
    with col1:
        # Parquet file uploader
        st.markdown("#### 1. Combined Data File (Required)")
        parquet_file = st.file_uploader("Select and upload combined Parquet file", type=["parquet", "pq"], key="parquet_uploader")
        
        # Currency selector (required)
        st.markdown("#### 2. Currency Setting (Required)")
        currency_valid, currency_message = get_currency_selector("upload_currency_selector", required=True)
        
        # Show the current currency selection
        if currency_valid:
            st.success(f"Selected currency: {get_currency_display_name()}")
            st.session_state.currency_selected = True
        
        # Process Parquet file if both file is uploaded AND currency is selected
        if parquet_file is not None and currency_valid:
            process_button = st.button("Process Data", key="process_data_button")
            
            if process_button:
                from ui.parquet_processor import process_parquet_data
                process_parquet_data(parquet_file)
    
    with col2:
        # Display app explainer text in the second column
        st.markdown(get_app_explainer_text(), unsafe_allow_html=True)
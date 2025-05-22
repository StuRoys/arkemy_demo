# ui/parquet_processor.py
import streamlit as st
import pandas as pd
import gc
import os
import re
from utils.data_validation import validate_csv_schema, transform_csv, display_validation_results
from utils.planned_validation import validate_planned_schema, transform_planned_csv, display_planned_validation_results
from utils.person_reference import enrich_person_data
from utils.project_reference import enrich_project_data
from utils.planned_processors import calculate_planned_summary_metrics

# Add a cached function for reading Parquet data by source
@st.cache_data
def read_parquet_data_from_path(parquet_path, data_source, columns=None):
    """
    Reads data from a Parquet file for a specific data source with optional column selection.
    
    Args:
        parquet_path: Path to the Parquet file
        data_source: The data source to filter by ('main', 'planned', etc.)
        columns: Optional list of columns to load
        
    Returns:
        DataFrame containing the requested data
    """
    # Default columns to load for each data source if not specified
    if columns is None:
        # Always include data_source column for filtering
        if data_source == 'main':
            # Main data requires most columns
            columns = None  # Load all columns for main data to be safe
        elif data_source == 'planned':
            # Planned data needs fewer columns
            columns = ['data_source', 'Date', 'Person', 'Project number', 'Project', 'Planned hours', 'Planned rate']
        elif data_source == 'person_reference':
            # Person reference data needs minimal columns
            columns = ['data_source', 'Person', 'Person type']
        elif data_source == 'project_reference':
            # Project reference data - load all columns as we don't know which metadata is needed
            columns = None
    
    try:
        # Use PyArrow engine for better performance
        if columns is None:
            # Read all columns
            df = pd.read_parquet(parquet_path, engine='pyarrow')
        else:
            # Read only specified columns
            df = pd.read_parquet(parquet_path, engine='pyarrow', columns=columns)
        
        # Filter by data source
        if 'data_source' in df.columns:
            filtered_df = df[df['data_source'] == data_source]
            
            # Drop the data_source column as it's no longer needed
            if 'data_source' in filtered_df.columns:
                filtered_df = filtered_df.drop(columns=['data_source'])
                
            return filtered_df
        else:
            # If data_source column doesn't exist, return empty DataFrame
            return pd.DataFrame()
    except Exception as e:
        # Return empty DataFrame on error
        print(f"Error reading Parquet data for {data_source}: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def get_data_sources_from_path(parquet_path):
    """
    Get available data sources from Parquet file.
    
    Args:
        parquet_path: Path to the Parquet file
        
    Returns:
        List of data sources
    """
    try:
        # Read just the data_source column for efficiency
        df = pd.read_parquet(parquet_path, engine='pyarrow', columns=['data_source'])
        return df['data_source'].unique().tolist()
    except Exception as e:
        print(f"Error getting data sources: {str(e)}")
        return []

# Apply caching to data transformation functions to improve performance
@st.cache_data
def cached_transform_csv(df):
    """Cached wrapper for transform_csv function"""
    return transform_csv(df)

@st.cache_data
def cached_transform_planned_csv(df):
    """Cached wrapper for transform_planned_csv function"""
    return transform_planned_csv(df)

@st.cache_data
def cached_enrich_person_data(df, reference_df):
    """Cached wrapper for enrich_person_data function"""
    return enrich_person_data(df, reference_df)

@st.cache_data
def cached_enrich_project_data(df, reference_df):
    """Cached wrapper for enrich_project_data function"""
    return enrich_project_data(df, reference_df)

def extract_currency_from_filename(filepath):
    """Extract currency from filename like 'data_NOK.parquet'"""
    filename = os.path.basename(filepath)
    # Look for currency pattern: 3 letters after underscore or dash
    match = re.search(r'[_-]([A-Z]{3})', filename.upper())
    if match:
        currency = match.group(1).lower()
        supported = ['nok', 'usd', 'eur', 'gbp', 'sek', 'dkk']
        return currency if currency in supported else None
    return None

def process_parquet_data_from_path(parquet_path):
    """
    Processes a Parquet file from file system path that contains combined datasets.
    
    Args:
        parquet_path: Path to the Parquet file
    """
    try:
        # Extract and set currency from filename first
        currency = extract_currency_from_filename(parquet_path)
        if currency:
            st.session_state.currency = currency
            st.session_state.currency_selected = True
            st.success(f"Currency detected from filename: {currency.upper()}")
        else:
            st.session_state.currency = 'nok'  # fallback
            st.session_state.currency_selected = True
            st.info("No currency in filename, using NOK as default")
        
        # Validate file exists
        if not os.path.exists(parquet_path):
            st.error(f"File not found: {parquet_path}")
            return
        
        # Get available data sources first (this is cached)
        data_sources = get_data_sources_from_path(parquet_path)
        
        if not data_sources:
            st.error("The Parquet file does not contain a 'data_source' column. Please use a Parquet file created with the conversion tool.")
            return
        
        # Display basic information about the data sources
        st.success(f"Successfully detected data sources in Parquet file.")
        st.info(f"Data sources found: {', '.join(data_sources)}")
        
        # Load main data first (this is cached)
        main_data = read_parquet_data_from_path(parquet_path, 'main')
        
        # Process main data
        if main_data.empty:
            st.error("No main project data found in the Parquet file.")
            return
        
        st.success(f"Loaded main data with {main_data.shape[0]} rows and {main_data.shape[1]} columns.")
        
        # Validate main data schema
        validation_results = validate_csv_schema(main_data)
        display_validation_results(validation_results)
        
        # If the data is valid, proceed with transformation and store in session state
        if validation_results["is_valid"]:
            transformed_df = cached_transform_csv(main_data)
            st.session_state.transformed_df = transformed_df
            st.session_state.csv_loaded = True
            
            # Clean up memory
            del main_data
            gc.collect()
            
            # Process planned data if available
            if 'planned' in data_sources:
                # Load planned data (this is cached)
                planned_data = read_parquet_data_from_path(parquet_path, 'planned')
                
                if planned_data is not None and not planned_data.empty:
                    planned_validation_results = validate_planned_schema(planned_data)
                    st.subheader("Planned Hours Validation")
                    display_planned_validation_results(planned_validation_results)
                    
                    if planned_validation_results["is_valid"]:
                        transformed_planned_df = cached_transform_planned_csv(planned_data)
                        st.session_state.transformed_planned_df = transformed_planned_df
                        st.session_state.planned_csv_loaded = True
                        st.success(f"Loaded planned hours data with {planned_data.shape[0]} rows.")
                        
                        # Calculate and display summary metrics for planned hours
                        planned_metrics = calculate_planned_summary_metrics(transformed_planned_df)
                        st.info(
                            f"Total planned hours: {int(planned_metrics['total_planned_hours']):,}\n"
                            f"Projects: {planned_metrics['unique_projects']}\n"
                            f"People: {planned_metrics['unique_people']}"
                        )
                        
                        # Store max planned date in session state for date filter extension
                        if 'Date' in transformed_planned_df.columns and not transformed_planned_df.empty:
                            st.session_state.planned_max_date = transformed_planned_df['Date'].max().date()
                            st.info(f"Planned hours extend to: {st.session_state.planned_max_date}")
                
                # Clean up memory
                del planned_data
                gc.collect()
            
            # Process person reference data if available
            if 'person_reference' in data_sources:
                # Load person reference data (this is cached)
                person_ref_data = read_parquet_data_from_path(parquet_path, 'person_reference')
                
                if person_ref_data is not None and not person_ref_data.empty:
                    # Validate basic structure (must have Person and Person type columns)
                    if "Person" not in person_ref_data.columns or "Person type" not in person_ref_data.columns:
                        st.error("Person reference data must contain 'Person' and 'Person type' columns")
                    else:
                        # Make sure Person type values are standardized (convert to lowercase)
                        person_ref_data['Person type'] = person_ref_data['Person type'].str.lower()
                        
                        # Store in session state
                        st.session_state.person_reference_df = person_ref_data
                        st.success(f"Loaded person reference data with {person_ref_data.shape[0]} entries.")
                        
                        # Immediately apply to the main dataframe if it exists
                        if 'transformed_df' in st.session_state and st.session_state.transformed_df is not None:
                            st.session_state.transformed_df = cached_enrich_person_data(
                                st.session_state.transformed_df, 
                                person_ref_data
                            )
                
                # Clean up memory
                del person_ref_data
                gc.collect()
            
            # Process project reference data if available
            if 'project_reference' in data_sources:
                # Load project reference data (this is cached)
                project_ref_data = read_parquet_data_from_path(parquet_path, 'project_reference')
                
                if project_ref_data is not None and not project_ref_data.empty:
                    # Validate basic structure (must have Project number column)
                    if "Project number" not in project_ref_data.columns:
                        st.error("Project reference data must contain 'Project number' column")
                    else:
                        st.session_state.project_reference_df = project_ref_data
                        st.success(f"Loaded project reference data with {project_ref_data.shape[0]} entries.")
                        
                        # Immediately apply to the main dataframe if it exists
                        if 'transformed_df' in st.session_state and st.session_state.transformed_df is not None:
                            st.session_state.transformed_df = cached_enrich_project_data(
                                st.session_state.transformed_df, 
                                project_ref_data
                            )
                            st.success("Applied project reference data to main dataset.")
                        
                        # Show sample of the data and metadata columns
                        with st.expander("Project Reference Data"):
                            st.write(project_ref_data.head())
                            metadata_columns = [col for col in project_ref_data.columns if col != 'Project number']
                            if metadata_columns:
                                st.info(f"Metadata columns: {', '.join(metadata_columns)}")
                            else:
                                st.warning("No metadata columns found besides 'Project number'")
                
                # Clean up memory
                del project_ref_data
                gc.collect()
            
            # Final cleanup
            gc.collect()
            
            # Reset loading flag so dashboard can render
            st.session_state.data_loading_attempted = False
            
            # Force page refresh to show dashboard
            st.rerun()
            
    except Exception as e:
        st.error(f"Error processing the Parquet file: {str(e)}")

# Keep original function for backward compatibility (if needed elsewhere)
def process_parquet_data(parquet_file):
    """
    Legacy function for processing uploaded Parquet files.
    Kept for backward compatibility.
    """
    # This would need to handle the uploaded file object differently
    # For now, just raise an error suggesting the new approach
    st.error("Upload-based processing is deprecated. Please use file-based loading instead.")
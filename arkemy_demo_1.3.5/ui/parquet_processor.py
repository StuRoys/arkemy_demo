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

# Import capacity-related functions
from utils.capacity_validation import (
    validate_schedule_schema, validate_absence_schema, validate_capacity_config_schema, validate_weekly_source_schema,
    display_schedule_validation_results, display_absence_validation_results, 
    display_capacity_config_validation_results, display_weekly_source_validation_results,
    load_client_absence_config
)
from utils.weekly_data_transformer import (
    transform_weekly_to_schedule, transform_weekly_to_absence, load_capacity_config_from_dataframe,
    create_capacity_summary, validate_weekly_data_completeness, get_capacity_processing_summary
)

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
        elif data_source in ['schedule', 'absence', 'capacity_config', 'weekly_source']:
            # Capacity-related data sources - load all columns to handle dynamic schemas
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

# Add cached wrappers for capacity functions
@st.cache_data
def cached_transform_weekly_to_schedule(weekly_df):
    """Cached wrapper for transform_weekly_to_schedule function"""
    return transform_weekly_to_schedule(weekly_df)

@st.cache_data
def cached_transform_weekly_to_absence(weekly_df, capacity_config):
    """Cached wrapper for transform_weekly_to_absence function"""
    return transform_weekly_to_absence(weekly_df, capacity_config)

@st.cache_data
def cached_create_capacity_summary(schedule_df, absence_df, capacity_config):
    """Cached wrapper for create_capacity_summary function"""
    return create_capacity_summary(schedule_df, absence_df, capacity_config)

def extract_currency_from_filename(filepath):
    """Extract currency from filename like 'data_NOK.parquet'"""
    filename = os.path.basename(filepath)
    # Look for currency pattern: 3 letters after underscore or dash, before extension or end of filename
    # Try multiple patterns to find currency codes
    patterns = [
        r'[_-]([A-Z]{3})(?:\.[^.]+)?$',  # 3 letters after underscore/dash at end or before extension
        r'[_-]([A-Z]{3})[_-]',           # 3 letters between underscores/dashes
    ]
    
    filename_upper = filename.upper()
    supported = ['nok', 'usd', 'eur', 'gbp', 'sek', 'dkk']
    
    for pattern in patterns:
        match = re.search(pattern, filename_upper)
        if match:
            currency = match.group(1).lower()
            if currency in supported:
                return currency
    
    return None

def extract_client_from_filename(filepath):
    """Extract client ID from filename"""
    filename = os.path.basename(filepath).lower()
    if 'nuno' in filename:
        return 'nuno'
    # Add other clients here as needed
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
        else:
            st.session_state.currency = 'nok'  # fallback
            st.session_state.currency_selected = True
        
        # Validate file exists
        if not os.path.exists(parquet_path):
            st.error(f"File not found: {parquet_path}")
            return
        
        # Extract client ID from filename
        client_id = extract_client_from_filename(parquet_path)
        
        # Load capacity configuration from YAML if client detected
        capacity_config = None
        if client_id:
            try:
                capacity_config = load_client_absence_config(client_id)
                st.session_state.capacity_config = capacity_config
                st.success(f"Loaded capacity configuration for client: {client_id}")
                
                # Show config summary
                with st.expander("Capacity Configuration Details"):
                    st.json(capacity_config)
            except Exception as e:
                st.warning(f"Could not load capacity config for {client_id}: {str(e)}")
        
        # Get available data sources (this is cached)
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
            
            # Process capacity data sources
            process_capacity_data_sources(parquet_path, data_sources, capacity_config)
            
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

def process_capacity_data_sources(parquet_path, data_sources, capacity_config):
    """
    Process all capacity-related data sources.
    
    Args:
        parquet_path: Path to the parquet file
        data_sources: List of available data sources
        capacity_config: Parsed capacity configuration (can be None)
    """
    
    # Check for capacity data sources
    has_schedule = 'schedule' in data_sources
    has_absence = 'absence' in data_sources  
    has_weekly_source = 'weekly_source' in data_sources
    
    if not (has_schedule or has_absence or has_weekly_source):
        # No capacity data sources found
        return
    
    st.subheader("Capacity Data Processing")
    
    # Initialize capacity dataframes
    schedule_df = pd.DataFrame()
    absence_df = pd.DataFrame()
    
    # Process weekly source data (your raw format)
    if has_weekly_source:
        weekly_data = read_parquet_data_from_path(parquet_path, 'weekly_source')
        st.session_state.weekly_source_df = weekly_data  # Add this line

        
        if not weekly_data.empty:
            # Validate weekly source data
            weekly_validation_results = validate_weekly_source_schema(weekly_data)
            display_weekly_source_validation_results(weekly_validation_results)
            
            if weekly_validation_results["is_valid"]:
                # Validate data completeness against config if available
                if capacity_config:
                    completeness_results = validate_weekly_data_completeness(weekly_data, capacity_config)
                    
                    if not completeness_results["is_complete"]:
                        st.warning("Weekly data validation warnings:")
                        for warning in completeness_results["warnings"]:
                            st.warning(f"• {warning}")
                        
                        if completeness_results["suggestions"]:
                            st.info("Suggestions:")
                            for suggestion in completeness_results["suggestions"]:
                                st.info(f"• {suggestion}")
                
                # Transform weekly data to schedule format
                schedule_df = cached_transform_weekly_to_schedule(weekly_data)
                st.success(f"Transformed weekly data to schedule format: {len(schedule_df)} records")
                
                # Transform weekly data to absence format (if config available)
                if capacity_config:
                    absence_df = cached_transform_weekly_to_absence(weekly_data, capacity_config)
                    st.success(f"Transformed weekly data to absence format: {len(absence_df)} records")
                else:
                    st.warning("Capacity configuration not available - absence data not processed")
        
        # Clean up memory
        del weekly_data
        gc.collect()
    
    # Process direct schedule data source (if separate from weekly)
    elif has_schedule:
        schedule_data = read_parquet_data_from_path(parquet_path, 'schedule')
        
        if not schedule_data.empty:
            schedule_validation_results = validate_schedule_schema(schedule_data)
            display_schedule_validation_results(schedule_validation_results)
            
            if schedule_validation_results["is_valid"]:
                schedule_df = schedule_data
                st.success(f"Loaded schedule data: {len(schedule_df)} records")
        
        # Clean up memory
        del schedule_data
        gc.collect()
    
    # Process direct absence data source (if separate from weekly)
    if has_absence and absence_df.empty:  # Only if not already processed from weekly
        absence_data = read_parquet_data_from_path(parquet_path, 'absence')
        
        if not absence_data.empty:
            absence_validation_results = validate_absence_schema(absence_data)
            display_absence_validation_results(absence_validation_results)
            
            if absence_validation_results["is_valid"]:
                absence_df = absence_data
                st.success(f"Loaded absence data: {len(absence_df)} records")
        
        # Clean up memory
        del absence_data
        gc.collect()
    
    # Store capacity data in session state and create summary
    if not schedule_df.empty:
        st.session_state.schedule_df = schedule_df
        st.session_state.schedule_loaded = True
        
        if not absence_df.empty:
            st.session_state.absence_df = absence_df
            st.session_state.absence_loaded = True
        
        # Create capacity summary if we have required data
        if capacity_config:
            capacity_summary_df = cached_create_capacity_summary(schedule_df, absence_df, capacity_config)
            st.session_state.capacity_summary_df = capacity_summary_df
            st.session_state.capacity_summary_loaded = True
            
            # Display processing summary
            processing_summary = get_capacity_processing_summary(schedule_df, absence_df, capacity_config)
            
            with st.expander("Capacity Processing Summary"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Schedule Records", processing_summary["schedule_records"])
                    st.metric("Unique Persons", processing_summary["unique_persons"])
                
                with col2:
                    st.metric("Absence Records", processing_summary["absence_records"]) 
                    st.metric("Total Scheduled Hours", f"{processing_summary['total_scheduled_hours']:,.0f}")
                
                with col3:
                    st.metric("Total Absence Hours", f"{processing_summary['total_absence_hours']:,.0f}")
                    if processing_summary["date_range"]:
                        date_range = processing_summary["date_range"]
                        st.info(f"Period: {date_range['start'].strftime('%Y-%m-%d')} to {date_range['end'].strftime('%Y-%m-%d')}")
            
            st.success("Capacity analysis data is ready for dashboard use.")

# Keep original function for backward compatibility (if needed elsewhere)
def process_parquet_data(parquet_file):
    """
    Legacy function for processing uploaded Parquet files.
    Kept for backward compatibility.
    """
    # This would need to handle the uploaded file object differently
    # For now, just raise an error suggesting the new approach
    st.error("Upload-based processing is deprecated. Please use file-based loading instead.")
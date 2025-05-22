# filters.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any, Set


def create_date_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Create date range filters for the dataframe.
    
    Args:
        df: The input dataframe with a 'Date' column
        
    Returns:
        Tuple of (filtered dataframe, filter settings dictionary)
    """
    filter_settings = {}
    
    # Check if Date column exists
    if 'Date' not in df.columns:
        st.error("Date column not found in data")
        return df, filter_settings
    
    # Ensure Date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'])
    
    # Get min and max dates from the dataframe
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()
    
    # If planned hours data exists with future dates, extend max_date for "All time" filter
    planned_max_date_exists = 'planned_max_date' in st.session_state
    if planned_max_date_exists and st.session_state.planned_max_date > max_date:
        planned_max_date = st.session_state.planned_max_date
    else:
        planned_max_date = max_date
    
    # Create date filter controls
    with st.sidebar.expander("Date", expanded=True):
        # Date range options
        date_filter_options = [
            "All time",
            #"This month",
            "Last month",
            #"This quarter",
            "Last quarter",
            "Current year",
            "Last year",
            "Custom range"
        ]
        
        date_filter_type = st.selectbox(
            "Select date range",
            options=date_filter_options,
            index=0
        )
    
        # Initialize start and end dates
        start_date = min_date
        end_date = max_date
        
        # Process the selected date range
        if date_filter_type == "This month":
            today = datetime.now().date()
            start_date = datetime(today.year, today.month, 1).date()
            
        elif date_filter_type == "Last month":
            today = datetime.now().date()
            # Get first day of current month
            first_day_current = datetime(today.year, today.month, 1).date()
            # Subtract one day to get last day of previous month
            last_day_prev = first_day_current - timedelta(days=1)
            # Get first day of previous month
            start_date = datetime(last_day_prev.year, last_day_prev.month, 1).date()
            end_date = last_day_prev
            
        elif date_filter_type == "This quarter":
            today = datetime.now().date()
            current_quarter = (today.month - 1) // 3 + 1
            start_date = datetime(today.year, (current_quarter - 1) * 3 + 1, 1).date()
            
        elif date_filter_type == "Last quarter":
            today = datetime.now().date()
            current_quarter = (today.month - 1) // 3 + 1
            prev_quarter = current_quarter - 1 if current_quarter > 1 else 4
            year = today.year if current_quarter > 1 else today.year - 1
            start_date = datetime(year, (prev_quarter - 1) * 3 + 1, 1).date()
            end_date = datetime(today.year, (current_quarter - 1) * 3 + 1, 1).date() - timedelta(days=1)
            
        elif date_filter_type == "Current year":
            today = datetime.now().date()
            start_date = datetime(today.year, 1, 1).date()
            # If planned hours extend into future, extend to planned_max_date for current year
            if planned_max_date_exists and today.year == planned_max_date.year and planned_max_date > today:
                end_date = planned_max_date
            
        elif date_filter_type == "Last year":
            today = datetime.now().date()
            start_date = datetime(today.year - 1, 1, 1).date()
            end_date = datetime(today.year, 1, 1).date() - timedelta(days=1)
            
        elif date_filter_type == "Custom range":
            # Move these column definitions inside the sidebar expander
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                start_date = st.date_input(
                    "Start date",
                    value=min_date,
                    #min_value=min_date,
                    #max_value=max_date
                )
                
            with col2:
                # For custom range, allow selection up to the planned max date if available
                display_max_date = planned_max_date if planned_max_date_exists else max_date
                end_date = st.date_input(
                    "End date",
                    value=display_max_date,
                    #min_value=min_date,
                    #max_value=display_max_date
                )
        
        # For "All time" specifically, extend to include planned hours future dates
        if date_filter_type == "All time" and planned_max_date_exists:
            end_date = planned_max_date
            
            # Show an info message when extending the date range
            if planned_max_date > max_date:
                st.info(f"Date range extended to include planned hours (up to {planned_max_date})")
    
    # Apply date filter
    mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
    filtered_df = df[mask]
    
    # Store filter settings
    filter_settings['date_filter_type'] = date_filter_type
    filter_settings['start_date'] = start_date
    filter_settings['end_date'] = end_date
    
    # Add info about planned date extension
    filter_settings['includes_planned_future_dates'] = (
        planned_max_date_exists and 
        planned_max_date > max_date and 
        end_date >= max_date
    )
    
    return filtered_df, filter_settings


def create_customer_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Create customer filter with empty selection meaning 'All'"""
    filter_settings = {}
    
    if 'Customer number' not in df.columns or 'Customer name' not in df.columns:
        return df, filter_settings
    
    with st.sidebar.expander("Customer"):
        # Get unique customers
        customers = df[['Customer number', 'Customer name']].drop_duplicates()
        customers['Customer'] = customers['Customer name'] + ' (' + customers['Customer number'] + ')'
        customer_options = customers['Customer'].tolist()
        
        # Simple multiselect (empty = all)
        selected_customers = st.multiselect(
            "Select specific customers",
            options=customer_options
        )
        
        # Create exclude multiselect
        exclude_customers = st.multiselect(
            "Exclude customers",
            options=customer_options
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    # Filter for included customers if any selected
    if selected_customers:
        included_ids = [c.split('(')[-1].split(')')[0] for c in selected_customers]
        filtered_df = filtered_df[filtered_df['Customer number'].isin(included_ids)]
    
    # Apply exclusions if any
    if exclude_customers:
        excluded_ids = [c.split('(')[-1].split(')')[0] for c in exclude_customers]
        filtered_df = filtered_df[~filtered_df['Customer number'].isin(excluded_ids)]
    
    # Store filter settings
    filter_settings['include_all_customers'] = len(selected_customers) == 0
    filter_settings['included_customers'] = [c.split('(')[-1].split(')')[0] for c in selected_customers]
    filter_settings['excluded_customers'] = [c.split('(')[-1].split(')')[0] for c in exclude_customers]
    
    return filtered_df, filter_settings


# This is the modified create_project_filter function in filters.py
def create_project_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Create project filters for the dataframe with include/exclude options.
    
    Args:
        df: The input dataframe
        
    Returns:
        Tuple of (filtered dataframe, filter settings dictionary)
    """
    filter_settings = {}
    
    # Check if project columns exist
    has_project_data = 'Project number' in df.columns and 'Project' in df.columns
    
    if not has_project_data:
        return df, filter_settings
    
    # Create project filter controls
    with st.sidebar.expander("Project"):
        # Get unique projects
        projects = df[['Project number', 'Project']].drop_duplicates()
        projects['Project label'] = projects['Project'] + ' (' + projects['Project number'] + ')'
        project_options = projects['Project label'].tolist()
        
        # Simple multiselect (empty = all)
        selected_projects = st.multiselect(
            "Select specific projects",
            options=project_options
        )
        
        # Create exclude multiselect
        exclude_projects = st.multiselect(
            "Exclude projects",
            options=project_options
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    # Filter for included projects if any selected
    if selected_projects:
        included_ids = [p.split('(')[-1].split(')')[0] for p in selected_projects]
        filtered_df = filtered_df[filtered_df['Project number'].isin(included_ids)]
    
    # Apply exclusions if any
    if exclude_projects:
        excluded_ids = [p.split('(')[-1].split(')')[0] for p in exclude_projects]
        filtered_df = filtered_df[~filtered_df['Project number'].isin(excluded_ids)]
    
    # Store filter settings
    filter_settings['include_all_projects'] = len(selected_projects) == 0
    filter_settings['included_projects'] = [p.split('(')[-1].split(')')[0] for p in selected_projects]
    filter_settings['excluded_projects'] = [p.split('(')[-1].split(')')[0] for p in exclude_projects]
    
    return filtered_df, filter_settings

def create_project_type_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Create project type filter for the dataframe with include/exclude options.
    
    Args:
        df: The input dataframe
        
    Returns:
        Tuple of (filtered dataframe, filter settings dictionary)
    """
    filter_settings = {}
    
    # Check if project type column exists
    if 'Project type' not in df.columns:
        return df, filter_settings
    
    # Create project type filter controls
    with st.sidebar.expander("Project Type"):
        project_types = sorted(df['Project type'].unique().tolist())
        
        # Simple multiselect (empty = all)
        selected_types = st.multiselect(
            "Select specific project types",
            options=project_types
        )
        
        # Create exclude multiselect
        exclude_types = st.multiselect(
            "Exclude project types",
            options=project_types
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    # Filter for included project types if any selected
    if selected_types:
        filtered_df = filtered_df[filtered_df['Project type'].isin(selected_types)]
    
    # Apply exclusions if any
    if exclude_types:
        filtered_df = filtered_df[~filtered_df['Project type'].isin(exclude_types)]
    
    # Store filter settings
    filter_settings['include_all_types'] = len(selected_types) == 0
    filter_settings['included_types'] = selected_types
    filter_settings['excluded_types'] = exclude_types
    
    return filtered_df, filter_settings


def create_price_model_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Create price model filter for the dataframe with include/exclude options.
    
    Args:
        df: The input dataframe
        
    Returns:
        Tuple of (filtered dataframe, filter settings dictionary)
    """
    filter_settings = {}
    
    # Check if Price model column exists
    if 'Price model' not in df.columns:
        return df, filter_settings
    
    # Create price model filter controls
    with st.sidebar.expander("Price Model"):
        price_models = sorted(df['Price model'].unique().tolist())
        
        # Simple multiselect (empty = all)
        selected_models = st.multiselect(
            "Select specific price models",
            options=price_models
        )
        
        # Create exclude multiselect
        exclude_models = st.multiselect(
            "Exclude price models",
            options=price_models
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    # Filter for included price models if any selected
    if selected_models:
        filtered_df = filtered_df[filtered_df['Price model'].isin(selected_models)]
    
    # Apply exclusions if any
    if exclude_models:
        filtered_df = filtered_df[~filtered_df['Price model'].isin(exclude_models)]
    
    # Store filter settings
    filter_settings['include_all_models'] = len(selected_models) == 0
    filter_settings['included_models'] = selected_models
    filter_settings['excluded_models'] = exclude_models
    
    return filtered_df, filter_settings

def create_activity_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Create activity and phase filters for the dataframe with include/exclude options.
    
    Args:
        df: The input dataframe
        
    Returns:
        Tuple of (filtered dataframe, filter settings dictionary)
    """
    filter_settings = {}
    
    # Check if activity columns exist
    has_activity = 'Activity' in df.columns
    has_phase = 'Phase' in df.columns
    
    if not has_activity and not has_phase:
        return df, filter_settings
    
    filtered_df = df.copy()
    
    # Phase filter (if available)
    if has_phase:
        with st.sidebar.expander("Phase"):
            phases = sorted(df['Phase'].unique().tolist())
            
            # Simple multiselect (empty = all)
            selected_phases = st.multiselect(
                "Select specific phases",
                options=phases
            )
            
            # Create exclude multiselect
            exclude_phases = st.multiselect(
                "Exclude phases",
                options=phases
            )
        
        # Apply phase filters
        if selected_phases:
            filtered_df = filtered_df[filtered_df['Phase'].isin(selected_phases)]
        
        if exclude_phases:
            filtered_df = filtered_df[~filtered_df['Phase'].isin(exclude_phases)]
            
        # Store filter settings
        filter_settings['include_all_phases'] = len(selected_phases) == 0
        filter_settings['included_phases'] = selected_phases
        filter_settings['excluded_phases'] = exclude_phases
    
    # Activity filter (if available)
    if has_activity:
        with st.sidebar.expander("Activity"):
            activities = sorted(filtered_df['Activity'].unique().tolist())
            
            # Simple multiselect (empty = all)
            selected_activities = st.multiselect(
                "Select specific activities",
                options=activities
            )
            
            # Create exclude multiselect
            exclude_activities = st.multiselect(
                "Exclude activities",
                options=activities
            )
        
        # Apply activity filters
        if selected_activities:
            filtered_df = filtered_df[filtered_df['Activity'].isin(selected_activities)]
        
        if exclude_activities:
            filtered_df = filtered_df[~filtered_df['Activity'].isin(exclude_activities)]
            
        # Store filter settings
        filter_settings['include_all_activities'] = len(selected_activities) == 0
        filter_settings['included_activities'] = selected_activities
        filter_settings['excluded_activities'] = exclude_activities
    
    return filtered_df, filter_settings


def create_person_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Create person filter for the dataframe with include/exclude options.
    
    Args:
        df: The input dataframe
        
    Returns:
        Tuple of (filtered dataframe, filter settings dictionary)
    """
    filter_settings = {}
    
    # Check if person column exists
    if 'Person' not in df.columns:
        return df, filter_settings
    
    # Create person filter controls
    with st.sidebar.expander("Person"):
        persons = sorted(df['Person'].unique().tolist())
        
        # Simple multiselect (empty = all)
        selected_persons = st.multiselect(
            "Select specific people",
            options=persons
        )
        
        # Create exclude multiselect
        exclude_persons = st.multiselect(
            "Exclude people",
            options=persons
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    # Filter for included persons if any selected
    if selected_persons:
        filtered_df = filtered_df[filtered_df['Person'].isin(selected_persons)]
    
    # Apply exclusions if any
    if exclude_persons:
        filtered_df = filtered_df[~filtered_df['Person'].isin(exclude_persons)]
    
    # Store filter settings
    filter_settings['include_all_persons'] = len(selected_persons) == 0
    filter_settings['included_persons'] = selected_persons
    filter_settings['excluded_persons'] = exclude_persons
    
    return filtered_df, filter_settings

def create_person_type_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Create person type filter for the dataframe.
    
    Args:
        df: The input dataframe
        
    Returns:
        Tuple of (filtered dataframe, filter settings dictionary)
    """
    filter_settings = {}
    
    # Check if Person type column exists
    if 'Person type' not in df.columns:
        return df, filter_settings
    
    # Create person type filter controls
    with st.sidebar.expander("Person Type (Internal/External)"):
        include_options = ["All", "Internal", "External"]
        selected_include = st.radio("Include person types", options=include_options, index=0)
    
    # Apply person type filter
    if selected_include == "Internal":
        # Handle case insensitivity and null values
        filtered_df = df[df['Person type'].fillna('').str.lower() == 'internal']
        filter_settings['selected_person_type'] = 'internal'
    elif selected_include == "External":
        # Handle case insensitivity and null values
        filtered_df = df[df['Person type'].fillna('').str.lower() == 'external']
        filter_settings['selected_person_type'] = 'external'
    else:
        filtered_df = df
        filter_settings['selected_person_type'] = 'all'
    
    return filtered_df, filter_settings


def create_project_hours_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Filter projects based on their total hours worked.
    
    Args:
        df: The input dataframe
        
    Returns:
        Tuple of (filtered dataframe, filter settings dictionary)
    """
    filter_settings = {}
    
    # Check if required columns exist
    if 'Project number' not in df.columns or 'Hours worked' not in df.columns:
        return df, filter_settings
    
    # Create a copy of the dataframe
    filtered_df = df.copy()
    
    # Calculate total hours per project
    project_hours = df.groupby('Project number')['Hours worked'].sum().reset_index()
    
    # Count total projects
    total_projects = project_hours['Project number'].nunique()
    
    # Create hours range filter controls
    with st.sidebar.expander("Project Hours Range"):
        # Add checkbox to enable/disable the filter
        enable_hours_filter = st.checkbox("Enable hours filter", value=False)
        
        # Fixed range values (not dependent on dataset)
        default_min = 0.0
        default_max = 100000.0
        
        col1, col2 = st.columns(2)
        with col1:
            min_selected_hours = st.number_input(
                "Min hours",
                min_value=0.0,
                max_value=default_max,
                value=default_min,
                step=0.1  # Allow decimal values
            )
        with col2:
            max_selected_hours = st.number_input(
                "Max hours",
                min_value=0.0,
                max_value=default_max * 10,  # Very large max to accommodate any project
                value=default_max,
                step=0.1  # Allow decimal values
            )

        # Only apply filter if enabled
        if enable_hours_filter:
            # Get list of projects that meet the criteria
            valid_projects = project_hours[
                (project_hours['Hours worked'] >= min_selected_hours) & 
                (project_hours['Hours worked'] <= max_selected_hours)
            ]['Project number'].tolist()
            
            # Count projects in range
            projects_in_range = len(valid_projects)
            
            # Display info message
            st.info(f"Showing {projects_in_range} of {total_projects} projects")

            # Check if there are any valid projects
            if not valid_projects:
                st.warning("No projects found with hours in the selected range.")
                # Return empty dataframe with same columns or original with no rows
                return pd.DataFrame(columns=df.columns), filter_settings

            # Filter the dataframe to include only those projects
            filtered_df = filtered_df[filtered_df['Project number'].isin(valid_projects)]
            
            # Store filter settings
            filter_settings['project_min_hours'] = min_selected_hours
            filter_settings['project_max_hours'] = max_selected_hours
            filter_settings['projects_in_range'] = projects_in_range
            filter_settings['project_hours_filter_enabled'] = True
        else:
            # Filter is disabled, show all projects
            projects_in_range = total_projects
            st.info(f"Filter disabled. Showing all {total_projects} projects.")
            
            # Store settings to indicate filter is disabled
            filter_settings['project_hours_filter_enabled'] = False
    
    # Always store these values for reference
    filter_settings['total_projects'] = total_projects
    
    return filtered_df, filter_settings


def create_billability_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Create billability filter for the dataframe.
    
    Args:
        df: The input dataframe
        
    Returns:
        Tuple of (filtered dataframe, filter settings dictionary)
    """
    filter_settings = {}
    
    # Check if hours columns exist
    if 'Hours worked' not in df.columns or 'Billable hours' not in df.columns:
        return df, filter_settings
    
    # Create billability filter controls
    with st.sidebar.expander("Billability"):
        include_options = ["All", "Billable / Partially", "Non-billable"]
        selected_include = st.radio("Include time records", options=include_options, index=0)
    
    # Apply billability filter
    if selected_include == "Billable / Partially":
        filtered_df = df[df['Billable hours'] > 0]
        filter_settings['selected_billability'] = 'billable'
    elif selected_include == "Non-billable":
        # Non-billable means billable hours are 0
        filtered_df = df[df['Billable hours'] == 0]
        filter_settings['selected_billability'] = 'non-billable'
    else:
        filtered_df = df
        filter_settings['selected_billability'] = 'all'
    
    return filtered_df, filter_settings


def apply_all_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Apply all filters to the dataframe.
    
    Args:
        df: The input dataframe
        
    Returns:
        Tuple of (filtered dataframe, combined filter settings dictionary)
    """
    # Initialize with a copy of the original dataframe
    filtered_df = df.copy()
    all_filter_settings = {}
    
    # Apply each filter in sequence
    # Each filter function will return a filtered dataframe and filter settings
    
    # Date filter
    filtered_df, date_settings = create_date_filters(filtered_df)
    all_filter_settings.update(date_settings)
    
    # Check if dataframe is already empty after date filter
    if filtered_df.empty:
        all_filter_settings['no_data'] = True
        return filtered_df, all_filter_settings
    
    # Customer filter
    filtered_df, customer_settings = create_customer_filter(filtered_df)
    all_filter_settings.update(customer_settings)
    
    # Check if dataframe is already empty after customer filter
    if filtered_df.empty:
        all_filter_settings['no_data'] = True
        return filtered_df, all_filter_settings
    
    # Project filter
    filtered_df, project_settings = create_project_filter(filtered_df)
    all_filter_settings.update(project_settings)
    
    # Check if dataframe is already empty after project filter
    if filtered_df.empty:
        all_filter_settings['no_data'] = True
        return filtered_df, all_filter_settings
    
    # Project type filter
    filtered_df, project_type_settings = create_project_type_filter(filtered_df)
    all_filter_settings.update(project_type_settings)
    
    # Check if dataframe is already empty after project type filter
    if filtered_df.empty:
        all_filter_settings['no_data'] = True
        return filtered_df, all_filter_settings
    
    # Price model filter (add this new section)
    filtered_df, price_model_settings = create_price_model_filter(filtered_df)
    all_filter_settings.update(price_model_settings)
    
    # Check if dataframe is already empty after price model filter
    if filtered_df.empty:
        all_filter_settings['no_data'] = True
        return filtered_df, all_filter_settings
    
    # Activity filter
    filtered_df, activity_settings = create_activity_filter(filtered_df)
    all_filter_settings.update(activity_settings)
    
    # Check if dataframe is already empty after activity filter
    if filtered_df.empty:
        all_filter_settings['no_data'] = True
        return filtered_df, all_filter_settings
    
    # Person filter
    filtered_df, person_settings = create_person_filter(filtered_df)
    all_filter_settings.update(person_settings)
    
    # Check if dataframe is already empty after person filter
    if filtered_df.empty:
        all_filter_settings['no_data'] = True
        return filtered_df, all_filter_settings
    
    # Person type filter (new)
    filtered_df, person_type_settings = create_person_type_filter(filtered_df)
    all_filter_settings.update(person_type_settings)
    
    # Check if dataframe is already empty after person type filter
    if filtered_df.empty:
        all_filter_settings['no_data'] = True
        return filtered_df, all_filter_settings
    
    # Project hours range filter
    try:
        filtered_df, project_hours_settings = create_project_hours_filter(filtered_df)
        all_filter_settings.update(project_hours_settings)
    except Exception as e:
        # If there's an error in the project hours filter, it might be due to empty data
        all_filter_settings['no_data'] = True
        return filtered_df, all_filter_settings
    
    # Billability filter
    filtered_df, billability_settings = create_billability_filter(filtered_df)
    all_filter_settings.update(billability_settings)

    # Check if the filtered dataframe is empty
    if filtered_df.empty:
        all_filter_settings['no_data'] = True
    else:
        all_filter_settings['no_data'] = False
        
    return filtered_df, all_filter_settings
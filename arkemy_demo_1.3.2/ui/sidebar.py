# ui/sidebar.py
import streamlit as st
from utils.filters import (
    create_date_filters, 
    create_customer_filter, 
    create_project_filter, 
    create_activity_filter, 
    create_person_filter, 
    create_person_type_filter, 
    create_project_hours_filter, 
    create_billability_filter,
    create_project_type_filter,
    create_price_model_filter
)
from utils.filter_display import display_filter_badges
from utils.project_reference import get_dynamic_project_filters

def render_sidebar_filters(df, planned_df=None):
    """
    Render filter controls in the sidebar and return filtered dataframes and settings.
    """
    # Create a copy of the input dataframe to avoid modifying the original
    filtered_df = df.copy()
    filter_settings = {}

    # Create a copy of planned_df and apply Person type mapping if needed
    if planned_df is not None:
        filtered_planned_df = planned_df.copy()
        
        # Create a mapping of Person → Person type from the main data
        if 'Person type' in df.columns:
            person_type_map = df[['Person', 'Person type']].drop_duplicates().set_index('Person')['Person type']
            
            # Apply this mapping directly to filtered_planned_df
            filtered_planned_df['Person type'] = filtered_planned_df['Person'].map(person_type_map)
            
            # Handle any persons in planned data that aren't in main data
            if filtered_planned_df['Person type'].isna().any():
                st.debug.info(f"Note: {filtered_planned_df['Person type'].isna().sum()} persons in planned data not found in main data")
    else:
        filtered_planned_df = None    

    # Apply dynamic project filters if reference data exists
    if 'project_reference_df' in st.session_state and st.session_state.project_reference_df is not None:
        try:
            # Always call the function to render UI
            temp_df, project_meta_settings, handled_columns = get_dynamic_project_filters(
                filtered_df, st.session_state.project_reference_df
            )
            
            filtered_df = temp_df
            filter_settings.update(project_meta_settings)
                
            if filtered_df.empty:
                filter_settings['no_data'] = True
        except Exception as e:
            st.sidebar.error(f"Error applying project metadata filters: {str(e)}")
            filter_settings['no_data'] = True
    
    # Apply all filters sequentially
    filter_functions = [
        create_date_filters,
        create_customer_filter,
        create_project_filter,
        create_project_type_filter,
        create_price_model_filter,
        create_activity_filter,
        create_person_filter,
        create_person_type_filter,
        create_project_hours_filter,
        create_billability_filter
    ]
    
    # Apply each filter function
    for filter_func in filter_functions:
        try:
            temp_df, new_settings = filter_func(filtered_df)
            filtered_df = temp_df
            filter_settings.update(new_settings)
        except Exception as e:
            st.sidebar.error(f"Error applying filter: {str(e)}")
    
    # Apply matching filters to planned data if available
    if filtered_planned_df is not None:
        # Match project filters if applicable
        if 'included_projects' in filter_settings and filter_settings['included_projects']:
            filtered_planned_df = filtered_planned_df[filtered_planned_df['Project number'].isin(filter_settings['included_projects'])]
        
        # Match excluded project filters if applicable
        if 'excluded_projects' in filter_settings and filter_settings['excluded_projects']:
            filtered_planned_df = filtered_planned_df[~filtered_planned_df['Project number'].isin(filter_settings['excluded_projects'])]
        
        # Match date filters if applicable
        if 'start_date' in filter_settings and 'end_date' in filter_settings:
            # Check if Date column exists in planned_df
            if 'Date' in filtered_planned_df.columns:
                # Apply date filter to planned data
                start_date = filter_settings['start_date']
                end_date = filter_settings['end_date']
                filtered_planned_df = filtered_planned_df[
                    (filtered_planned_df['Date'].dt.date >= start_date) & 
                    (filtered_planned_df['Date'].dt.date <= end_date)
                ]

            # Apply person type filter if applicable
            if 'selected_person_type' in filter_settings and filter_settings['selected_person_type'] != 'all':
                # Check if Person type column exists in planned_df
                if 'Person type' in filtered_planned_df.columns:
                    # Apply person type filter to planned data
                    if filter_settings['selected_person_type'] == 'internal':
                        filtered_planned_df = filtered_planned_df[filtered_planned_df['Person type'].fillna('').str.lower() == 'internal']
                    elif filter_settings['selected_person_type'] == 'external':
                        filtered_planned_df = filtered_planned_df[filtered_planned_df['Person type'].fillna('').str.lower() == 'external']
 
    # Display filter badges after all filters have been processed
    display_filter_badges(filter_settings, location="sidebar")
    
    # Add upload new dataset button at the bottom of the sidebar
    st.sidebar.markdown("---")  # Add a separator
    
    if 'reset_confirmation' not in st.session_state:
        st.session_state.reset_confirmation = False

    if st.session_state.reset_confirmation:
        st.sidebar.warning("Are you sure? All data will be lost.")
        col1, col2 = st.sidebar.columns(2)
        
        if col1.button("Yes, reset"):
            # Reset all session state variables
            for key in list(st.session_state.keys()):
                if key != 'reset_confirmation':  # Keep this one for now
                    del st.session_state[key]
            
            # Reset the confirmation flag and redirect
            st.session_state.reset_confirmation = False
            st.rerun()
        
        if col2.button("Cancel"):
            st.session_state.reset_confirmation = False
            st.rerun()
    else:
        if st.sidebar.button("Upload new dataset"):
            st.session_state.reset_confirmation = True
            st.rerun()
        
    return filtered_df, filtered_planned_df, filter_settings
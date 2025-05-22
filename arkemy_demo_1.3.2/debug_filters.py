# debug_filters.py
import streamlit as st

def debug_planned_data_filtering(planned_df, person_type_filter=None, location="sidebar"):
    """Debug helper that prints information about the planned data filtering
    
    Args:
        planned_df: The planned dataframe to inspect
        person_type_filter: The currently applied person type filter (if any)
        location: Where to show debug info ("sidebar" or "main")
    """
    display_func = st.sidebar.write if location == "sidebar" else st.write
    
    # Show header
    display_func("## DEBUG: Planned Data")
    
    # Check if planned dataframe exists
    if planned_df is None:
        display_func("No planned data available")
        return
    
    # Check shape
    display_func(f"Planned DF shape: {planned_df.shape[0]} rows × {planned_df.shape[1]} columns")
    
    # Check if Person type column exists
    has_person_type = 'Person type' in planned_df.columns
    display_func(f"Has Person type column: {has_person_type}")
    
    # Show Person type counts if the column exists
    if has_person_type:
        display_func("Person types in planned data:")
        person_type_counts = planned_df['Person type'].value_counts().to_dict()
        for ptype, count in person_type_counts.items():
            display_func(f"- {ptype}: {count} records")
        
        # Show nulls if any
        null_count = planned_df['Person type'].isna().sum()
        if null_count > 0:
            display_func(f"- NULL/NaN: {null_count} records")
    
    # Show filter status
    if person_type_filter:
        display_func(f"Current Person type filter: {person_type_filter}")
    else:
        display_func("No Person type filter applied")
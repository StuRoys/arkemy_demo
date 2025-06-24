# planned_validation.py
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import streamlit as st

# Define the expected schema for planned hours CSV
PLANNED_SCHEMA = {
    "Date": "datetime",
    "Person": "string",
    "Project number": "string",
    "Project": "string",
    "Planned hours": "float"
}

# All columns are required for the planned hours CSV
OPTIONAL_COLUMNS = []

def validate_planned_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates if the planned hours dataframe has the expected schema.
    
    Args:
        df: The dataframe to validate
        
    Returns:
        Dict with validation results
    """
    result = {
        "is_valid": True,
        "missing_columns": [],
        "type_errors": [],
        "problematic_values": {}  # Field to store problematic values
    }
    
    # Check for missing columns (exclude optional ones)
    for column in PLANNED_SCHEMA:
        if column not in df.columns and column not in OPTIONAL_COLUMNS:
            result["missing_columns"].append(column)
            result["is_valid"] = False
    
    if not result["is_valid"]:
        return result
    
    # Check data types
    for column, expected_type in PLANNED_SCHEMA.items():
        if column in df.columns:  # Only check columns that exist in the dataframe
            if expected_type == "datetime":
                try:
                    # Attempt to convert to datetime
                    pd.to_datetime(df[column])
                except Exception as e:
                    result["type_errors"].append(f"{column} is not a valid datetime")
                    result["is_valid"] = False
                    
                    # Store problematic values
                    problematic_rows = []
                    for idx, value in df[column].items():
                        try:
                            pd.to_datetime(value)
                        except:
                            problematic_rows.append((idx, value))
                    
                    if problematic_rows:
                        result["problematic_values"][column] = problematic_rows[:10]  # Limit to first 10
                
            elif expected_type == "float":
                try:
                    # Check if values can be converted to float
                    df[column].astype(float)
                except Exception as e:
                    result["type_errors"].append(f"{column} contains non-numeric values")
                    result["is_valid"] = False
                    
                    # Store problematic values
                    problematic_rows = []
                    for idx, value in df[column].items():
                        try:
                            float(value)
                        except:
                            problematic_rows.append((idx, value))
                    
                    if problematic_rows:
                        result["problematic_values"][column] = problematic_rows[:10]  # Limit to first 10
    
    return result

def transform_planned_csv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms the planned hours dataframe to match the expected schema.
    
    Args:
        df: The dataframe to transform
        
    Returns:
        Transformed dataframe
    """
    # Create a copy to avoid modifying the original
    transformed_df = df.copy()
    
    # Convert columns to the correct types
    for column, expected_type in PLANNED_SCHEMA.items():
        if column in transformed_df.columns:
            if expected_type == "datetime":
                # Ensure dates are properly converted to pandas datetime
                transformed_df[column] = pd.to_datetime(transformed_df[column])
            elif expected_type == "float":
                transformed_df[column] = pd.to_numeric(transformed_df[column], errors='coerce')
            elif expected_type == "string":
                transformed_df[column] = transformed_df[column].astype(str)
    
    return transformed_df

def display_planned_validation_results(validation_results: Dict[str, Any]) -> None:
    """
    Displays validation results for planned hours CSV in the Streamlit app.
    
    Args:
        validation_results: Dictionary with validation results
    """
    if validation_results["is_valid"]:
        st.success("Planned hours CSV data matches the expected schema!")
    else:
        st.error("Planned hours CSV data does not match the expected schema.")
        
        if validation_results["missing_columns"]:
            st.warning(f"Missing columns: {', '.join(validation_results['missing_columns'])}")
        
        if validation_results["type_errors"]:
            st.warning(f"Type errors: {', '.join(validation_results['type_errors'])}")
        
        # Display problematic values
        if "problematic_values" in validation_results and validation_results["problematic_values"]:
            st.subheader("Problematic Values")
            for column, values in validation_results["problematic_values"].items():
                st.write(f"**{column}** - Problematic values:")
                for idx, value in values:
                    st.write(f"Row {idx}: '{value}' (type: {type(value).__name__})")
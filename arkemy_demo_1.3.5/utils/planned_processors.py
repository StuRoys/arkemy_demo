# planned_processors.py
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

def aggregate_by_project_planned(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate planned hours data by project using simple pandas operations.
    
    Args:
        df: DataFrame with planned hours data
        
    Returns:
        Dataframe with project aggregations of planned hours
    """
    # Basic validation
    if df is None or df.empty:
        # Return empty dataframe with expected columns
        return pd.DataFrame(columns=["Project number", "Project", "Planned hours", "Number of people", "Planned rate", "Planned revenue"])
        
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # Convert Project number to string for consistent joining
    df["Project number"] = df["Project number"].astype(str)
    df["Project"] = df["Project"].fillna("Unknown Project")
    
    # Simple groupby aggregation by project
    project_agg = df.groupby(["Project number", "Project"], as_index=False).agg({
        "Planned hours": "sum",
        "Person": "nunique"
    })
    
    # Rename Person column to match expected format
    project_agg = project_agg.rename(columns={"Person": "Number of people"})
    
    # Add planned rate calculation if available
    if "Planned rate" in df.columns:
        # Calculate weighted rate per project
        rate_df = df.copy()
        rate_df["weighted_rate"] = rate_df["Planned rate"] * rate_df["Planned hours"]
        
        # Group and calculate weighted average
        rate_agg = rate_df.groupby("Project number", as_index=False).agg({
            "weighted_rate": "sum",
            "Planned hours": "sum"
        })
        
        # Calculate the weighted average rate
        rate_agg["Planned rate"] = 0.0
        mask = rate_agg["Planned hours"] > 0
        rate_agg.loc[mask, "Planned rate"] = rate_agg.loc[mask, "weighted_rate"] / rate_agg.loc[mask, "Planned hours"]
        
        # Merge rate with main aggregation
        project_agg = pd.merge(
            project_agg, 
            rate_agg[["Project number", "Planned rate"]], 
            on="Project number",
            how="left"
        )
        
        # Calculate planned revenue
        project_agg["Planned revenue"] = project_agg["Planned hours"] * project_agg["Planned rate"]
    else:
        # Add placeholder columns
        project_agg["Planned rate"] = 0
        project_agg["Planned revenue"] = 0
    
    return project_agg

def merge_actual_planned_projects(actual_df: pd.DataFrame, planned_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge actual and planned hours data at the project level.
    
    Args:
        actual_df: DataFrame with actual project aggregations
        planned_df: DataFrame with planned project aggregations
        
    Returns:
        Merged dataframe with both actual and planned metrics
    """
    # Ensure inputs are valid
    if actual_df is None or actual_df.empty:
        return planned_df
    
    if planned_df is None or planned_df.empty:
        return actual_df
    
    # Make copies to avoid modifying originals
    actual_df = actual_df.copy()
    planned_df = planned_df.copy()
    
    # Ensure Project number is string type
    actual_df["Project number"] = actual_df["Project number"].astype(str)
    planned_df["Project number"] = planned_df["Project number"].astype(str)
    
    # Get required columns from planned data
    planned_cols = ["Project number", "Project", "Planned hours"]
    if "Planned rate" in planned_df.columns:
        planned_cols.append("Planned rate")
    if "Planned revenue" in planned_df.columns:
        planned_cols.append("Planned revenue")
    
    # Simple outer merge on Project number and name
    merged_df = pd.merge(
        actual_df,
        planned_df[planned_cols],
        on=["Project number", "Project"],
        how="outer"  # Include all projects from both dataframes
    )
    
    # Fill missing values
    for col in merged_df.columns:
        if col in ["Hours worked", "Billable hours", "Planned hours", "Revenue", "Planned revenue"]:
            merged_df[col] = merged_df[col].fillna(0)
    
    # Calculate variance metrics
    merged_df["Hours variance"] = merged_df["Hours worked"] - merged_df["Planned hours"]
    
    # Calculate percentage variance (avoiding division by zero)
    merged_df["Variance percentage"] = 0.0
    mask = merged_df["Planned hours"] > 0
    merged_df.loc[mask, "Variance percentage"] = (
        merged_df.loc[mask, "Hours variance"] / merged_df.loc[mask, "Planned hours"] * 100
    ).round(2)
    
    # Handle rate variances if available
    if "Planned rate" in merged_df.columns:
        merged_df["Planned rate"] = merged_df["Planned rate"].fillna(0)
        merged_df["Effective rate"] = merged_df["Effective rate"].fillna(0)
        
        merged_df["Rate variance"] = merged_df["Effective rate"] - merged_df["Planned rate"]
        
        # Calculate rate variance percentage (avoiding division by zero)
        merged_df["Rate variance percentage"] = 0.0
        mask = merged_df["Planned rate"] > 0
        merged_df.loc[mask, "Rate variance percentage"] = (
            merged_df.loc[mask, "Rate variance"] / merged_df.loc[mask, "Planned rate"] * 100
        ).round(2)
    
    # Handle revenue variances if available
    if "Planned revenue" in merged_df.columns:
        merged_df["Revenue variance"] = merged_df["Revenue"] - merged_df["Planned revenue"]
        
        # Calculate revenue variance percentage (avoiding division by zero)
        merged_df["Revenue variance percentage"] = 0.0
        mask = merged_df["Planned revenue"] > 0
        merged_df.loc[mask, "Revenue variance percentage"] = (
            merged_df.loc[mask, "Revenue variance"] / merged_df.loc[mask, "Planned revenue"] * 100
        ).round(2)
    
    return merged_df

def calculate_planned_summary_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate summary metrics for planned hours.
    
    Args:
        df: DataFrame with planned hours data
        
    Returns:
        Dictionary containing summary metrics
    """
    metrics = {}
    
    # Count metrics
    metrics["total_entries"] = len(df)
    metrics["unique_projects"] = df["Project number"].nunique()
    metrics["unique_people"] = df["Person"].nunique()
    
    # Sum metrics
    metrics["total_planned_hours"] = df["Planned hours"].sum()
    
    # Date metrics
    if "Date" in df.columns and not df.empty:
        metrics["first_planned_record"] = df["Date"].min()
        metrics["last_planned_record"] = df["Date"].max()
        # Calculate span in days between first and last record
        date_diff = metrics["last_planned_record"] - metrics["first_planned_record"]
        metrics["days_span"] = date_diff.days
    else:
        metrics["first_planned_record"] = None
        metrics["last_planned_record"] = None
        metrics["days_span"] = 0
    
    # Add planned rate metrics if available
    if "Planned rate" in df.columns:
        # Calculate weighted average planned rate
        total_planned_hours = df["Planned hours"].sum()
        if total_planned_hours > 0:
            metrics["average_planned_rate"] = (
                (df["Planned rate"] * df["Planned hours"]).sum() / total_planned_hours
            ).round(2)
        else:
            metrics["average_planned_rate"] = 0
            
        # Calculate total planned revenue
        metrics["total_planned_revenue"] = (df["Planned rate"] * df["Planned hours"]).sum()
    else:
        metrics["average_planned_rate"] = 0
        metrics["total_planned_revenue"] = 0
        
    return metrics

def compare_actual_vs_planned(actual_df: pd.DataFrame, planned_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compare actual vs planned hours at summary level.
    
    Args:
        actual_df: DataFrame with actual hours data
        planned_df: DataFrame with planned hours data
        
    Returns:
        Dictionary with comparison metrics
    """
    comparison = {}
    
    # Get totals
    total_actual = actual_df["Hours worked"].sum() if "Hours worked" in actual_df.columns else 0
    total_planned = planned_df["Planned hours"].sum() if "Planned hours" in planned_df.columns else 0
    
    # Calculate variance
    comparison["total_actual_hours"] = total_actual
    comparison["total_planned_hours"] = total_planned
    comparison["total_variance_hours"] = total_actual - total_planned
    
    # Calculate percentage variance
    if total_planned > 0:
        comparison["total_variance_percentage"] = (comparison["total_variance_hours"] / total_planned * 100).round(2)
    else:
        comparison["total_variance_percentage"] = 0
        
    # Count metrics
    comparison["actual_projects"] = actual_df["Project number"].nunique() if "Project number" in actual_df.columns else 0
    comparison["planned_projects"] = planned_df["Project number"].nunique() if "Project number" in planned_df.columns else 0
    
    # Projects in both datasets
    if "Project number" in actual_df.columns and "Project number" in planned_df.columns:
        actual_projects = set(actual_df["Project number"].unique())
        planned_projects = set(planned_df["Project number"].unique())
        
        comparison["common_projects"] = len(actual_projects.intersection(planned_projects))
        comparison["only_actual_projects"] = len(actual_projects - planned_projects)
        comparison["only_planned_projects"] = len(planned_projects - actual_projects)
    else:
        comparison["common_projects"] = 0
        comparison["only_actual_projects"] = 0
        comparison["only_planned_projects"] = 0
    
    # Add rate comparison if available
    if "Effective rate" in actual_df.columns and "Planned rate" in planned_df.columns:
        # Calculate weighted averages
        total_actual_billable = actual_df["Billable hours"].sum() if "Billable hours" in actual_df.columns else 0
        if total_actual_billable > 0:
            avg_effective_rate = actual_df["Revenue"].sum() / total_actual_billable
        else:
            avg_effective_rate = 0
            
        total_planned_hours = planned_df["Planned hours"].sum()
        if total_planned_hours > 0:
            avg_planned_rate = (
                (planned_df["Planned rate"] * planned_df["Planned hours"]).sum() / total_planned_hours
            )
        else:
            avg_planned_rate = 0
            
        # Store rates and variances
        comparison["avg_effective_rate"] = avg_effective_rate
        comparison["avg_planned_rate"] = avg_planned_rate
        comparison["rate_variance"] = avg_effective_rate - avg_planned_rate
        
        # Calculate percentage variance
        if avg_planned_rate > 0:
            comparison["rate_variance_percentage"] = (
                comparison["rate_variance"] / avg_planned_rate * 100
            ).round(2)
        else:
            comparison["rate_variance_percentage"] = 0
            
    return comparison
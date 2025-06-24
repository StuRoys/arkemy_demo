# processors.py
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional


def calculate_summary_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate summary metrics from the validated dataframe.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dictionary containing summary metrics
    """
    metrics = {}
    
    # Count metrics
    metrics["total_entries"] = len(df)
    metrics["unique_customers"] = df["Customer number"].nunique()
    metrics["unique_projects"] = df["Project number"].nunique()
    metrics["unique_people"] = df["Person"].nunique()
    
    # Sum metrics
    metrics["total_hours"] = df["Hours worked"].sum()
    metrics["total_billable_hours"] = df["Billable hours"].sum()
    
    # Date metrics
    if "Date" in df.columns and not df.empty:
        metrics["first_time_record"] = df["Date"].min()
        metrics["last_time_record"] = df["Date"].max()
        # Calculate years between first and last time record
        date_diff = metrics["last_time_record"] - metrics["first_time_record"]
        metrics["years_between"] = date_diff.days / 365.25  # More accurate representation of a year
    else:
        metrics["first_time_record"] = None
        metrics["last_time_record"] = None
        metrics["years_between"] = 0
    
    # Calculated metrics
    if metrics["total_hours"] > 0:
        metrics["billability_percentage"] = (metrics["total_billable_hours"] / metrics["total_hours"]) * 100
    else:
        metrics["billability_percentage"] = 0
    
    # Revenue metrics (new approach with fallback)
    if "Fee per time record" in df.columns:
        metrics["total_revenue"] = df["Fee per time record"].sum()
    elif "Hourly rate" in df.columns:
        # Fallback to old calculation
        billable_df = df.copy()
        billable_df.loc[billable_df["Billable hours"] <= 0, "Hourly rate"] = 0
        metrics["total_revenue"] = (billable_df["Billable hours"] * billable_df["Hourly rate"]).sum()
    else:
        metrics["total_revenue"] = 0
    
    # Cost metrics
    if "Cost per time record" in df.columns:
        metrics["total_cost"] = df["Cost per time record"].sum()
    else:
        metrics["total_cost"] = 0
    
    # Profit metrics
    if "Profit per time record" in df.columns:
        metrics["total_profit"] = df["Profit per time record"].sum()
    else:
        metrics["total_profit"] = 0
    
    # Calculate profit margin
    if metrics["total_revenue"] > 0:
        metrics["profit_margin_percentage"] = (metrics["total_profit"] / metrics["total_revenue"]) * 100
    else:
        metrics["profit_margin_percentage"] = 0
    
    # Revenue-based calculations
    if metrics["unique_projects"] > 0:
        metrics["avg_revenue_per_project"] = metrics["total_revenue"] / metrics["unique_projects"]
    else:
        metrics["avg_revenue_per_project"] = 0
        
    # Calculate billable hourly rate (average rate for billable hours only)
    if metrics["total_billable_hours"] > 0:
        metrics["Billable rate"] = metrics["total_revenue"] / metrics["total_billable_hours"]
    else:
        metrics["Billable rate"] = 0
        
    # Calculate effective hourly rate (revenue divided by all hours)
    if metrics["total_hours"] > 0:
        metrics["Effective rate"] = metrics["total_revenue"] / metrics["total_hours"]
    else:
        metrics["Effective rate"] = 0
    
    return metrics


def aggregate_by_time(df: pd.DataFrame, time_period: str = 'day') -> pd.DataFrame:
    """
    Aggregate data by specified time period.
    
    Args:
        df: Validated and transformed dataframe
        time_period: Time period to aggregate by ('day', 'week', 'month', 'year')
        
    Returns:
        Aggregated dataframe
    """
    # Ensure Date column exists and is datetime type
    if "Date" not in df.columns:
        raise ValueError("Date column not found in dataframe")
    
    # Create date categories based on specified time period
    if time_period == 'day':
        date_groups = df["Date"]
    elif time_period == 'week':
        date_groups = df["Date"].dt.isocalendar().week
    elif time_period == 'month':
        date_groups = df["Date"].dt.to_period('M')
    elif time_period == 'year':
        date_groups = df["Date"].dt.year
    else:
        raise ValueError(f"Invalid time period: {time_period}")
    
    # Aggregate metrics by time period
    agg_df = df.groupby(date_groups).agg({
        "Hours worked": "sum",
        "Billable hours": "sum"
    }).reset_index()
    
    # Add calculated columns
    agg_df["Non-billable hours"] = agg_df["Hours worked"] - agg_df["Billable hours"]
    agg_df["Billability %"] = (agg_df["Billable hours"] / agg_df["Hours worked"] * 100).round(2)
    
    # Add revenue (new approach with fallback)
    if "Fee per time record" in df.columns:
        revenue_by_date = df.groupby(date_groups)["Fee per time record"].sum().reset_index(name="Revenue")
        agg_df = pd.merge(agg_df, revenue_by_date, on="Date")
    elif "Hourly rate" in df.columns:
        # Fallback to old calculation
        revenue_by_date = df.groupby(date_groups).apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")
        agg_df = pd.merge(agg_df, revenue_by_date, on="Date")
    else:
        agg_df["Revenue"] = 0
    
    # Add cost
    if "Cost per time record" in df.columns:
        cost_by_date = df.groupby(date_groups)["Cost per time record"].sum().reset_index(name="Total cost")
        agg_df = pd.merge(agg_df, cost_by_date, on="Date")
    else:
        agg_df["Total cost"] = 0
    
    # Add profit
    if "Profit per time record" in df.columns:
        profit_by_date = df.groupby(date_groups)["Profit per time record"].sum().reset_index(name="Total profit")
        agg_df = pd.merge(agg_df, profit_by_date, on="Date")
    else:
        agg_df["Total profit"] = 0
    
    # Calculate rates
    agg_df["Billable rate"] = 0  # Default
    mask = agg_df["Billable hours"] > 0
    agg_df.loc[mask, "Billable rate"] = agg_df.loc[mask, "Revenue"] / agg_df.loc[mask, "Billable hours"]
    
    agg_df["Effective rate"] = 0  # Default
    mask = agg_df["Hours worked"] > 0
    agg_df.loc[mask, "Effective rate"] = agg_df.loc[mask, "Revenue"] / agg_df.loc[mask, "Hours worked"]
    
    # Calculate profit margin
    agg_df["Profit margin %"] = 0.0
    mask = agg_df["Revenue"] > 0
    agg_df.loc[mask, "Profit margin %"] = (agg_df.loc[mask, "Total profit"] / agg_df.loc[mask, "Revenue"] * 100).round(2)
    
    return agg_df

def aggregate_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by year.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with yearly aggregations
    """
    # Ensure Date column exists and is datetime type
    if "Date" not in df.columns:
        raise ValueError("Date column not found in dataframe")
    
    # Extract year from the Date column
    year_df = df.copy()
    year_df['Year'] = year_df['Date'].dt.year
    
    # Aggregate metrics by year
    year_agg = year_df.groupby("Year").agg({
        "Hours worked": "sum",
        "Billable hours": "sum",
        "Project number": "nunique",
        "Customer number": "nunique",
        "Person": "nunique"
    }).reset_index()
    
    # Add calculated columns
    year_agg["Non-billable hours"] = year_agg["Hours worked"] - year_agg["Billable hours"]
    year_agg["Billability %"] = (year_agg["Billable hours"] / year_agg["Hours worked"] * 100).round(2)
    year_agg.rename(columns={
        "Project number": "Number of projects",
        "Customer number": "Number of customers",
        "Person": "Number of people"
    }, inplace=True)
    
    # Add revenue (new approach with fallback)
    if "Fee per time record" in df.columns:
        revenue_by_year = year_df.groupby("Year")["Fee per time record"].sum().reset_index(name="Revenue")
        year_agg = pd.merge(year_agg, revenue_by_year, on="Year")
    elif "Hourly rate" in df.columns:
        # Fallback to old calculation
        revenue_by_year = year_df.groupby("Year").apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")
        year_agg = pd.merge(year_agg, revenue_by_year, on="Year")
    else:
        year_agg["Revenue"] = 0
    
    # Add cost
    if "Cost per time record" in df.columns:
        cost_by_year = year_df.groupby("Year")["Cost per time record"].sum().reset_index(name="Total cost")
        year_agg = pd.merge(year_agg, cost_by_year, on="Year")
    else:
        year_agg["Total cost"] = 0
    
    # Add profit
    if "Profit per time record" in df.columns:
        profit_by_year = year_df.groupby("Year")["Profit per time record"].sum().reset_index(name="Total profit")
        year_agg = pd.merge(year_agg, profit_by_year, on="Year")
    else:
        year_agg["Total profit"] = 0
    
    # Calculate rates
    year_agg["Billable rate"] = 0  # Default
    mask = year_agg["Billable hours"] > 0
    year_agg.loc[mask, "Billable rate"] = year_agg.loc[mask, "Revenue"] / year_agg.loc[mask, "Billable hours"]
    
    year_agg["Effective rate"] = 0  # Default
    mask = year_agg["Hours worked"] > 0
    year_agg.loc[mask, "Effective rate"] = year_agg.loc[mask, "Revenue"] / year_agg.loc[mask, "Hours worked"]
    
    # Calculate profit margin
    year_agg["Profit margin %"] = 0.0
    mask = year_agg["Revenue"] > 0
    year_agg.loc[mask, "Profit margin %"] = (year_agg.loc[mask, "Total profit"] / year_agg.loc[mask, "Revenue"] * 100).round(2)
    
    return year_agg


def aggregate_by_customer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by customer.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with customer aggregations
    """
    customer_agg = df.groupby(["Customer number", "Customer name"]).agg({
        "Hours worked": "sum",
        "Billable hours": "sum",
        "Project number": "nunique"
    }).reset_index()
    
    customer_agg["Non-billable hours"] = customer_agg["Hours worked"] - customer_agg["Billable hours"]
    customer_agg["Billability %"] = (customer_agg["Billable hours"] / customer_agg["Hours worked"] * 100).round(2)
    customer_agg.rename(columns={"Project number": "Number of projects"}, inplace=True)
    
    # Add revenue (new approach with fallback)
    if "Fee per time record" in df.columns:
        revenue_by_customer = df.groupby("Customer number")["Fee per time record"].sum().reset_index(name="Revenue")
        customer_agg = pd.merge(customer_agg, revenue_by_customer, on="Customer number")
    elif "Hourly rate" in df.columns:
        # Fallback to old calculation
        revenue_by_customer = df.groupby("Customer number").apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")
        customer_agg = pd.merge(customer_agg, revenue_by_customer, on="Customer number")
    else:
        customer_agg["Revenue"] = 0
    
    # Add cost
    if "Cost per time record" in df.columns:
        cost_by_customer = df.groupby("Customer number")["Cost per time record"].sum().reset_index(name="Total cost")
        customer_agg = pd.merge(customer_agg, cost_by_customer, on="Customer number")
    else:
        customer_agg["Total cost"] = 0
    
    # Add profit
    if "Profit per time record" in df.columns:
        profit_by_customer = df.groupby("Customer number")["Profit per time record"].sum().reset_index(name="Total profit")
        customer_agg = pd.merge(customer_agg, profit_by_customer, on="Customer number")
    else:
        customer_agg["Total profit"] = 0
    
    # Calculate rates
    customer_agg["Billable rate"] = 0  # Default
    mask = customer_agg["Billable hours"] > 0
    customer_agg.loc[mask, "Billable rate"] = customer_agg.loc[mask, "Revenue"] / customer_agg.loc[mask, "Billable hours"]
    
    customer_agg["Effective rate"] = 0  # Default
    mask = customer_agg["Hours worked"] > 0
    customer_agg.loc[mask, "Effective rate"] = customer_agg.loc[mask, "Revenue"] / customer_agg.loc[mask, "Hours worked"]
    
    # Calculate profit margin
    customer_agg["Profit margin %"] = 0.0
    mask = customer_agg["Revenue"] > 0
    customer_agg.loc[mask, "Profit margin %"] = (customer_agg.loc[mask, "Total profit"] / customer_agg.loc[mask, "Revenue"] * 100).round(2)
    
    return customer_agg


def aggregate_by_project(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by project.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with project aggregations
    """
    # Check if Project type column exists
    if "Project type" in df.columns:
        # Use all three columns if Project type exists
        project_agg = df.groupby(["Project number", "Project", "Project type"]).agg({
            "Hours worked": "sum",
            "Billable hours": "sum",
            "Person": "nunique"
        }).reset_index()
    else:
        # Only use Project number and Project columns if Project type doesn't exist
        project_agg = df.groupby(["Project number", "Project"]).agg({
            "Hours worked": "sum",
            "Billable hours": "sum",
            "Person": "nunique"
        }).reset_index()
        # Add an empty Project type column to maintain expected schema
        project_agg["Project type"] = "Unknown"
    
    project_agg["Non-billable hours"] = project_agg["Hours worked"] - project_agg["Billable hours"]
    project_agg["Billability %"] = (project_agg["Billable hours"] / project_agg["Hours worked"] * 100).round(2)
    project_agg.rename(columns={"Person": "Number of people"}, inplace=True)
    
    # Add revenue (new approach with fallback)
    if "Fee per time record" in df.columns:
        revenue_by_project = df.groupby("Project number")["Fee per time record"].sum().reset_index(name="Revenue")
        project_agg = pd.merge(project_agg, revenue_by_project, on="Project number")
    elif "Hourly rate" in df.columns:
        # Fallback to old calculation
        revenue_by_project = df.groupby("Project number").apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")
        project_agg = pd.merge(project_agg, revenue_by_project, on="Project number")
    else:
        project_agg["Revenue"] = 0
    
    # Add cost
    if "Cost per time record" in df.columns:
        cost_by_project = df.groupby("Project number")["Cost per time record"].sum().reset_index(name="Total cost")
        project_agg = pd.merge(project_agg, cost_by_project, on="Project number")
    else:
        project_agg["Total cost"] = 0
    
    # Add profit
    if "Profit per time record" in df.columns:
        profit_by_project = df.groupby("Project number")["Profit per time record"].sum().reset_index(name="Total profit")
        project_agg = pd.merge(project_agg, profit_by_project, on="Project number")
    else:
        project_agg["Total profit"] = 0
    
    # Calculate rates
    project_agg["Billable rate"] = 0  # Default
    mask = project_agg["Billable hours"] > 0
    project_agg.loc[mask, "Billable rate"] = project_agg.loc[mask, "Revenue"] / project_agg.loc[mask, "Billable hours"]
    
    project_agg["Effective rate"] = 0  # Default
    mask = project_agg["Hours worked"] > 0
    project_agg.loc[mask, "Effective rate"] = project_agg.loc[mask, "Revenue"] / project_agg.loc[mask, "Hours worked"]
    
    # Calculate profit margin
    project_agg["Profit margin %"] = 0.0
    mask = project_agg["Revenue"] > 0
    project_agg.loc[mask, "Profit margin %"] = (project_agg.loc[mask, "Total profit"] / project_agg.loc[mask, "Revenue"] * 100).round(2)
    
    return project_agg


def aggregate_by_project_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by project type.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with project type aggregations
    """
    project_type_agg = df.groupby(["Project type"]).agg({
        "Hours worked": "sum",
        "Billable hours": "sum",
        "Project number": "nunique",
        "Person": "nunique"
    }).reset_index()
    
    project_type_agg["Non-billable hours"] = project_type_agg["Hours worked"] - project_type_agg["Billable hours"]
    project_type_agg["Billability %"] = (project_type_agg["Billable hours"] / project_type_agg["Hours worked"] * 100).round(2)
    project_type_agg.rename(columns={
        "Project number": "Number of projects",
        "Person": "Number of people"
    }, inplace=True)
    
    # Add revenue (new approach with fallback)
    if "Fee per time record" in df.columns:
        revenue_by_type = df.groupby("Project type")["Fee per time record"].sum().reset_index(name="Revenue")
        project_type_agg = pd.merge(project_type_agg, revenue_by_type, on="Project type")
    elif "Hourly rate" in df.columns:
        # Fallback to old calculation
        revenue_by_type = df.groupby("Project type").apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")
        project_type_agg = pd.merge(project_type_agg, revenue_by_type, on="Project type")
    else:
        project_type_agg["Revenue"] = 0
    
    # Add cost
    if "Cost per time record" in df.columns:
        cost_by_type = df.groupby("Project type")["Cost per time record"].sum().reset_index(name="Total cost")
        project_type_agg = pd.merge(project_type_agg, cost_by_type, on="Project type")
    else:
        project_type_agg["Total cost"] = 0
    
    # Add profit
    if "Profit per time record" in df.columns:
        profit_by_type = df.groupby("Project type")["Profit per time record"].sum().reset_index(name="Total profit")
        project_type_agg = pd.merge(project_type_agg, profit_by_type, on="Project type")
    else:
        project_type_agg["Total profit"] = 0
    
    # Calculate rates
    project_type_agg["Billable rate"] = 0  # Default
    mask = project_type_agg["Billable hours"] > 0
    project_type_agg.loc[mask, "Billable rate"] = project_type_agg.loc[mask, "Revenue"] / project_type_agg.loc[mask, "Billable hours"]
    
    project_type_agg["Effective rate"] = 0  # Default
    mask = project_type_agg["Hours worked"] > 0
    project_type_agg.loc[mask, "Effective rate"] = project_type_agg.loc[mask, "Revenue"] / project_type_agg.loc[mask, "Hours worked"]
    
    # Calculate profit margin
    project_type_agg["Profit margin %"] = 0.0
    mask = project_type_agg["Revenue"] > 0
    project_type_agg.loc[mask, "Profit margin %"] = (project_type_agg.loc[mask, "Total profit"] / project_type_agg.loc[mask, "Revenue"] * 100).round(2)
    
    return project_type_agg


def aggregate_by_phase(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by project phase.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with phase aggregations
    """
    phase_agg = df.groupby(["Phase"]).agg({
        "Hours worked": "sum",
        "Billable hours": "sum",
        "Project number": "nunique",
        "Person": "nunique"
    }).reset_index()
    
    phase_agg["Non-billable hours"] = phase_agg["Hours worked"] - phase_agg["Billable hours"]
    phase_agg["Billability %"] = (phase_agg["Billable hours"] / phase_agg["Hours worked"] * 100).round(2)
    phase_agg.rename(columns={
        "Project number": "Number of projects",
        "Person": "Number of people"
    }, inplace=True)
    
    # Add revenue (new approach with fallback)
    if "Fee per time record" in df.columns:
        revenue_by_phase = df.groupby("Phase")["Fee per time record"].sum().reset_index(name="Revenue")
        phase_agg = pd.merge(phase_agg, revenue_by_phase, on="Phase")
    elif "Hourly rate" in df.columns:
        # Fallback to old calculation
        revenue_by_phase = df.groupby("Phase").apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")
        phase_agg = pd.merge(phase_agg, revenue_by_phase, on="Phase")
    else:
        phase_agg["Revenue"] = 0
    
    # Add cost
    if "Cost per time record" in df.columns:
        cost_by_phase = df.groupby("Phase")["Cost per time record"].sum().reset_index(name="Total cost")
        phase_agg = pd.merge(phase_agg, cost_by_phase, on="Phase")
    else:
        phase_agg["Total cost"] = 0
    
    # Add profit
    if "Profit per time record" in df.columns:
        profit_by_phase = df.groupby("Phase")["Profit per time record"].sum().reset_index(name="Total profit")
        phase_agg = pd.merge(phase_agg, profit_by_phase, on="Phase")
    else:
        phase_agg["Total profit"] = 0
    
    # Calculate rates
    phase_agg["Billable rate"] = 0  # Default
    mask = phase_agg["Billable hours"] > 0
    phase_agg.loc[mask, "Billable rate"] = phase_agg.loc[mask, "Revenue"] / phase_agg.loc[mask, "Billable hours"]
    
    phase_agg["Effective rate"] = 0  # Default
    mask = phase_agg["Hours worked"] > 0
    phase_agg.loc[mask, "Effective rate"] = phase_agg.loc[mask, "Revenue"] / phase_agg.loc[mask, "Hours worked"]
    
    # Calculate profit margin
    phase_agg["Profit margin %"] = 0.0
    mask = phase_agg["Revenue"] > 0
    phase_agg.loc[mask, "Profit margin %"] = (phase_agg.loc[mask, "Total profit"] / phase_agg.loc[mask, "Revenue"] * 100).round(2)
    
    return phase_agg

def aggregate_by_price_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by price model.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with price model aggregations
    """
    price_model_agg = df.groupby(["Price model"]).agg({
        "Hours worked": "sum",
        "Billable hours": "sum",
        "Project number": "nunique",
        "Person": "nunique"
    }).reset_index()
    
    price_model_agg["Non-billable hours"] = price_model_agg["Hours worked"] - price_model_agg["Billable hours"]
    price_model_agg["Billability %"] = (price_model_agg["Billable hours"] / price_model_agg["Hours worked"] * 100).round(2)
    price_model_agg.rename(columns={
        "Project number": "Number of projects",
        "Person": "Number of people"
    }, inplace=True)
    
    # Add revenue (new approach with fallback)
    if "Fee per time record" in df.columns:
        revenue_by_price_model = df.groupby("Price model")["Fee per time record"].sum().reset_index(name="Revenue")
        price_model_agg = pd.merge(price_model_agg, revenue_by_price_model, on="Price model")
    elif "Hourly rate" in df.columns:
        # Fallback to old calculation
        revenue_by_price_model = df.groupby("Price model").apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")
        price_model_agg = pd.merge(price_model_agg, revenue_by_price_model, on="Price model")
    else:
        price_model_agg["Revenue"] = 0
    
    # Add cost
    if "Cost per time record" in df.columns:
        cost_by_price_model = df.groupby("Price model")["Cost per time record"].sum().reset_index(name="Total cost")
        price_model_agg = pd.merge(price_model_agg, cost_by_price_model, on="Price model")
    else:
        price_model_agg["Total cost"] = 0
    
    # Add profit
    if "Profit per time record" in df.columns:
        profit_by_price_model = df.groupby("Price model")["Profit per time record"].sum().reset_index(name="Total profit")
        price_model_agg = pd.merge(price_model_agg, profit_by_price_model, on="Price model")
    else:
        price_model_agg["Total profit"] = 0
    
    # Calculate rates
    price_model_agg["Billable rate"] = 0  # Default
    mask = price_model_agg["Billable hours"] > 0
    price_model_agg.loc[mask, "Billable rate"] = price_model_agg.loc[mask, "Revenue"] / price_model_agg.loc[mask, "Billable hours"]
    
    price_model_agg["Effective rate"] = 0  # Default
    mask = price_model_agg["Hours worked"] > 0
    price_model_agg.loc[mask, "Effective rate"] = price_model_agg.loc[mask, "Revenue"] / price_model_agg.loc[mask, "Hours worked"]
    
    # Calculate profit margin
    price_model_agg["Profit margin %"] = 0.0
    mask = price_model_agg["Revenue"] > 0
    price_model_agg.loc[mask, "Profit margin %"] = (price_model_agg.loc[mask, "Total profit"] / price_model_agg.loc[mask, "Revenue"] * 100).round(2)
    
    return price_model_agg


def aggregate_by_activity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by activity.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with activity aggregations
    """
    activity_agg = df.groupby(["Activity"]).agg({
        "Hours worked": "sum",
        "Billable hours": "sum",
        "Project number": "nunique",
        "Person": "nunique"
    }).reset_index()
    
    activity_agg["Non-billable hours"] = activity_agg["Hours worked"] - activity_agg["Billable hours"]
    activity_agg["Billability %"] = (activity_agg["Billable hours"] / activity_agg["Hours worked"] * 100).round(2)
    activity_agg.rename(columns={
        "Project number": "Number of projects",
        "Person": "Number of people"
    }, inplace=True)
    
    # Add revenue (new approach with fallback)
    if "Fee per time record" in df.columns:
        revenue_by_activity = df.groupby("Activity")["Fee per time record"].sum().reset_index(name="Revenue")
        activity_agg = pd.merge(activity_agg, revenue_by_activity, on="Activity")
    elif "Hourly rate" in df.columns:
        # Fallback to old calculation
        revenue_by_activity = df.groupby("Activity").apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")
        activity_agg = pd.merge(activity_agg, revenue_by_activity, on="Activity")
    else:
        activity_agg["Revenue"] = 0
    
    # Add cost
    if "Cost per time record" in df.columns:
        cost_by_activity = df.groupby("Activity")["Cost per time record"].sum().reset_index(name="Total cost")
        activity_agg = pd.merge(activity_agg, cost_by_activity, on="Activity")
    else:
        activity_agg["Total cost"] = 0
    
    # Add profit
    if "Profit per time record" in df.columns:
        profit_by_activity = df.groupby("Activity")["Profit per time record"].sum().reset_index(name="Total profit")
        activity_agg = pd.merge(activity_agg, profit_by_activity, on="Activity")
    else:
        activity_agg["Total profit"] = 0
    
    # Calculate rates
    activity_agg["Billable rate"] = 0  # Default
    mask = activity_agg["Billable hours"] > 0
    activity_agg.loc[mask, "Billable rate"] = activity_agg.loc[mask, "Revenue"] / activity_agg.loc[mask, "Billable hours"]
    
    activity_agg["Effective rate"] = 0  # Default
    mask = activity_agg["Hours worked"] > 0
    activity_agg.loc[mask, "Effective rate"] = activity_agg.loc[mask, "Revenue"] / activity_agg.loc[mask, "Hours worked"]
    
    # Calculate profit margin
    activity_agg["Profit margin %"] = 0.0
    mask = activity_agg["Revenue"] > 0
    activity_agg.loc[mask, "Profit margin %"] = (activity_agg.loc[mask, "Total profit"] / activity_agg.loc[mask, "Revenue"] * 100).round(2)
    
    return activity_agg


def aggregate_by_person(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by person.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with person aggregations
    """
    person_agg = df.groupby(["Person"]).agg({
        "Hours worked": "sum",
        "Billable hours": "sum",
        "Project number": "nunique"
    }).reset_index()
    
    person_agg["Non-billable hours"] = person_agg["Hours worked"] - person_agg["Billable hours"]
    person_agg["Billability %"] = (person_agg["Billable hours"] / person_agg["Hours worked"] * 100).round(2)
    person_agg.rename(columns={"Project number": "Number of projects"}, inplace=True)
    
    # Add revenue (new approach with fallback)
    if "Fee per time record" in df.columns:
        revenue_by_person = df.groupby("Person")["Fee per time record"].sum().reset_index(name="Revenue")
        person_agg = pd.merge(person_agg, revenue_by_person, on="Person")
    elif "Hourly rate" in df.columns:
        # Fallback to old calculation
        revenue_by_person = df.groupby("Person").apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")
        person_agg = pd.merge(person_agg, revenue_by_person, on="Person")
    else:
        person_agg["Revenue"] = 0
    
    # Add cost
    if "Cost per time record" in df.columns:
        cost_by_person = df.groupby("Person")["Cost per time record"].sum().reset_index(name="Total cost")
        person_agg = pd.merge(person_agg, cost_by_person, on="Person")
    else:
        person_agg["Total cost"] = 0
    
    # Add profit
    if "Profit per time record" in df.columns:
        profit_by_person = df.groupby("Person")["Profit per time record"].sum().reset_index(name="Total profit")
        person_agg = pd.merge(person_agg, profit_by_person, on="Person")
    else:
        person_agg["Total profit"] = 0
    
    # Calculate rates
    person_agg["Billable rate"] = 0  # Default
    mask = person_agg["Billable hours"] > 0
    person_agg.loc[mask, "Billable rate"] = person_agg.loc[mask, "Revenue"] / person_agg.loc[mask, "Billable hours"]
    
    person_agg["Effective rate"] = 0  # Default
    mask = person_agg["Hours worked"] > 0
    person_agg.loc[mask, "Effective rate"] = person_agg.loc[mask, "Revenue"] / person_agg.loc[mask, "Hours worked"]
    
    # Calculate profit margin
    person_agg["Profit margin %"] = 0.0
    mask = person_agg["Revenue"] > 0
    person_agg.loc[mask, "Profit margin %"] = (person_agg.loc[mask, "Total profit"] / person_agg.loc[mask, "Revenue"] * 100).round(2)
    
    return person_agg


def find_top_items(df: pd.DataFrame, category: str, metric: str, top_n: int = 5) -> pd.DataFrame:
    """
    Find top items by a specific metric.
    
    Args:
        df: Validated and transformed dataframe
        category: Category to group by ('customer', 'project', 'person')
        metric: Metric to sort by ('hours', 'billable', 'revenue', 'cost', 'profit')
        top_n: Number of top items to return
        
    Returns:
        Dataframe with top items
    """
    if category == 'customer':
        group_cols = ["Customer number", "Customer name"]
    elif category == 'project':
        group_cols = ["Project number", "Project"]
    elif category == 'person':
        group_cols = ["Person"]
    else:
        raise ValueError(f"Invalid category: {category}")
    
    # Calculate metrics for each group
    result = df.groupby(group_cols).agg({
        "Hours worked": "sum",
        "Billable hours": "sum"
    }).reset_index()
    
    # Add revenue (new approach with fallback)
    if "Fee per time record" in df.columns:
        revenue_by_group = df.groupby(group_cols[0])["Fee per time record"].sum().reset_index(name="Revenue")
        result = pd.merge(result, revenue_by_group, on=group_cols[0])
    elif "Hourly rate" in df.columns:
        # Fallback to old calculation
        revenue_by_group = df.groupby(group_cols[0]).apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")
        result = pd.merge(result, revenue_by_group, on=group_cols[0])
    else:
        result["Revenue"] = 0
    
    # Add cost
    if "Cost per time record" in df.columns:
        cost_by_group = df.groupby(group_cols[0])["Cost per time record"].sum().reset_index(name="Total cost")
        result = pd.merge(result, cost_by_group, on=group_cols[0])
    else:
        result["Total cost"] = 0
    
    # Add profit
    if "Profit per time record" in df.columns:
        profit_by_group = df.groupby(group_cols[0])["Profit per time record"].sum().reset_index(name="Total profit")
        result = pd.merge(result, profit_by_group, on=group_cols[0])
    else:
        result["Total profit"] = 0
    
    # Calculate rates
    result["Billable rate"] = 0  # Default
    mask = result["Billable hours"] > 0
    result.loc[mask, "Billable rate"] = result.loc[mask, "Revenue"] / result.loc[mask, "Billable hours"]
    
    result["Effective rate"] = 0  # Default
    mask = result["Hours worked"] > 0
    result.loc[mask, "Effective rate"] = result.loc[mask, "Revenue"] / result.loc[mask, "Hours worked"]
    
    # Determine sort column
    if metric == 'hours':
        sort_col = "Hours worked"
    elif metric == 'billable':
        sort_col = "Billable hours"
    elif metric == 'revenue':
        sort_col = "Revenue"
    elif metric == 'cost':
        sort_col = "Total cost"
    elif metric == 'profit':
        sort_col = "Total profit"
    else:
        sort_col = "Hours worked"  # Default
    
    return result.sort_values(sort_col, ascending=False).head(top_n)


def calculate_utilization_rates(df: pd.DataFrame, work_hours_per_day: float = 8.0) -> pd.DataFrame:
    """
    Calculate utilization rates for each person.
    
    Args:
        df: Validated and transformed dataframe
        work_hours_per_day: Standard work hours per day
        
    Returns:
        Dataframe with utilization rates
    """
    # Group by person and date to get hours per person per day
    person_daily = df.groupby(["Person", "Date"])["Hours worked"].sum().reset_index()
    
    # Calculate days worked per person
    days_worked = person_daily.groupby("Person")["Date"].nunique()
    
    # Calculate total possible work hours (days worked * work hours per day)
    total_possible_hours = days_worked * work_hours_per_day
    
    # Calculate actual hours worked per person
    hours_worked = df.groupby("Person")["Hours worked"].sum()
    
    # Calculate billable hours per person
    billable_hours = df.groupby("Person")["Billable hours"].sum()
    
    # Combine into a single dataframe
    util_df = pd.DataFrame({
        "Days worked": days_worked,
        "Potential hours": total_possible_hours,
        "Actual hours": hours_worked,
        "Billable hours": billable_hours
    }).reset_index()
    
    # Calculate utilization rates
    util_df["Utilization %"] = (util_df["Actual hours"] / util_df["Potential hours"] * 100).round(2)
    util_df["Billable utilization %"] = (util_df["Billable hours"] / util_df["Potential hours"] * 100).round(2)
    
    # Add revenue (new approach with fallback)
    if "Fee per time record" in df.columns:
        revenue_by_person = df.groupby("Person")["Fee per time record"].sum().reset_index(name="Revenue")
        util_df = pd.merge(util_df, revenue_by_person, on="Person")
    elif "Hourly rate" in df.columns:
        # Fallback to old calculation
        revenue_by_person = df.groupby("Person").apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")
        util_df = pd.merge(util_df, revenue_by_person, on="Person")
    else:
        util_df["Revenue"] = 0
    
    # Add cost
    if "Cost per time record" in df.columns:
        cost_by_person = df.groupby("Person")["Cost per time record"].sum().reset_index(name="Total cost")
        util_df = pd.merge(util_df, cost_by_person, on="Person")
    else:
        util_df["Total cost"] = 0
    
    # Add profit
    if "Profit per time record" in df.columns:
        profit_by_person = df.groupby("Person")["Profit per time record"].sum().reset_index(name="Total profit")
        util_df = pd.merge(util_df, profit_by_person, on="Person")
    else:
        util_df["Total profit"] = 0
    
    # Calculate rates
    util_df["Billable rate"] = 0  # Default
    mask = util_df["Billable hours"] > 0
    util_df.loc[mask, "Billable rate"] = util_df.loc[mask, "Revenue"] / util_df.loc[mask, "Billable hours"]
    
    util_df["Effective rate"] = 0  # Default
    mask = util_df["Actual hours"] > 0
    util_df.loc[mask, "Effective rate"] = util_df.loc[mask, "Revenue"] / util_df.loc[mask, "Actual hours"]
    
    return util_df

def aggregate_by_month_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by month and year.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with month-year aggregations
    """
    # Ensure Date column exists and is datetime type
    if "Date" not in df.columns:
        raise ValueError("Date column not found in dataframe")
    
    # Create month and year columns
    month_year_df = df.copy()
    month_year_df['Year'] = month_year_df['Date'].dt.year
    month_year_df['Month'] = month_year_df['Date'].dt.month
    
    # Create month name for better display
    month_names = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    month_year_df['Month name'] = month_year_df['Month'].map(month_names)
    
    # Aggregate metrics by month and year
    month_year_agg = month_year_df.groupby(['Year', 'Month', 'Month name']).agg({
        "Hours worked": "sum",
        "Billable hours": "sum",
        "Project number": "nunique",
        "Customer number": "nunique",
        "Person": "nunique"
    }).reset_index()
    
    # Add calculated columns
    month_year_agg["Non-billable hours"] = month_year_agg["Hours worked"] - month_year_agg["Billable hours"]
    month_year_agg["Billability %"] = (month_year_agg["Billable hours"] / month_year_agg["Hours worked"] * 100).round(2)
    month_year_agg.rename(columns={
        "Project number": "Number of projects",
        "Customer number": "Number of customers",
        "Person": "Number of people"
    }, inplace=True)
    
    # Add revenue (new approach with fallback)
    if "Fee per time record" in df.columns:
        revenue_by_month_year = month_year_df.groupby(['Year', 'Month'])["Fee per time record"].sum().reset_index(name="Revenue")
        month_year_agg = pd.merge(month_year_agg, revenue_by_month_year, on=['Year', 'Month'])
    elif "Hourly rate" in df.columns:
        # Fallback to old calculation
        revenue_by_month_year = month_year_df.groupby(['Year', 'Month']).apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")
        month_year_agg = pd.merge(month_year_agg, revenue_by_month_year, on=['Year', 'Month'])
    else:
        month_year_agg["Revenue"] = 0
    
    # Add cost
    if "Cost per time record" in df.columns:
        cost_by_month_year = month_year_df.groupby(['Year', 'Month'])["Cost per time record"].sum().reset_index(name="Total cost")
        month_year_agg = pd.merge(month_year_agg, cost_by_month_year, on=['Year', 'Month'])
    else:
        month_year_agg["Total cost"] = 0
    
    # Add profit
    if "Profit per time record" in df.columns:
        profit_by_month_year = month_year_df.groupby(['Year', 'Month'])["Profit per time record"].sum().reset_index(name="Total profit")
        month_year_agg = pd.merge(month_year_agg, profit_by_month_year, on=['Year', 'Month'])
    else:
        month_year_agg["Total profit"] = 0
    
    # Calculate rates
    month_year_agg["Billable rate"] = 0  # Default
    mask = month_year_agg["Billable hours"] > 0
    month_year_agg.loc[mask, "Billable rate"] = month_year_agg.loc[mask, "Revenue"] / month_year_agg.loc[mask, "Billable hours"]
    
    month_year_agg["Effective rate"] = 0  # Default
    mask = month_year_agg["Hours worked"] > 0
    month_year_agg.loc[mask, "Effective rate"] = month_year_agg.loc[mask, "Revenue"] / month_year_agg.loc[mask, "Hours worked"]
    
    # Calculate profit margin
    month_year_agg["Profit margin %"] = 0.0
    mask = month_year_agg["Revenue"] > 0
    month_year_agg.loc[mask, "Profit margin %"] = (month_year_agg.loc[mask, "Total profit"] / month_year_agg.loc[mask, "Revenue"] * 100).round(2)
    
    return month_year_agg

def aggregate_customer_project_hierarchy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by customer and project to create a hierarchical structure
    for treemap visualization.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with hierarchical customer-project aggregations
    """
    # Create a copy of the dataframe to avoid modifying the original
    hierarchy_df = df.copy()
    
    # First, get customer-level aggregations
    customer_agg = aggregate_by_customer(df)
    customer_agg['Level'] = 'Customer'  # Add level identifier
    
    # Next, get project-level aggregations with customer information
    project_with_customer = df.groupby([
        "Customer number", "Customer name", "Project number", "Project"
    ]).agg({
        "Hours worked": "sum",
        "Billable hours": "sum",
        "Person": "nunique"
    }).reset_index()
    
    # Add calculated metrics for projects
    project_with_customer["Non-billable hours"] = (
        project_with_customer["Hours worked"] - project_with_customer["Billable hours"]
    )
    project_with_customer["Billability %"] = (
        project_with_customer["Billable hours"] / project_with_customer["Hours worked"] * 100
    ).round(2)
    project_with_customer.rename(columns={"Person": "Number of people"}, inplace=True)
    project_with_customer['Level'] = 'Project'  # Add level identifier
    
    # Add revenue (new approach with fallback)
    if "Fee per time record" in df.columns:
        revenue_by_project = df.groupby(["Customer number", "Project number"])["Fee per time record"].sum().reset_index(name="Revenue")
        project_with_customer = pd.merge(
            project_with_customer, 
            revenue_by_project, 
            on=["Customer number", "Project number"]
        )
    elif "Hourly rate" in df.columns:
        # Fallback to old calculation
        revenue_by_project = df.groupby(["Customer number", "Project number"]).apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")
        project_with_customer = pd.merge(
            project_with_customer, 
            revenue_by_project, 
            on=["Customer number", "Project number"]
        )
    else:
        project_with_customer["Revenue"] = 0
    
    # Add cost
    if "Cost per time record" in df.columns:
        cost_by_project = df.groupby(["Customer number", "Project number"])["Cost per time record"].sum().reset_index(name="Total cost")
        project_with_customer = pd.merge(
            project_with_customer, 
            cost_by_project, 
            on=["Customer number", "Project number"]
        )
    else:
        project_with_customer["Total cost"] = 0
    
    # Add profit
    if "Profit per time record" in df.columns:
        profit_by_project = df.groupby(["Customer number", "Project number"])["Profit per time record"].sum().reset_index(name="Total profit")
        project_with_customer = pd.merge(
            project_with_customer, 
            profit_by_project, 
            on=["Customer number", "Project number"]
        )
    else:
        project_with_customer["Total profit"] = 0
    
    # Calculate rates for projects
    project_with_customer["Billable rate"] = 0  # Default
    mask = project_with_customer["Billable hours"] > 0
    project_with_customer.loc[mask, "Billable rate"] = (
        project_with_customer.loc[mask, "Revenue"] / 
        project_with_customer.loc[mask, "Billable hours"]
    )
    
    project_with_customer["Effective rate"] = 0  # Default
    mask = project_with_customer["Hours worked"] > 0
    project_with_customer.loc[mask, "Effective rate"] = (
        project_with_customer.loc[mask, "Revenue"] / 
        project_with_customer.loc[mask, "Hours worked"]
    )
    
    # Calculate profit margin for projects
    project_with_customer["Profit margin %"] = 0.0
    mask = project_with_customer["Revenue"] > 0
    project_with_customer.loc[mask, "Profit margin %"] = (
        project_with_customer.loc[mask, "Total profit"] / 
        project_with_customer.loc[mask, "Revenue"] * 100
    ).round(2)
    
    # Add a column to store parent ID for hierarchical relationships
    customer_agg["id"] = customer_agg["Customer number"]
    customer_agg["parent"] = None  # Customers are top level
    
    # For projects, parent is the customer
    project_with_customer["id"] = project_with_customer["Customer number"].astype(str) + "-" + project_with_customer["Project number"].astype(str)
    project_with_customer["parent"] = project_with_customer["Customer number"]
    
    # Select the same columns for both dataframes for consistent merging
    common_columns = [
        'id', 'parent', 'Level', 'Customer number', 'Customer name',
        'Hours worked', 'Billable hours', 'Non-billable hours', 'Billability %',
        'Revenue', 'Total cost', 'Total profit', 'Profit margin %',
        'Billable rate', 'Effective rate'
    ]
    
    # Add project-specific columns to project dataframe
    project_columns = common_columns + ['Project number', 'Project', 'Number of people']
    
    # For customer dataframe, add placeholder columns for project-specific data
    customer_agg['Project number'] = None
    customer_agg['Project'] = None
    customer_agg['Number of people'] = customer_agg['Number of projects']  # Use project count instead
    
    # Select final columns for both dataframes
    customer_df = customer_agg[project_columns].copy()
    project_df = project_with_customer[project_columns].copy()
    
    # Combine the two dataframes
    hierarchy_df = pd.concat([customer_df, project_df], ignore_index=True)
    
    return hierarchy_df

def aggregate_project_by_month_year(df: pd.DataFrame, project_numbers: list = None, planned_df: pd.DataFrame = None, filter_settings: dict = None) -> pd.DataFrame:
    """
    Aggregate data by month and year for specific projects, including planned hours if available.
    
    Args:
        df: Validated and transformed dataframe
        project_numbers: List of project numbers to include (None means all projects)
        planned_df: Optional planned hours dataframe (already filtered by Person type)
        filter_settings: Dictionary with filter settings, including date_filter_type
        
    Returns:
        Dataframe with month-year aggregations for specified projects
    """
    # Ensure Date column exists and is datetime type
    if "Date" not in df.columns and (planned_df is None or "Date" not in planned_df.columns):
        raise ValueError("Date column not found in dataframe")
    
    # Filter by project if project_numbers provided
    filtered_df = df.copy()
    if project_numbers is not None and len(project_numbers) > 0:
        filtered_df = filtered_df[filtered_df['Project number'].isin(project_numbers)]
    
    # Handle case where filtered_df is empty but we have planned data
    if filtered_df.empty and (planned_df is None or planned_df.empty):
        return pd.DataFrame()
    
    # Initialize month_year_agg
    month_year_agg = pd.DataFrame()
    
    # Process actual data if not empty
    if not filtered_df.empty:
        # Create month and year columns
        filtered_df['Year'] = filtered_df['Date'].dt.year
        filtered_df['Month'] = filtered_df['Date'].dt.month
        
        # Create month name for better display
        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        filtered_df['Month name'] = filtered_df['Month'].map(month_names)
        
        # Create date string for sorting (YYYY-MM)
        filtered_df['Date string'] = filtered_df['Year'].astype(str) + '-' + filtered_df['Month'].astype(str).str.zfill(2)
        
        # Aggregate metrics by month and year
        month_year_agg = filtered_df.groupby(['Year', 'Month', 'Month name', 'Date string']).agg({
            "Hours worked": "sum",
            "Billable hours": "sum",
            "Person": "nunique"
        }).reset_index()
        
        # Add calculated columns
        month_year_agg["Non-billable hours"] = month_year_agg["Hours worked"] - month_year_agg["Billable hours"]
        month_year_agg["Billability %"] = (month_year_agg["Billable hours"] / month_year_agg["Hours worked"] * 100).round(2)
        month_year_agg.rename(columns={"Person": "Number of people"}, inplace=True)
    
    # Handle planned hours data if provided
    if planned_df is not None and not planned_df.empty:
        # Create month name mapping
        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        
        # Create month and year columns in planned data
        planned_df_agg = planned_df.copy()
        
        # Determine if we should use date filtering
        apply_date_filter = True
        if filter_settings and 'date_filter_type' in filter_settings:
            # Don't filter dates if "All time" is selected
            if filter_settings['date_filter_type'] == "All time":
                apply_date_filter = False
                
        # Apply date filter if needed
        if apply_date_filter and filter_settings and 'start_date' in filter_settings and 'end_date' in filter_settings:
            start_date = filter_settings['start_date']
            end_date = filter_settings['end_date']
            planned_df_agg = planned_df_agg[
                (planned_df_agg['Date'].dt.date >= start_date) & 
                (planned_df_agg['Date'].dt.date <= end_date)
            ]
        
        planned_df_agg['Year'] = planned_df_agg['Date'].dt.year
        planned_df_agg['Month'] = planned_df_agg['Date'].dt.month
        
        # Filter by project if project_numbers provided
        if project_numbers is not None and len(project_numbers) > 0:
            planned_df_agg = planned_df_agg[planned_df_agg['Project number'].isin(project_numbers)]
        
        # Create month name for planned data too
        planned_df_agg['Month name'] = planned_df_agg['Month'].map(month_names)
        planned_df_agg['Date string'] = planned_df_agg['Year'].astype(str) + '-' + planned_df_agg['Month'].astype(str).str.zfill(2)
        
        # Create base aggregation for planned hours
        planned_agg_dict = {"Planned hours": "sum"}
        
        # Check if Planned rate exists and add to aggregation
        has_planned_rate = "Planned rate" in planned_df_agg.columns
        
        # Aggregate planned hours by month and year
        if not has_planned_rate:
            planned_month_year = planned_df_agg.groupby(['Year', 'Month', 'Month name', 'Date string']).agg(
                planned_agg_dict
            ).reset_index()
        else:
            # First aggregate just the hours
            planned_month_year = planned_df_agg.groupby(['Year', 'Month', 'Month name', 'Date string']).agg(
                planned_agg_dict
            ).reset_index()
            
            # Then calculate weighted average of planned rate by month/year
            planned_rate_by_month = planned_df_agg.groupby(['Year', 'Month', 'Month name', 'Date string']).apply(
                lambda x: (x["Planned rate"] * x["Planned hours"]).sum() / x["Planned hours"].sum() 
                if x["Planned hours"].sum() > 0 else 0
            ).reset_index()
            planned_rate_by_month.columns = ['Year', 'Month', 'Month name', 'Date string', 'Planned rate']
            
            # Merge planned rate into the planned hours dataframe
            planned_month_year = pd.merge(
                planned_month_year,
                planned_rate_by_month,
                on=['Year', 'Month', 'Month name', 'Date string']
            )
        
        # Calculate planned revenue (planned hours * planned rate)
        if "Planned rate" in planned_month_year.columns:
            planned_month_year["Planned revenue"] = planned_month_year["Planned hours"] * planned_month_year["Planned rate"]
        
        # Merge planned hours with actual hours
        if month_year_agg.empty:
            # No actual data, use planned data as base
            month_year_agg = planned_month_year.copy()
            # Add missing actual data columns with zeros
            month_year_agg["Hours worked"] = 0
            month_year_agg["Billable hours"] = 0
            month_year_agg["Number of people"] = 0
            month_year_agg["Non-billable hours"] = 0
            month_year_agg["Billability %"] = 0
        else:
            # Merge planned with actual
            month_year_agg = pd.merge(
                month_year_agg,
                planned_month_year,
                on=['Year', 'Month', 'Month name', 'Date string'],
                how='outer'
            )
            
            # Fill missing values with 0
            month_year_agg["Hours worked"] = month_year_agg["Hours worked"].fillna(0)
            month_year_agg["Billable hours"] = month_year_agg["Billable hours"].fillna(0)
            month_year_agg["Number of people"] = month_year_agg["Number of people"].fillna(0)
            month_year_agg["Non-billable hours"] = month_year_agg["Non-billable hours"].fillna(0)
            month_year_agg["Billability %"] = month_year_agg["Billability %"].fillna(0)
            month_year_agg["Planned hours"] = month_year_agg["Planned hours"].fillna(0)
        
        # Calculate hours variance metrics
        if "Planned hours" in month_year_agg.columns:
            month_year_agg["Hours variance"] = month_year_agg["Hours worked"] - month_year_agg["Planned hours"]
            
            # Calculate hours variance percentage (avoid division by zero)
            month_year_agg["Variance percentage"] = 0.0
            mask = month_year_agg["Planned hours"] > 0
            month_year_agg.loc[mask, "Variance percentage"] = (
                month_year_agg.loc[mask, "Hours variance"] / month_year_agg.loc[mask, "Planned hours"] * 100
            ).round(2)
        
        # Handle rate calculations if planned rate exists
        if has_planned_rate and "Planned rate" in month_year_agg.columns:
            month_year_agg["Planned rate"] = month_year_agg["Planned rate"].fillna(0)
            
            # Calculate effective rate from billable hours/revenue if we have actual data
            if not filtered_df.empty:
                # Add revenue calculations using new approach
                if "Fee per time record" in filtered_df.columns:
                    revenue_by_month = filtered_df.groupby(['Year', 'Month', 'Month name', 'Date string'])["Fee per time record"].sum().reset_index(name="Revenue")
                elif "Hourly rate" in filtered_df.columns:
                    # Fallback calculation
                    revenue_by_month = filtered_df.groupby(['Year', 'Month', 'Month name', 'Date string']).apply(
                        lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
                    ).reset_index()
                    revenue_by_month.columns = ['Year', 'Month', 'Month name', 'Date string', 'Revenue']
                else:
                    revenue_by_month = pd.DataFrame(columns=['Year', 'Month', 'Month name', 'Date string', 'Revenue'])
                
                # Merge revenue into aggregated dataframe
                month_year_agg = pd.merge(
                    month_year_agg,
                    revenue_by_month,
                    on=['Year', 'Month', 'Month name', 'Date string'],
                    how='left'
                )
                
                # Fill missing values
                month_year_agg["Revenue"] = month_year_agg["Revenue"].fillna(0)
                
                # Calculate effective rate (revenue / billable hours)
                month_year_agg["Effective rate"] = 0.0
                mask = month_year_agg["Billable hours"] > 0
                month_year_agg.loc[mask, "Effective rate"] = (
                    month_year_agg.loc[mask, "Revenue"] / month_year_agg.loc[mask, "Billable hours"]
                ).round(2)
                
                # Calculate rate variance metrics
                month_year_agg["Rate variance"] = month_year_agg["Effective rate"] - month_year_agg["Planned rate"]
                
                # Calculate rate variance percentage (avoid division by zero)
                month_year_agg["Rate variance percentage"] = 0.0
                mask = month_year_agg["Planned rate"] > 0
                month_year_agg.loc[mask, "Rate variance percentage"] = (
                    month_year_agg.loc[mask, "Rate variance"] / month_year_agg.loc[mask, "Planned rate"] * 100
                ).round(2)
                
                # Calculate revenue variance if planned revenue exists
                if "Planned revenue" in month_year_agg.columns:
                    # Calculate revenue variance metrics
                    month_year_agg["Revenue variance"] = month_year_agg["Revenue"] - month_year_agg["Planned revenue"]
                    
                    # Calculate revenue variance percentage (avoid division by zero)
                    month_year_agg["Revenue variance percentage"] = 0.0
                    mask = month_year_agg["Planned revenue"] > 0
                    month_year_agg.loc[mask, "Revenue variance percentage"] = (
                        month_year_agg.loc[mask, "Revenue variance"] / month_year_agg.loc[mask, "Planned revenue"] * 100
                    ).round(2)
            else:
                # No actual data or hourly rate, set default values
                month_year_agg["Revenue"] = 0
                month_year_agg["Effective rate"] = 0
                month_year_agg["Rate variance"] = 0 - month_year_agg["Planned rate"]
                month_year_agg["Rate variance percentage"] = -100.0  # 100% below planned
                
                if "Planned revenue" in month_year_agg.columns:
                    month_year_agg["Revenue variance"] = 0 - month_year_agg["Planned revenue"]
                    month_year_agg["Revenue variance percentage"] = -100.0  # 100% below planned
    
    # Add revenue and hourly rates if not already added
    if not filtered_df.empty and "Revenue" not in month_year_agg.columns:
        # Add revenue (new approach with fallback)
        if "Fee per time record" in df.columns:
            revenue_by_month_year = filtered_df.groupby(['Year', 'Month'])["Fee per time record"].sum().reset_index(name="Revenue")
        elif "Hourly rate" in df.columns:
            # Fallback to old calculation
            revenue_by_month_year = filtered_df.groupby(['Year', 'Month']).apply(
                lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
            ).reset_index()
            revenue_by_month_year.columns = ['Year', 'Month', 'Revenue']
        else:
            revenue_by_month_year = pd.DataFrame(columns=['Year', 'Month', 'Revenue'])
        
        # Merge revenue into the aggregated dataframe
        month_year_agg = pd.merge(month_year_agg, revenue_by_month_year, on=['Year', 'Month'], how='left')
        month_year_agg["Revenue"] = month_year_agg["Revenue"].fillna(0)
        
        # Calculate billable hourly rate (revenue / billable hours)
        month_year_agg["Billable rate"] = 0  # Default
        mask = month_year_agg["Billable hours"] > 0
        month_year_agg.loc[mask, "Billable rate"] = month_year_agg.loc[mask, "Revenue"] / month_year_agg.loc[mask, "Billable hours"]
        
        # Calculate effective hourly rate (revenue / total hours)
        month_year_agg["Effective rate"] = 0  # Default
        mask = month_year_agg["Hours worked"] > 0
        month_year_agg.loc[mask, "Effective rate"] = month_year_agg.loc[mask, "Revenue"] / month_year_agg.loc[mask, "Hours worked"]
    else:
        # Make sure these columns exist if not already added
        if "Revenue" not in month_year_agg.columns:
            month_year_agg["Revenue"] = 0
        if "Billable rate" not in month_year_agg.columns:
            month_year_agg["Billable rate"] = 0
        if "Effective rate" not in month_year_agg.columns:
            month_year_agg["Effective rate"] = 0
    
    # Add cost and profit calculations if not already added
    if not filtered_df.empty:
        # Add cost if not already present
        if "Total cost" not in month_year_agg.columns:
            if "Cost per time record" in filtered_df.columns:
                cost_by_month_year = filtered_df.groupby(['Year', 'Month'])["Cost per time record"].sum().reset_index(name="Total cost")
                month_year_agg = pd.merge(month_year_agg, cost_by_month_year, on=['Year', 'Month'], how='left')
                month_year_agg["Total cost"] = month_year_agg["Total cost"].fillna(0)
            else:
                month_year_agg["Total cost"] = 0
        
        # Add profit if not already present
        if "Total profit" not in month_year_agg.columns:
            if "Profit per time record" in filtered_df.columns:
                profit_by_month_year = filtered_df.groupby(['Year', 'Month'])["Profit per time record"].sum().reset_index(name="Total profit")
                month_year_agg = pd.merge(month_year_agg, profit_by_month_year, on=['Year', 'Month'], how='left')
                month_year_agg["Total profit"] = month_year_agg["Total profit"].fillna(0)
            else:
                month_year_agg["Total profit"] = 0
        
        # Calculate profit margin if not already present
        if "Profit margin %" not in month_year_agg.columns:
            month_year_agg["Profit margin %"] = 0.0
            mask = month_year_agg["Revenue"] > 0
            month_year_agg.loc[mask, "Profit margin %"] = (month_year_agg.loc[mask, "Total profit"] / month_year_agg.loc[mask, "Revenue"] * 100).round(2)
    
    # Sort by date if we have data
    if not month_year_agg.empty and 'Date string' in month_year_agg.columns:
        month_year_agg = month_year_agg.sort_values('Date string')
    
    return month_year_agg
# charts/summary_charts.py
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
from typing import Dict, Any, List, Tuple
from utils.chart_styles import get_currency_formatting
from utils.currency_formatter import format_millions, get_currency_code, CURRENCY_SYMBOLS

def render_summary_tab(
    filtered_df: pd.DataFrame,
    filter_settings: Dict[str, Any]
) -> None:
    """
    Renders a matrix of project performance data.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        filter_settings: Dictionary containing all active filter settings
    """
    
    # Check if dataframe is empty
    if filtered_df.empty:
        st.warning("No data available with the current filter settings. Please adjust your filters to see a summary.")
        return
    
    # Generate filter description
    filter_description = generate_filter_description(filter_settings)
    
    # Calculate key metrics
    total_hours = filtered_df["Hours worked"].sum()
    total_billable_hours = filtered_df["Billable hours"].sum()
    billability_percentage = (total_billable_hours / total_hours * 100) if total_hours > 0 else 0
    total_projects = filtered_df["Project number"].nunique()
    
    # Revenue metrics (if hourly rate exists)
    has_revenue = "Hourly rate" in filtered_df.columns
    total_revenue = None
    if has_revenue:
        total_revenue = (filtered_df["Billable hours"] * filtered_df["Hourly rate"]).sum()
        avg_hourly_rate = total_revenue / total_billable_hours if total_billable_hours > 0 else 0
    
    # Get data for matrix
    customer_insights = get_customer_insights(filtered_df, top_n=10)
    project_insights = get_top_projects(filtered_df, top_n=10)
    project_type_insights = get_project_type_insights(filtered_df, top_n=10)
    phase_insights = get_phase_insights(filtered_df, top_n=10)
    activity_insights = get_activity_insights(filtered_df, top_n=10)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Define card styles once
    st.markdown("""
        <style>
        .card-container {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            height: 100%;
            min-height: 140px;
        }
        .card-title {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 10px;
            color: #1E3050;
            border-bottom: 1px solid #dee2e6;
            padding-bottom: 5px;
        }
        .card-content {
            font-size: 1.1rem;
        }
        .no-data {
            color: #6c757d;
            font-style: italic;
        }
        .matrix-header {
            text-align: center;
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 1.4rem;
        }
        .row-header {
            font-weight: bold;
            margin-top: 10px;
            margin-bottom: 5px;
            font-size: 1.3rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Create matrix layout headers
    col_headers = st.columns(3)
    with col_headers[0]:
        st.markdown('<div class="matrix-header">💰 Revenue</div>', unsafe_allow_html=True)
    with col_headers[1]:
        st.markdown('<div class="matrix-header">⏱️ Hours Worked</div>', unsafe_allow_html=True)
    with col_headers[2]:
        st.markdown('<div class="matrix-header">💲 Avg. Hourly Rate</div>', unsafe_allow_html=True)
        
    # Row 1: Customers
    st.markdown('<div class="row-header">🏢 Customers</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    
    # Revenue
    with cols[0]:
        create_card(
            title="Top Customers by Revenue",
            content=render_by_revenue(customer_insights.get("top_customers", []), has_revenue, "customer"),
            show_data=has_revenue and len(customer_insights.get("top_customers", [])) > 0
        )
    
    # Hours
    with cols[1]:
        create_card(
            title="Top Customers by Hours",
            content=render_by_hours(customer_insights.get("top_customers", []), "customer"),
            show_data=len(customer_insights.get("top_customers", [])) > 0
        )
    
    # Rate
    with cols[2]:
        create_card(
            title="Top Customers by Hourly Rate",
            content=render_by_rate(customer_insights.get("top_customers", []), has_revenue, "customer"),
            show_data=has_revenue and len(customer_insights.get("top_customers", [])) > 0
        )
    
    # Row 2: Projects
    st.markdown('<div class="row-header">📋 Projects</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    
    # Revenue
    with cols[0]:
        create_card(
            title="Top Projects by Revenue",
            content=render_by_revenue(project_insights, has_revenue, "project"),
            show_data=has_revenue and len(project_insights) > 0
        )
    
    # Hours
    with cols[1]:
        create_card(
            title="Top Projects by Hours",
            content=render_by_hours(project_insights, "project"),
            show_data=len(project_insights) > 0
        )
    
    # Rate
    with cols[2]:
        create_card(
            title="Top Projects by Hourly Rate",
            content=render_by_rate(project_insights, has_revenue, "project"),
            show_data=has_revenue and len(project_insights) > 0
        )
    
    # Row 3: Project Types
    st.markdown('<div class="row-header">📊 Project Types</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    
    # Revenue
    with cols[0]:
        create_card(
            title="Top Project Types by Revenue",
            content=render_by_revenue(project_type_insights.get("top_project_types", []), has_revenue, "project_type"),
            show_data=has_revenue and len(project_type_insights.get("top_project_types", [])) > 0
        )
    
    # Hours
    with cols[1]:
        create_card(
            title="Top Project Types by Hours",
            content=render_by_hours(project_type_insights.get("top_project_types", []), "project_type"),
            show_data=len(project_type_insights.get("top_project_types", [])) > 0
        )
    
    # Rate
    with cols[2]:
        create_card(
            title="Top Project Types by Hourly Rate",
            content=render_by_rate(project_type_insights.get("top_project_types", []), has_revenue, "project_type"),
            show_data=has_revenue and len(project_type_insights.get("top_project_types", [])) > 0
        )
    
    # Row 4: Phases
    st.markdown('<div class="row-header">🔄 Phases</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    
    # Revenue
    with cols[0]:
        create_card(
            title="Top Phases by Revenue",
            content=render_by_revenue(phase_insights.get("top_phases", []), has_revenue, "phase"),
            show_data=has_revenue and len(phase_insights.get("top_phases", [])) > 0
        )
    
    # Hours
    with cols[1]:
        create_card(
            title="Top Phases by Hours",
            content=render_by_hours(phase_insights.get("top_phases", []), "phase"),
            show_data=len(phase_insights.get("top_phases", [])) > 0
        )
    
    # Rate
    with cols[2]:
        create_card(
            title="Top Phases by Hourly Rate",
            content=render_by_rate(phase_insights.get("top_phases", []), has_revenue, "phase"),
            show_data=has_revenue and len(phase_insights.get("top_phases", [])) > 0
        )
    
    # Row 5: Activities
    st.markdown('<div class="row-header">🔨 Activities</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    
    # Revenue
    with cols[0]:
        create_card(
            title="Top Activities by Revenue",
            content=render_by_revenue(activity_insights.get("top_activities", []), has_revenue, "activity"),
            show_data=has_revenue and len(activity_insights.get("top_activities", [])) > 0
        )
    
    # Hours
    with cols[1]:
        create_card(
            title="Top Activities by Hours",
            content=render_by_hours(activity_insights.get("top_activities", []), "activity"),
            show_data=len(activity_insights.get("top_activities", [])) > 0
        )
    
    # Rate
    with cols[2]:
        create_card(
            title="Top Activities by Hourly Rate",
            content=render_by_rate(activity_insights.get("top_activities", []), has_revenue, "activity"),
            show_data=has_revenue and len(activity_insights.get("top_activities", [])) > 0
        )


def create_card(title: str, content: str, show_data: bool = True) -> None:
    """
    Creates a card-like container for displaying information.
    
    Args:
        title: Card title
        content: Card content (HTML/markdown)
        show_data: Whether to show data or a placeholder message
    """
    # Create the card HTML
    if show_data:
        st.markdown(f"""
            <div class="card-container">
                <div class="card-title">{title}</div>
                <div class="card-content">
                    {content}
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="card-container">
                <div class="card-title">{title}</div>
                <div class="card-content">
                    <div class="no-data">No data available</div>
        """, unsafe_allow_html=True)


def render_by_revenue(items: List[Dict[str, Any]], has_revenue: bool, item_type: str) -> str:
    """
    Renders HTML for items sorted by revenue
    
    Args:
        items: List of items (customers, projects, etc.)
        has_revenue: Whether revenue data is available
        item_type: Type of item (customer, project, etc.)
    
    Returns:
        HTML string with formatted content
    """
    if not items or not has_revenue:
        return "<div class='no-data'>No revenue data available</div>"
    
    # Sort items by revenue if present
    sorted_items = sorted(items, key=lambda x: x.get('revenue', 0), reverse=True)
    
    html = ""
    for i, item in enumerate(sorted_items[:10]):
        if "revenue" not in item:
            continue
            
        item_name = item.get('name', '')
        revenue = format_millions(item['revenue'])
        
        # Add percentage if available or calculate it
        percentage_text = ""
        if "revenue_percentage" in item:
            percentage_text = f" ({item['revenue_percentage']:.1f}% of total)"
        
        html += f"""
            <div style="margin-bottom: 8px;">
                <div style="font-weight: bold;">{i+1}. {item_name}</div>
                <div>{revenue}{percentage_text}</div>
            </div>
        """
    
    return html if html else "<div class='no-data'>No revenue data available</div>"


def render_by_hours(items: List[Dict[str, Any]], item_type: str) -> str:
    """
    Renders HTML for items sorted by hours worked
    
    Args:
        items: List of items (customers, projects, etc.)
        item_type: Type of item (customer, project, etc.)
    
    Returns:
        HTML string with formatted content
    """
    if not items:
        return "<div class='no-data'>No hours data available</div>"
    
    # Sort items by hours if present
    sorted_items = sorted(items, key=lambda x: x.get('hours', 0), reverse=True)
    
    html = ""
    for i, item in enumerate(sorted_items[:10]):
        if "hours" not in item:
            continue
            
        item_name = item.get('name', '')
        # Format hours as whole number with space as thousand separator
        hours = f"{int(item['hours']):,}".replace(',', ' ') + " hours"
        
        # Add additional context based on item type
        context_text = ""
        if item_type == "customer" and "projects" in item:
            context_text = f" ({item['projects']} projects)"
        elif item_type == "project" and "projects" in item:
            context_text = f" ({item['projects']} projects)"
        elif item_type == "project_type" and "projects" in item:
            context_text = f" ({item['projects']} projects)"
        
        html += f"""
            <div style="margin-bottom: 8px;">
                <div style="font-weight: bold;">{i+1}. {item_name}</div>
                <div>{hours}{context_text}</div>
            </div>
        """
    
    return html if html else "<div class='no-data'>No hours data available</div>"


def render_by_rate(items: List[Dict[str, Any]], has_revenue: bool, item_type: str) -> str:
    """
    Renders HTML for items sorted by hourly rate
    
    Args:
        items: List of items (customers, projects, etc.)
        has_revenue: Whether revenue data is available
        item_type: Type of item (customer, project, etc.)
    
    Returns:
        HTML string with formatted content
    """
    if not items or not has_revenue:
        return "<div class='no-data'>No hourly rate data available</div>"
    
    # Calculate and add hourly rate if not present
    for item in items:
        if "revenue" in item and "hours" in item and "rate" not in item and item["hours"] > 0:
            item["rate"] = item["revenue"] / item["hours"]
    
    # Sort items by rate
    sorted_items = sorted(items, key=lambda x: x.get('rate', 0) 
                          if isinstance(x.get('rate', 0), (int, float)) else 0, reverse=True)
    
    # Get currency formatting
    symbol, position, _ = get_currency_formatting()
    
    html = ""
    for i, item in enumerate(sorted_items[:10]):
        # Skip items with no hourly rate or with zero hours
        if "rate" not in item or item.get("hours", 0) <= 0:
            continue
            
        item_name = item.get('name', '')
        
        # Format the rate with appropriate currency symbol and position
        if position == 'before':
            rate = f"{symbol}{item['rate']:.0f}/hour"
        else:
            rate = f"{item['rate']:.0f} {symbol}/hour"
        
        html += f"""
            <div style="margin-bottom: 8px;">
                <div style="font-weight: bold;">{i+1}. {item_name}</div>
                <div>{rate}</div>
            </div>
        """
    
    return html if html else "<div class='no-data'>No hourly rate data available</div>"


def generate_filter_description(filter_settings: Dict[str, Any]) -> str:
    """
    Generates a natural language description of the applied filters.
    
    Args:
        filter_settings: Dictionary containing all active filter settings
        
    Returns:
        String describing the filters that are applied
    """
    descriptions = []
    
    # Date filter description
    if "date_filter_type" in filter_settings:
        if filter_settings["date_filter_type"] == "All time":
            descriptions.append("across all time periods")
        elif filter_settings["date_filter_type"] == "Custom range":
            start_date = filter_settings.get("start_date")
            end_date = filter_settings.get("end_date")
            if start_date and end_date:
                start_str = start_date.strftime("%B %d, %Y")
                end_str = end_date.strftime("%B %d, %Y")
                descriptions.append(f"from {start_str} to {end_str}")
        else:
            descriptions.append(f"during {filter_settings['date_filter_type'].lower()}")
    
    # Customer filter description
    if "included_customers" in filter_settings and filter_settings["included_customers"]:
        if len(filter_settings["included_customers"]) == 1:
            descriptions.append(f"for customer {filter_settings['included_customers'][0]}")
        else:
            descriptions.append(f"for {len(filter_settings['included_customers'])} selected customers")
    
    # Project filter description
    if "included_projects" in filter_settings and filter_settings["included_projects"]:
        if len(filter_settings["included_projects"]) == 1:
            descriptions.append(f"focusing on project {filter_settings['included_projects'][0]}")
        else:
            descriptions.append(f"focusing on {len(filter_settings['included_projects'])} selected projects")
    
    # Project type filter description
    if "included_types" in filter_settings and filter_settings["included_types"]:
        if len(filter_settings["included_types"]) == 1:
            descriptions.append(f"for {filter_settings['included_types'][0]} type projects")
        else:
            descriptions.append(f"for {', '.join(filter_settings['included_types'])} type projects")

    # Project hours range filter description
    if "project_min_hours" in filter_settings and "project_max_hours" in filter_settings:
        min_hours = filter_settings["project_min_hours"]
        max_hours = filter_settings["project_max_hours"]
        descriptions.append(f"in projects between {min_hours} and {max_hours} hours")
    
    # Billability filter description
    if "selected_billability" in filter_settings:
        if filter_settings["selected_billability"] == "billable":
            descriptions.append("considering only billable hours")
        elif filter_settings["selected_billability"] == "non-billable":
            descriptions.append("considering only non-billable hours")
    
    # Combine all descriptions
    if descriptions:
        return "Based on time records " + ", ".join(descriptions) + ", "
    else:
        return "Based on all time records, "


def get_top_projects(df: pd.DataFrame, top_n: int = 3) -> List[Dict[str, Any]]:
    """
    Identifies the top projects by revenue.
    
    Args:
        df: Filtered DataFrame
        top_n: Number of top projects to return
        
    Returns:
        List of dictionaries with project metrics
    """
    # Check if dataframe is empty or lacks necessary columns
    if df.empty or "Project" not in df.columns or "Project number" not in df.columns:
        return []
    
    # Check if we can calculate revenue
    has_revenue = "Hourly rate" in df.columns and "Billable hours" in df.columns
    
    # Aggregate data by project
    project_metrics = []
    
    # Group by project and calculate metrics
    project_agg = df.groupby(["Project number", "Project"]).agg({
        "Hours worked": "sum",
        "Billable hours": "sum"
    }).reset_index()
    
    if has_revenue:
        # Calculate revenue
        project_agg["Revenue"] = df.groupby(["Project number"]).apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")["Revenue"]
        
        # Calculate hourly rate
        project_agg["Rate"] = project_agg["Revenue"] / project_agg["Hours worked"].where(project_agg["Hours worked"] > 0, 1)
        
        # Calculate total revenue for percentage calculation
        total_revenue = project_agg["Revenue"].sum()
    
    # Create project info dictionaries
    for _, project in project_agg.iterrows():
        project_info = {
            "number": project["Project number"],
            "name": project["Project"],
            "hours": project["Hours worked"]
        }
        
        if has_revenue:
            project_info["revenue"] = project["Revenue"]
            project_info["rate"] = project["Rate"]
            project_info["revenue_percentage"] = (project["Revenue"] / total_revenue * 100) if total_revenue > 0 else 0
        
        project_metrics.append(project_info)
    
    return project_metrics


def get_customer_insights(df: pd.DataFrame, top_n: int = 3) -> Dict[str, Any]:
    """
    Extracts key insights about top customers from the filtered data.
    
    Args:
        df: Filtered DataFrame
        top_n: Number of top customers to return
        
    Returns:
        Dictionary with customer insights
    """
    insights = {}
    
    # Check if dataframe is empty or lacks necessary columns
    if df.empty or "Customer number" not in df.columns or "Customer name" not in df.columns:
        return insights
    
    # Calculate customer metrics
    customer_agg = df.groupby(["Customer number", "Customer name"]).agg({
        "Hours worked": "sum",
        "Project number": "nunique"
    }).reset_index()
    
    # Check if we can calculate revenue
    has_revenue = "Hourly rate" in df.columns and "Billable hours" in df.columns
    
    if has_revenue:
        # Calculate revenue by customer
        customer_agg["Revenue"] = df.groupby(["Customer number"]).apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")["Revenue"]
        
        # Calculate hourly rate
        customer_agg["Rate"] = customer_agg["Revenue"] / customer_agg["Hours worked"].where(customer_agg["Hours worked"] > 0, 1)
        
        # Calculate total revenue
        total_revenue = customer_agg["Revenue"].sum()
    
    # Store top customers data
    top_customers_list = []
    for _, customer in customer_agg.iterrows():
        customer_info = {
            "name": customer["Customer name"],
            "number": customer["Customer number"],
            "hours": customer["Hours worked"],
            "projects": customer["Project number"]
        }
        
        if has_revenue:
            customer_info["revenue"] = customer["Revenue"]
            customer_info["rate"] = customer["Rate"]
            customer_info["revenue_percentage"] = (customer["Revenue"] / total_revenue * 100) if total_revenue > 0 else 0
        
        top_customers_list.append(customer_info)
    
    insights["top_customers"] = top_customers_list
    insights["total_customers"] = len(customer_agg)
    
    return insights


def get_project_type_insights(df: pd.DataFrame, top_n: int = 3) -> Dict[str, Any]:
    """
    Extracts key insights about project types from the filtered data.
    
    Args:
        df: Filtered DataFrame
        top_n: Number of top project types to return
        
    Returns:
        Dictionary with project type insights
    """
    insights = {}
    
    # Check if dataframe is empty or lacks necessary columns
    if df.empty or "Project type" not in df.columns:
        return insights
    
    # Calculate project type metrics
    project_type_agg = df.groupby(["Project type"]).agg({
        "Hours worked": "sum",
        "Project number": "nunique"
    }).reset_index()
    
    # Check if we can calculate revenue
    has_revenue = "Hourly rate" in df.columns and "Billable hours" in df.columns
    
    if has_revenue:
        # Calculate revenue directly in the aggregation
        project_type_revenue = {}
        
        # For each project type, calculate total revenue
        for project_type in df["Project type"].unique():
            project_df = df[df["Project type"] == project_type]
            revenue = (project_df["Billable hours"] * project_df["Hourly rate"]).sum()
            project_type_revenue[project_type] = revenue
        
        # Add revenue to aggregated data
        project_type_agg["Revenue"] = project_type_agg["Project type"].map(project_type_revenue)
        
        # Calculate hourly rate
        project_type_agg["Rate"] = project_type_agg["Revenue"] / project_type_agg["Hours worked"].where(project_type_agg["Hours worked"] > 0, 1)
        
        # Calculate total revenue for percentage calculation
        total_revenue = project_type_agg["Revenue"].sum()
    
    # Store top project types data
    top_project_types_list = []
    for _, project_type in project_type_agg.iterrows():
        project_type_info = {
            "name": project_type["Project type"],
            "hours": project_type["Hours worked"],
            "projects": project_type["Project number"]
        }
        
        if has_revenue:
            project_type_info["revenue"] = project_type["Revenue"]
            project_type_info["rate"] = project_type["Rate"]
            project_type_info["revenue_percentage"] = (project_type["Revenue"] / total_revenue * 100) if total_revenue > 0 else 0
        
        top_project_types_list.append(project_type_info)
    
    insights["top_project_types"] = top_project_types_list
    insights["total_project_types"] = len(project_type_agg)
    
    return insights


def get_phase_insights(df: pd.DataFrame, top_n: int = 3) -> Dict[str, Any]:
    """
    Extracts key insights about project phases from the filtered data.
    
    Args:
        df: Filtered DataFrame
        top_n: Number of top phases to return
        
    Returns:
        Dictionary with phase insights
    """
    insights = {}
    
    # Check if dataframe is empty or lacks necessary columns
    if df.empty or "Phase" not in df.columns:
        return insights
    
    # Calculate phase metrics
    phase_agg = df.groupby(["Phase"]).agg({
        "Hours worked": "sum"
    }).reset_index()
    
    # Check if we can calculate revenue
    has_revenue = "Hourly rate" in df.columns and "Billable hours" in df.columns
    
    if has_revenue:
        # Calculate revenue by phase
        phase_agg["Revenue"] = df.groupby(["Phase"]).apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")["Revenue"]
        
        # Calculate hourly rate
        phase_agg["Rate"] = phase_agg["Revenue"] / phase_agg["Hours worked"].where(phase_agg["Hours worked"] > 0, 1)
        
        # Calculate total revenue for percentage calculation
        total_revenue = phase_agg["Revenue"].sum()
    
    # Store top phases data
    top_phases_list = []
    for _, phase in phase_agg.iterrows():
        phase_info = {
            "name": phase["Phase"],
            "hours": phase["Hours worked"]
        }
        
        if has_revenue:
            phase_info["revenue"] = phase["Revenue"]
            phase_info["rate"] = phase["Rate"]
            phase_info["revenue_percentage"] = (phase["Revenue"] / total_revenue * 100) if total_revenue > 0 else 0
        
        top_phases_list.append(phase_info)
    
    insights["top_phases"] = top_phases_list
    insights["total_phases"] = len(phase_agg)
    
    return insights


def get_activity_insights(df: pd.DataFrame, top_n: int = 3) -> Dict[str, Any]:
    """
    Extracts key insights about activities from the filtered data.
    
    Args:
        df: Filtered DataFrame
        top_n: Number of top activities to return
        
    Returns:
        Dictionary with activity insights
    """
    insights = {}
    
    # Check if dataframe is empty or lacks necessary columns
    if df.empty or "Activity" not in df.columns:
        return insights
    
    # Calculate activity metrics
    activity_agg = df.groupby(["Activity"]).agg({
        "Hours worked": "sum"
    }).reset_index()
    
    # Check if we can calculate revenue
    has_revenue = "Hourly rate" in df.columns and "Billable hours" in df.columns
    
    if has_revenue:
        # Calculate revenue by activity
        activity_agg["Revenue"] = df.groupby(["Activity"]).apply(
            lambda x: (x["Billable hours"] * x["Hourly rate"]).sum()
        ).reset_index(name="Revenue")["Revenue"]
        
        # Calculate hourly rate
        activity_agg["Rate"] = activity_agg["Revenue"] / activity_agg["Hours worked"].where(activity_agg["Hours worked"] > 0, 1)
        
        # Calculate total revenue for percentage calculation
        total_revenue = activity_agg["Revenue"].sum()
    
    # Store top activities data
    top_activities_list = []
    for _, activity in activity_agg.iterrows():
        activity_info = {
            "name": activity["Activity"],
            "hours": activity["Hours worked"]
        }
        
        if has_revenue:
            activity_info["revenue"] = activity["Revenue"]
            activity_info["rate"] = activity["Rate"]
            activity_info["revenue_percentage"] = (activity["Revenue"] / total_revenue * 100) if total_revenue > 0 else 0
        
        top_activities_list.append(activity_info)
    
    insights["top_activities"] = top_activities_list
    insights["total_activities"] = len(activity_agg)
    
    return insights
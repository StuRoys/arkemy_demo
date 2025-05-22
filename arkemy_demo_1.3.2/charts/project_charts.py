# charts/project_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import re
import numpy as np
from datetime import datetime

from utils.chart_styles import (
    create_column_config, 
    render_chart, 
    get_category_colors,
    get_metric_options,
    get_visualization_options,
    format_variance_columns,
    format_time_period_columns,
    standardize_column_order
)

from utils.chart_helpers import (
    create_standardized_customdata,
    create_comparison_chart,
    create_single_metric_chart,
    filter_projects_by_metric,
    create_forecast_chart,
    create_monthly_metrics_chart,
    create_summary_metrics_table,
    create_yearly_metrics_table,
    create_monthly_metrics_table
)

# We no longer need this import as we're using Streamlit's built-in formatting
# from utils.currency_formatter import format_with_space_separators

def render_project_tab(filtered_df, aggregate_by_project, render_chart, get_category_colors, planned_df=None, filter_settings=None):
    """
    Renders the project analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_project: Function to aggregate data by project
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
        planned_df: Optional DataFrame with planned hours data
    """
    # Check if planned data is available - use simple check on data presence
    has_planned_data = planned_df is not None and len(planned_df) > 0
    
    # Ensure Project number is string type in both dataframes for consistent joining
    filtered_df = filtered_df.copy()
    filtered_df["Project number"] = filtered_df["Project number"].astype(str)
    
    if has_planned_data:
        planned_df = planned_df.copy()
        planned_df["Project number"] = planned_df["Project number"].astype(str)
    
    # Aggregate by project
    project_agg = aggregate_by_project(filtered_df)
    
    # Merge with planned data if available
    if has_planned_data:
        # Import the function to merge actual and planned data
        from utils.planned_processors import aggregate_by_project_planned, merge_actual_planned_projects
        
        # Aggregate planned data by project
        planned_agg = aggregate_by_project_planned(planned_df)
        
        # Merge actual and planned data
        project_agg = merge_actual_planned_projects(project_agg, planned_agg)
    
    # Get metric options using the new helper function
    metric_options = get_metric_options(has_planned_data)

    col1, col2 = st.columns(2)

    with col1:
        selected_metric = st.selectbox(
            "Metric",
            options=metric_options,
            index=1,  # Default to Hours worked
            key="metric_selectbox"
        )
        
        # Skip category headers if they're selected
        if "---" in selected_metric:
            selected_metric = "Hours worked"  # Default fallback
    
    # Set comparison view flags based on metric selection
    is_hours_comparison_view = selected_metric == "Hours worked vs Planned hours"
    is_rate_comparison_view = selected_metric == "Effective rate vs Planned rate"
    is_revenue_comparison_view = selected_metric == "Revenue vs Planned revenue"
    is_forecast_hours_view = selected_metric == "Hours" and "--- Forecast ---" in metric_options
    is_comparison_view = is_hours_comparison_view or is_rate_comparison_view or is_revenue_comparison_view

    with col2:
        # Get visualization options using the new helper function
        viz_options = get_visualization_options(is_comparison_view, is_forecast_hours_view)
        default_index = 0  # Default to Monthly: Bar chart
        
        # Visualization type selection
        selected_viz_type = st.radio(
            "Chart type",
            options=viz_options,
            index=default_index,
            key="viz_type_radio",
            horizontal=True
        )
        visualization_type = selected_viz_type
    
    # For monthly view, use the filtered dataframe directly
    is_monthly_view = visualization_type == "Monthly: Bar chart"
    
    # Import the new function for monthly aggregation if needed
    from utils.processors import aggregate_project_by_month_year
    
    # For monthly view, process differently based on whether it's a comparison or single metric
    if is_monthly_view:
        # Get monthly data using the already filtered dataframe and pass planned data if available
        monthly_data = aggregate_project_by_month_year(filtered_df, planned_df=planned_df, filter_settings=filter_settings)
        
        # Check if we have data
        if monthly_data.empty:
            st.error("No monthly data available for the selected projects.")
        else:
            # Create the monthly chart
            month_labels = monthly_data["Month name"] + " " + monthly_data["Year"].astype(str)
            
            # If it's a forecast hours view, create the accumulated forecast chart
            if is_forecast_hours_view and has_planned_data:
                # Use the new helper function to create the forecast chart
                fig, forecast_df = create_forecast_chart(monthly_data)
                
            # If it's a hours comparison view, create a grouped bar chart
            elif is_hours_comparison_view and has_planned_data:
                fig = create_comparison_chart(
                    monthly_data,
                    "Hours worked",
                    "Planned hours",
                    "Hours Worked vs Planned Hours by Month",
                    "Hours",
                    x_field=monthly_data["Month name"] + " " + monthly_data["Year"].astype(str)
                )
                
                # Ensure x-axis is in chronological order
                fig.update_layout(
                    xaxis={'categoryorder': 'array', 'categoryarray': month_labels}
                )
                
            # If it's a rate comparison view, create a grouped bar chart
            elif is_rate_comparison_view and has_planned_data and "Planned rate" in monthly_data.columns:
                fig = create_comparison_chart(
                    monthly_data,
                    "Effective rate",
                    "Planned rate",
                    "Effective Rate vs Planned Rate by Month",
                    "Rate",
                    x_field=monthly_data["Month name"] + " " + monthly_data["Year"].astype(str)
                )
                
                # Ensure x-axis is in chronological order
                fig.update_layout(
                    xaxis={'categoryorder': 'array', 'categoryarray': month_labels}
                )
                
            # If it's a revenue comparison view, create a grouped bar chart
            elif is_revenue_comparison_view and has_planned_data and "Planned revenue" in monthly_data.columns:
                fig = create_comparison_chart(
                    monthly_data,
                    "Revenue",
                    "Planned revenue",
                    "Revenue vs Planned Revenue by Month",
                    "Revenue_Amount",
                    x_field=monthly_data["Month name"] + " " + monthly_data["Year"].astype(str)
                )
                
                # Ensure x-axis is in chronological order
                fig.update_layout(
                    xaxis={'categoryorder': 'array', 'categoryarray': month_labels}
                )
                
            else:
                # For single metric view, use the new helper function
                # Check if the selected metric is a comparison that we need to handle specially
                if selected_metric in ["Hours worked vs Planned hours", "Effective rate vs Planned rate", "Revenue vs Planned revenue"]:
                    # Default to Hours worked if it's a comparison view but we got here
                    plot_metric = "Hours worked"
                else:
                    plot_metric = selected_metric
                    
                fig = create_monthly_metrics_chart(monthly_data, plot_metric, month_labels)
            
            # Render the chart
            render_chart(fig, "project_monthly")
            
            # Create total summary table - expanded first
            with st.expander("Metrics: Total", expanded=False):
                # Use the new helper function to create the summary metrics table
                summary_df = create_summary_metrics_table(monthly_data, has_planned_data)
                
                # Add unique project count from original filtered_df
                summary_df["Unique projects"] = filtered_df["Project number"].nunique()
                
                # Display summary metrics - use original dataframe instead of formatted
                st.dataframe(
                    summary_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config=create_column_config(summary_df)
                )
            
            # Yearly metrics
            with st.expander("Metrics: Year", expanded=False):
                # Use the new helper function to create the yearly metrics table
                yearly_data = create_yearly_metrics_table(monthly_data, filtered_df, has_planned_data)
                
                # Display the yearly aggregation - use original dataframe
                st.dataframe(
                    yearly_data,
                    use_container_width=True,
                    hide_index=True,
                    column_config=create_column_config(yearly_data)
                )
            
            # Monthly metrics    
            with st.expander("Metrics: Month", expanded=False):
                # Use the new helper function to create the monthly metrics table
                forecast_df_param = forecast_df if is_forecast_hours_view and has_planned_data and 'forecast_df' in locals() else None
                display_df, visible_cols = create_monthly_metrics_table(monthly_data, filtered_df, is_forecast_hours_view, forecast_df_param, has_planned_data)
                
                # Use original dataframe
                st.dataframe(
                    display_df[visible_cols],  # Only show visible columns
                    use_container_width=True,
                    hide_index=True,
                    column_config=create_column_config(display_df)
                )
            
            # Project metrics
            with st.expander("Metrics: Project", expanded=False):
                # Use the complete project_agg dataframe from earlier
                sorted_project_agg = standardize_column_order(project_agg.sort_values("Hours worked", ascending=False))
                
                # Display the table with column configurations - use original dataframe
                st.dataframe(
                    sorted_project_agg,
                    use_container_width=True,
                    hide_index=True,
                    column_config=create_column_config(sorted_project_agg)
                )
    else:
        # Filter projects based on selected metric or for comparison view
        if is_hours_comparison_view:
            # For hours comparison view, include projects with either hours worked or planned hours > 0
            filtered_project_agg = filter_projects_by_metric(
                project_agg, 
                "Hours worked", 
                "Planned hours", 
                is_comparison_view=True
            )
        elif is_rate_comparison_view:
            # For rate comparison view, include projects with either effective rate or planned rate > 0
            filtered_project_agg = filter_projects_by_metric(
                project_agg, 
                "Effective rate", 
                "Planned rate", 
                is_comparison_view=True
            )
        elif is_revenue_comparison_view:
            # For revenue comparison view, include projects with either revenue or planned revenue > 0
            filtered_project_agg = filter_projects_by_metric(
                project_agg, 
                "Revenue", 
                "Planned revenue", 
                is_comparison_view=True
            )
        else:
            # For single metric view, filter projects with metric > 0
            filtered_project_agg = filter_projects_by_metric(
                project_agg, 
                selected_metric
            )
        
        # Render visualization based on type and metric
        if not filtered_project_agg.empty:
            # Hours comparison view (Hours worked vs Planned hours)
            if is_hours_comparison_view and has_planned_data:
                fig = create_comparison_chart(
                    filtered_project_agg,
                    "Hours worked",
                    "Planned hours",
                    "Hours Worked vs Planned Hours by Project",
                    "Hours"
                )
                
                # Render the chart
                render_chart(fig, "project")
            
            # Rate comparison view (Effective rate vs Planned rate)
            elif is_rate_comparison_view and has_planned_data and "Planned rate" in filtered_project_agg.columns:
                fig = create_comparison_chart(
                    filtered_project_agg,
                    "Effective rate",
                    "Planned rate",
                    "Effective Rate vs Planned Rate by Project",
                    "Rate"
                )
                
                # Render the chart
                render_chart(fig, "project")
                
            # Revenue comparison view (Revenue vs Planned revenue)
            elif is_revenue_comparison_view and has_planned_data and "Planned revenue" in filtered_project_agg.columns:
                fig = create_comparison_chart(
                    filtered_project_agg,
                    "Revenue",
                    "Planned revenue",
                    "Revenue vs Planned Revenue by Project",
                    "Revenue_Amount"
                )
                
                # Render the chart
                render_chart(fig, "project")
            
            # Project: Treemap visualization
            elif visualization_type == "Project: Treemap":
                fig = create_single_metric_chart(
                    filtered_project_agg,
                    selected_metric,
                    f"Project {selected_metric} Distribution",
                    chart_type="treemap"
                )
                
                render_chart(fig, "project")
            
            # Project: Bar chart visualization
            elif visualization_type == "Project: Bar chart":
                fig = create_single_metric_chart(
                    filtered_project_agg,
                    selected_metric,
                    f"{selected_metric} by Project",
                    chart_type="bar",
                    sort_by=selected_metric
                )
                
                # Render the chart
                render_chart(fig, "project")
        else:
            st.error(f"No projects have values greater than zero for {selected_metric}.")
        
        # Project metrics table only for non-monthly views
        with st.expander("Metrics: Project", expanded=False):
            # Sort by hours worked in descending order
            sorted_project_agg = standardize_column_order(project_agg.sort_values("Hours worked", ascending=False))
            
            # Display the table with column configurations - use original dataframe
            st.dataframe(
                sorted_project_agg,
                use_container_width=True,
                hide_index=True,
                column_config=create_column_config(sorted_project_agg)
            )
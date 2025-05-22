# chart_helpers.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np

def create_standardized_customdata(df):
    """
    Creates standardized custom data array for consistent hover templates.
    
    Args:
        df: DataFrame containing project or monthly metrics
        
    Returns:
        List of lists to be used as custom_data in Plotly charts
    """
    custom_data = []
    
    # [0] Hours worked
    custom_data.append(df["Hours worked"])
    
    # [1] Billable hours
    if "Billable hours" in df.columns:
        custom_data.append(df["Billable hours"])
    else:
        custom_data.append([0] * len(df))
    
    # [2] Billability %
    if "Billability %" in df.columns:
        custom_data.append(df["Billability %"])
    else:
        custom_data.append([0] * len(df))
    
    # [3] Number of people/projects
    if "Number of people" in df.columns:
        custom_data.append(df["Number of people"])
    else:
        custom_data.append([0] * len(df))
    
    # [4] Billable rate
    if "Billable rate" in df.columns:
        custom_data.append(df["Billable rate"])
    else:
        custom_data.append([0] * len(df))
    
    # [5] Effective rate
    if "Effective rate" in df.columns:
        custom_data.append(df["Effective rate"])
    else:
        custom_data.append([0] * len(df))
    
    # [6] Revenue
    if "Revenue" in df.columns:
        custom_data.append(df["Revenue"])
    else:
        custom_data.append([0] * len(df))
    
    # [7] Planned hours
    if "Planned hours" in df.columns:
        custom_data.append(df["Planned hours"])
    else:
        custom_data.append([0] * len(df))
    
    # [8] Planned rate
    if "Planned rate" in df.columns:
        custom_data.append(df["Planned rate"])
    else:
        custom_data.append([0] * len(df))
    
    # [9] Planned revenue
    if "Planned revenue" in df.columns:
        custom_data.append(df["Planned revenue"])
    else:
        custom_data.append([0] * len(df))
    
    # [10] Hours variance (absolute)
    if "Hours variance" in df.columns:
        custom_data.append(df["Hours variance"])
    else:
        custom_data.append([0] * len(df))
    
    # [11] Hours variance (%)
    if "Variance percentage" in df.columns:
        custom_data.append(df["Variance percentage"])
    else:
        custom_data.append([0] * len(df))
    
    # [12] Rate variance (absolute)
    if "Rate variance" in df.columns:
        custom_data.append(df["Rate variance"])
    else:
        custom_data.append([0] * len(df))
    
    # [13] Rate variance (%)
    if "Rate variance percentage" in df.columns:
        custom_data.append(df["Rate variance percentage"])
    else:
        custom_data.append([0] * len(df))
    
    # [14] Revenue variance (absolute)
    if "Revenue variance" in df.columns:
        custom_data.append(df["Revenue variance"])
    else:
        custom_data.append([0] * len(df))
    
    # [15] Revenue variance (%)
    if "Revenue variance percentage" in df.columns:
        custom_data.append(df["Revenue variance percentage"])
    else:
        custom_data.append([0] * len(df))
    
    return custom_data

# Replace the create_comparison_chart function in chart_helpers.py with this version

def create_comparison_chart(df, primary_metric, comparison_metric, title, y_axis_label, x_field="Project"):
    """
    Creates a comparison bar chart between two metrics.
    
    Args:
        df: DataFrame with project/month data
        primary_metric: Name of the primary metric (e.g., "Hours worked")
        comparison_metric: Name of the comparison metric (e.g., "Planned hours")
        title: Chart title
        y_axis_label: Label for Y axis
        x_field: Field to use for x-axis categories, defaults to "Project"
        
    Returns:
        Plotly figure with grouped bar chart
    """
    # Check if x_field is a Series (not a string column name)
    # If it is, create a temporary column to use for indexing
    temp_df = df.copy()
    if not isinstance(x_field, str):
        # Create a temporary column for the x-axis labels
        temp_df["_temp_x_axis_"] = x_field
        x_field_name = "_temp_x_axis_"
    else:
        x_field_name = x_field
    
    # Prepare data for comparison chart
    comparison_df = temp_df[[x_field_name, primary_metric, comparison_metric]].copy()
    
    # Sort by primary metric in descending order
    comparison_df = comparison_df.sort_values(primary_metric, ascending=False)
    
    # Add a slider to control number of items to display if we have more than one
    if len(comparison_df) > 1 and x_field_name == "Project":  # Only show slider for Project view
        num_items = st.slider(
            f"Number of {x_field_name.lower()}s to display:",
            min_value=1,
            max_value=min(1000, len(comparison_df)),
            value=min(10, len(comparison_df)),
            step=1,
            key="item_count_slider"
        )
        # Limit the number of items based on slider
        comparison_df = comparison_df.head(num_items)
    
    # Convert from wide to long format for grouped bar chart
    comparison_long_df = pd.melt(
        comparison_df,
        id_vars=[x_field_name],
        value_vars=[primary_metric, comparison_metric],
        var_name="Metric",
        value_name=y_axis_label
    )
    
    # Create a grouped bar chart
    fig = px.bar(
        comparison_long_df,
        x=x_field_name,
        y=y_axis_label,
        color="Metric",
        barmode="group",
        title=title,
        color_discrete_sequence=["#2ca02c", "#1f77b4"]  # Green for primary, Blue for comparison
    )
    
    # Improve layout for better readability
    fig.update_layout(
        xaxis_title="",
        yaxis_title=y_axis_label,
        xaxis={'categoryorder':'total descending'},
        legend_title_text=""
    )
    
    return fig

def create_single_metric_chart(df, metric, title, chart_type="bar", x_field="Project", sort_by=None):
    """
    Creates a single metric visualization (bar chart or treemap).
    
    Args:
        df: DataFrame with project/month data
        metric: Name of the metric to visualize
        title: Chart title
        chart_type: 'bar' or 'treemap'
        x_field: Field to use for x-axis or path (for treemap)
        sort_by: Optional column to sort by (for bar charts)
        
    Returns:
        Plotly figure
    """
    # For bar charts
    if chart_type == "bar":
        # Sort data if specified
        if sort_by:
            df = df.sort_values(sort_by, ascending=False)
        
        # Add a slider to control number of items if we have more than one
        if len(df) > 1 and x_field == "Project":  # Only show slider for Project view
            num_items = st.slider(
                f"Number of {x_field.lower()}s to display:",
                min_value=1,
                max_value=min(1000, len(df)),
                value=min(10, len(df)),
                step=1,
                key="item_count_slider"
            )
            # Limit the number of items based on slider
            limited_df = df.head(num_items)
        else:
            limited_df = df
        
        # Get customdata for hover AFTER limiting the dataframe
        custom_data = create_standardized_customdata(limited_df)
        
        # Create the bar chart
        fig = px.bar(
            limited_df,
            x=x_field,
            y=metric,
            color=metric,
            color_continuous_scale="Greens",
            title=title,
            custom_data=custom_data
        )
        
        # Improve layout for better readability
        fig.update_layout(
            xaxis_title="",
            yaxis_title=metric,
            xaxis={'categoryorder':'total descending'}
        )
    
    # For treemaps
    elif chart_type == "treemap":
        # Create custom data for treemap
        treemap_custom_data = create_standardized_customdata(df)
        
        # Create the treemap
        fig = px.treemap(
            df,
            path=[x_field],
            values=metric,
            color=metric,
            color_continuous_scale="Greens",
            custom_data=treemap_custom_data,
            title=title
        )
    
    return fig

def filter_projects_by_metric(df, metric, planned_metric=None, is_comparison_view=False):
    """
    Filters projects based on selected metric or for comparison view.
    
    Args:
        df: DataFrame with project data
        metric: Name of the primary metric
        planned_metric: Name of the comparison metric (for comparison views)
        is_comparison_view: Whether this is a comparison view
        
    Returns:
        Filtered DataFrame
    """
    if is_comparison_view and planned_metric:
        # For comparison view, include projects with either metric > 0
        return df[(df[metric] > 0) | (df[planned_metric] > 0)]
    else:
        # For single metric view, filter projects with metric > 0
        return df[df[metric] > 0]

def create_forecast_chart(monthly_data):
    """
    Creates a forecast hours chart that shows accumulated hours over time.
    
    Args:
        monthly_data: DataFrame with monthly hours data
        
    Returns:
        Plotly figure with the forecast chart
    """
    # Get current month and year for comparison
    current_date = datetime.now().date()
    current_year = current_date.year
    current_month = current_date.month
    
    # Create a copy of the monthly data to calculate forecast
    forecast_df = monthly_data.copy()
    
    # Create a column to indicate if the month is in the past or future
    forecast_df["Time Period"] = forecast_df.apply(
        lambda row: "Actual" if (row["Year"] < current_year or 
                               (row["Year"] == current_year and row["Month"] < current_month)) 
                        else "Planned",
        axis=1
    )
    
    # Create the forecast column using hours worked for past months and planned hours for future
    forecast_df["Month Value"] = forecast_df.apply(
        lambda row: row["Hours worked"] if row["Time Period"] == "Actual" else row["Planned hours"],
        axis=1
    )
    
    # Make sure the data is sorted chronologically
    forecast_df = forecast_df.sort_values(["Year", "Month"])
    
    # Calculate the cumulative sum of forecast values
    forecast_df["Accumulated Forecast"] = forecast_df["Month Value"].cumsum()
    
    # Create the bar chart
    fig = px.bar(
        forecast_df,
        x=forecast_df["Month name"] + " " + forecast_df["Year"].astype(str),
        y="Accumulated Forecast",
        color="Time Period",
        color_discrete_map={"Actual": "#2ca02c", "Planned": "#1f77b4"},  # Green for past, Blue for future
        title="Accumulated Hours Forecast by Month",
        text=forecast_df["Month Value"].round(0).astype(int)
    )
    
    # Create custom hover data
    hover_template = "<b>%{x}</b><br><br>"
    hover_template += "Month's Value: %{text} hours<br>"
    hover_template += "Accumulated Forecast: %{y:,.1f} hours<br>"
    hover_template += "<extra></extra>"  # Hide secondary tooltip
    
    # Ensure x-axis is in chronological order and apply hover template
    month_labels = monthly_data["Month name"] + " " + monthly_data["Year"].astype(str)
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Accumulated Hours",
        xaxis={'categoryorder': 'array', 'categoryarray': month_labels}
    )
    
    fig.update_traces(hovertemplate=hover_template)
    
    # Adjust text position and format
    fig.update_traces(textposition='inside', textangle=0)
    
    return fig, forecast_df

def create_monthly_metrics_chart(monthly_data, selected_metric, month_labels):
    """
    Creates a single metric monthly bar chart.
    
    Args:
        monthly_data: DataFrame with monthly metrics
        selected_metric: The metric to plot
        month_labels: Labels for the x-axis
        
    Returns:
        Plotly figure with the monthly metrics chart
    """
    # Get standardized customdata for hover templating
    custom_data = create_standardized_customdata(monthly_data)
    
    fig = px.bar(
        monthly_data,
        x=month_labels,
        y=selected_metric,
        color=selected_metric,
        color_continuous_scale="Greens",
        title=f"{selected_metric} by Month for Selected Projects",
        custom_data=custom_data
    )
                
    # Improve layout
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title=selected_metric,
        xaxis={'categoryorder': 'array', 'categoryarray': month_labels},
        hovermode="closest"
    )
    
    return fig

# Import the standardize_column_order function
from utils.chart_styles import standardize_column_order

def create_summary_metrics_table(monthly_data, has_planned_data=False):
    """
    Creates a summary metrics table with totals across all time periods.
    
    Args:
        monthly_data: DataFrame with monthly metrics
        has_planned_data: Whether planned data is available
        
    Returns:
        DataFrame with summary metrics
    """
    # Calculate summary metrics from monthly data
    summary_metrics = {
        "Hours worked": monthly_data["Hours worked"].sum(),
        "Billable hours": monthly_data["Billable hours"].sum(),
        "Billability %": (monthly_data["Billable hours"].sum() / monthly_data["Hours worked"].sum() * 100) if monthly_data["Hours worked"].sum() > 0 else 0,
    }
    
    # Weighted average for billable rate (weighted by billable hours)
    if "Billable rate" in monthly_data.columns and "Billable hours" in monthly_data.columns:
        billable_sum = monthly_data["Billable hours"].sum()
        summary_metrics["Billable rate"] = (monthly_data["Billable rate"] * monthly_data["Billable hours"]).sum() / billable_sum if billable_sum > 0 else 0
    else:
        summary_metrics["Billable rate"] = 0
        
    # Weighted average for effective rate (weighted by hours worked)
    if "Effective rate" in monthly_data.columns:
        hours_sum = monthly_data["Hours worked"].sum()
        summary_metrics["Effective rate"] = (monthly_data["Effective rate"] * monthly_data["Hours worked"]).sum() / hours_sum if hours_sum > 0 else 0
    else:
        summary_metrics["Effective rate"] = 0
        
    # Revenue total
    if "Revenue" in monthly_data.columns:
        summary_metrics["Revenue"] = monthly_data["Revenue"].sum()
    
    # Add planned metrics if available
    if has_planned_data:
        if "Planned hours" in monthly_data.columns:
            summary_metrics["Planned hours"] = monthly_data["Planned hours"].sum()
            summary_metrics["Hours variance"] = summary_metrics["Hours worked"] - summary_metrics["Planned hours"]
            if summary_metrics["Planned hours"] > 0:
                summary_metrics["Variance percentage"] = (summary_metrics["Hours variance"] / summary_metrics["Planned hours"]) * 100
            
        if "Planned rate" in monthly_data.columns:
            planned_hours_sum = monthly_data["Planned hours"].sum() if "Planned hours" in monthly_data.columns else 0
            if planned_hours_sum > 0:
                summary_metrics["Planned rate"] = (monthly_data["Planned rate"] * monthly_data["Planned hours"]).sum() / planned_hours_sum
                if "Effective rate" in summary_metrics:
                    summary_metrics["Rate variance"] = summary_metrics["Effective rate"] - summary_metrics["Planned rate"]
                    if summary_metrics["Planned rate"] > 0:
                        summary_metrics["Rate variance percentage"] = (summary_metrics["Rate variance"] / summary_metrics["Planned rate"]) * 100
            
        if "Planned revenue" in monthly_data.columns:
            summary_metrics["Planned revenue"] = monthly_data["Planned revenue"].sum()
            if "Revenue" in summary_metrics:
                summary_metrics["Revenue variance"] = summary_metrics["Revenue"] - summary_metrics["Planned revenue"]
                if summary_metrics["Planned revenue"] > 0:
                    summary_metrics["Revenue variance percentage"] = (summary_metrics["Revenue variance"] / summary_metrics["Planned revenue"]) * 100
    
    # Convert to DataFrame for display
    summary_df = pd.DataFrame([summary_metrics])
    
    # Standardize column order before returning
    return standardize_column_order(summary_df)

def create_yearly_metrics_table(monthly_data, filtered_df, has_planned_data=False):
    """
    Creates a yearly metrics table aggregated by year.
    
    Args:
        monthly_data: DataFrame with monthly metrics
        filtered_df: Original filtered DataFrame with time records
        has_planned_data: Whether planned data is available
        
    Returns:
        DataFrame with yearly metrics
    """
    # Group by Year and aggregate
    yearly_data = monthly_data.groupby('Year').agg({
        'Hours worked': 'sum',
        'Billable hours': 'sum',
        'Month': 'count'  # Count of months with data
    })

    # Calculate Billability % for each year
    yearly_data['Billability %'] = (yearly_data['Billable hours'] / yearly_data['Hours worked'] * 100)

    # Calculate weighted averages for rates if available
    if 'Effective rate' in monthly_data.columns:
        # Weighted average - effective rate weighted by hours worked
        yearly_rates = monthly_data.groupby('Year').apply(
            lambda x: (x['Effective rate'] * x['Hours worked']).sum() / x['Hours worked'].sum() 
            if x['Hours worked'].sum() > 0 else 0
        )
        yearly_data['Effective rate'] = yearly_rates

    if 'Billable rate' in monthly_data.columns:
        # Weighted average - billable rate weighted by billable hours
        yearly_billable_rates = monthly_data.groupby('Year').apply(
            lambda x: (x['Billable rate'] * x['Billable hours']).sum() / x['Billable hours'].sum() 
            if x['Billable hours'].sum() > 0 else 0
        )
        yearly_data['Billable rate'] = yearly_billable_rates

    # Add Revenue if available
    if 'Revenue' in monthly_data.columns:
        yearly_data['Revenue'] = monthly_data.groupby('Year')['Revenue'].sum()

    # Add unique projects count per year
    # Create a temporary dataframe with year and unique project counts
    yearly_projects = filtered_df.groupby(pd.Grouper(key='Date', freq='Y')).agg({
        'Project number': 'nunique'
    }).reset_index()
    yearly_projects['Year'] = yearly_projects['Date'].dt.year
    
    # Create a mapping dictionary and apply it to yearly_data
    yearly_projects_dict = dict(zip(yearly_projects['Year'], yearly_projects['Project number']))
    
    # Make sure yearly_data has Year as a column for mapping
    if isinstance(yearly_data.index, pd.Index) and yearly_data.index.name == 'Year':
        yearly_data = yearly_data.reset_index()
    
    # Map the unique project counts
    yearly_data['Unique projects'] = yearly_data['Year'].map(yearly_projects_dict)

    # Add planned data metrics if available
    if has_planned_data:
        if 'Planned hours' in monthly_data.columns:
            yearly_data['Planned hours'] = monthly_data.groupby('Year')['Planned hours'].sum()
            yearly_data['Hours variance'] = yearly_data['Hours worked'] - yearly_data['Planned hours']
            yearly_data['Variance percentage'] = (yearly_data['Hours variance'] / yearly_data['Planned hours'] * 100) \
                .where(yearly_data['Planned hours'] > 0, 0)
                
        if 'Planned rate' in monthly_data.columns:
            # Weighted average for planned rate
            yearly_planned_rates = monthly_data.groupby('Year').apply(
                lambda x: (x['Planned rate'] * x['Planned hours']).sum() / x['Planned hours'].sum() 
                if x['Planned hours'].sum() > 0 else 0
            )
            yearly_data['Planned rate'] = yearly_planned_rates
            
            if 'Effective rate' in yearly_data.columns:
                yearly_data['Rate variance'] = yearly_data['Effective rate'] - yearly_data['Planned rate']
                yearly_data['Rate variance percentage'] = (yearly_data['Rate variance'] / yearly_data['Planned rate'] * 100) \
                    .where(yearly_data['Planned rate'] > 0, 0)
                
        if 'Planned revenue' in monthly_data.columns:
            yearly_data['Planned revenue'] = monthly_data.groupby('Year')['Planned revenue'].sum()
            
            if 'Revenue' in yearly_data.columns:
                yearly_data['Revenue variance'] = yearly_data['Revenue'] - yearly_data['Planned revenue']
                yearly_data['Revenue variance percentage'] = (yearly_data['Revenue variance'] / yearly_data['Planned revenue'] * 100) \
                    .where(yearly_data['Planned revenue'] > 0, 0)

    # Rename the 'Month' column to something more descriptive
    yearly_data = yearly_data.rename(columns={'Month': 'Months'})
    
    # Convert Year to string (if it's not a string already)
    if 'Year' in yearly_data.columns and not pd.api.types.is_string_dtype(yearly_data['Year']):
        yearly_data['Year'] = yearly_data['Year'].astype(str)
    
    # Drop any columns that are all NaN
    yearly_data = yearly_data.dropna(axis=1, how='all')
    
    # Ensure index is dropped
    yearly_data = yearly_data.reset_index(drop=True)
    
    # Standardize column order before returning
    return standardize_column_order(yearly_data)

def create_monthly_metrics_table(monthly_data, filtered_df, is_forecast_hours_view=False, forecast_df=None, has_planned_data=False):
    """
    Creates a monthly metrics table with all metrics by month.
    
    Args:
        monthly_data: DataFrame with monthly metrics
        filtered_df: Original filtered DataFrame with time records
        is_forecast_hours_view: Whether this is a forecast hours view
        forecast_df: Optional forecast DataFrame if in forecast view
        has_planned_data: Whether planned data is available
        
    Returns:
        DataFrame with monthly metrics
    """
    # Define base columns that should always be included if they exist
    base_cols = ["Year", "Month name", "Hours worked", "Billable hours", "Date string"]

    # Define additional metrics we want to display if available
    additional_metrics = [
        "Billability %", 
        "Billable rate",
        "Effective rate",
        "Revenue"
    ]
    
    # Calculate unique projects per month and add to monthly_data
    # Only do this calculation once
    if "Unique projects" not in monthly_data.columns:
        # Create monthly grouping with unique project counts
        monthly_projects = filtered_df.groupby([
            pd.Grouper(key='Date', freq='M')
        ]).agg({
            'Project number': 'nunique'
        }).reset_index()
        
        # Extract year and month for joining
        monthly_projects['Year'] = monthly_projects['Date'].dt.year
        monthly_projects['Month'] = monthly_projects['Date'].dt.month
        
        # Create join keys
        monthly_projects['join_key'] = monthly_projects['Year'].astype(str) + "-" + monthly_projects['Month'].astype(str)
        monthly_data['join_key'] = monthly_data['Year'].astype(str) + "-" + monthly_data['Month'].astype(str)
        
        # Merge
        monthly_data = pd.merge(
            monthly_data,
            monthly_projects[['join_key', 'Project number']],
            on='join_key',
            how='left'
        )
        
        # Rename and clean up
        monthly_data = monthly_data.rename(columns={'Project number': 'Unique projects'})
        monthly_data = monthly_data.drop(columns=['join_key'])
    
    # Add Unique projects to additional metrics
    additional_metrics.append("Unique projects")

    # Define planned metrics to include if available
    planned_metrics = [
        "Planned hours",
        "Planned rate", 
        "Planned revenue",
        "Hours variance",
        "Variance percentage",
        "Rate variance",
        "Rate variance percentage",
        "Revenue variance",
        "Revenue variance percentage"
    ]

    # Start with base columns
    display_cols = base_cols.copy()

    # Add any additional metrics that exist in the DataFrame
    for metric in additional_metrics:
        if metric in monthly_data.columns:
            display_cols.append(metric)

    # Add any planned metrics that exist
    for metric in planned_metrics:
        if metric in monthly_data.columns:
            display_cols.append(metric)

    # Add accumulated forecast to table if we're in forecast view
    if is_forecast_hours_view and has_planned_data and forecast_df is not None:
        # Create copy of the display dataframe including forecast data
        # Make sure to include 'Month' for merging, even if it's not in display_cols
        merge_cols = list(display_cols) + (['Month'] if 'Month' not in display_cols else [])
        forecast_display_df = pd.merge(
            monthly_data[merge_cols],
            forecast_df[['Year', 'Month', 'Month Value', 'Accumulated Forecast', 'Time Period']],
            on=['Year', 'Month'],
            how='left'
        )
        display_df = forecast_display_df
        # Add forecast columns to display list
        visible_cols = [col for col in display_df.columns if col != "Date string" and col != "Month"]
    else:
        # Sort by Year and Month name instead of Month
        display_df = monthly_data[display_cols].copy()
        # Add forecast columns to display list
        visible_cols = [col for col in display_df.columns if col != "Date string"]

    # Sort the DataFrame
    if "Year" in display_df.columns:
        if "Month" in display_df.columns:
            display_df = display_df.sort_values(["Year", "Month"])
        else:
            # If Month column doesn't exist, try sorting by Date string
            if "Date string" in monthly_data.columns:
                display_df = display_df.sort_values("Date string")
            else:
                display_df = display_df.sort_values("Year")
    
    # Standardize column order
    display_df = standardize_column_order(display_df)
    
    # For the visible columns, we need to ensure "Date string" and "Month" are excluded
    visible_cols = [col for col in display_df.columns if col not in ["Date string", "Month"]]
    
    return display_df, visible_cols

def add_unique_projects_count(df, filtered_df, frequency='M'):
    """
    Adds unique projects count to a dataframe.
    
    Args:
        df: DataFrame to add the counts to
        filtered_df: Source DataFrame with project data
        frequency: Time frequency for grouping ('M' for month, 'Y' for year)
        
    Returns:
        DataFrame with unique projects count added
    """
    # Create grouping with unique project counts
    projects_count = filtered_df.groupby([
        pd.Grouper(key='Date', freq=frequency)
    ]).agg({
        'Project number': 'nunique'
    }).reset_index()
    
    # Extract year and month/year for joining
    projects_count['Year'] = projects_count['Date'].dt.year
    
    if frequency == 'M':
        projects_count['Month'] = projects_count['Date'].dt.month
        # Create join keys
        projects_count['join_key'] = projects_count['Year'].astype(str) + "-" + projects_count['Month'].astype(str)
        df['join_key'] = df['Year'].astype(str) + "-" + df['Month'].astype(str)
    else:
        # For yearly, use only Year as join key
        projects_count['join_key'] = projects_count['Year'].astype(str)
        df['join_key'] = df['Year'].astype(str)
    
    # Merge
    join_cols = ['join_key']
    result_df = pd.merge(
        df,
        projects_count[join_cols + ['Project number']],
        on=join_cols,
        how='left'
    )
    
    # Rename and clean up
    result_df = result_df.rename(columns={'Project number': 'Unique projects'})
    result_df = result_df.drop(columns=['join_key'])
    
    return result_df

def calculate_weighted_averages(df, weight_column, value_columns, group_by=None):
    """
    Calculates weighted averages for specified columns.
    
    Args:
        df: DataFrame with the data
        weight_column: Column to use as weights
        value_columns: List of columns to calculate weighted averages for
        group_by: Optional column to group by before calculating
        
    Returns:
        Series or DataFrame with weighted averages
    """
    if group_by is None:
        # Calculate weighted averages across the entire DataFrame
        result = {}
        for col in value_columns:
            if col in df.columns and weight_column in df.columns:
                weights_sum = df[weight_column].sum()
                if weights_sum > 0:
                    result[col] = (df[col] * df[weight_column]).sum() / weights_sum
                else:
                    result[col] = 0
        return pd.Series(result)
    else:
        # Calculate weighted averages by group
        result = {}
        for col in value_columns:
            if col in df.columns and weight_column in df.columns:
                result[col] = df.groupby(group_by).apply(
                    lambda x: (x[col] * x[weight_column]).sum() / x[weight_column].sum() 
                    if x[weight_column].sum() > 0 else 0
                )
        return pd.DataFrame(result)
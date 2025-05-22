# year_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_year_tab(filtered_df, aggregate_by_year, render_chart, get_category_colors):
    """
    Renders the year analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_year: Function to aggregate data by year
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    #st.subheader("Year Analysis")
    
    # Add metric selection dropdown
    metric_options = [
        "Hours worked",
        "Billable hours", 
        "Billability %",
        "Billable rate",
        "Effective rate",
        "Revenue",
        "Number of projects",
        "Number of customers",
        "Number of people"
    ]
    
    selected_metric = st.selectbox(
        "Select metric to visualize:",
        options=metric_options,
        index=0,  # Default to Hours worked
        key="year_metric_selector"
    )
    
    # Aggregate by year
    year_agg = aggregate_by_year(filtered_df)
    
    # Sort years chronologically
    sorted_years = year_agg.sort_values("Year")
    
    # Create the bar chart with color gradient
    fig_bar = px.bar(
        sorted_years,
        x="Year",
        y=selected_metric,
        color=selected_metric,
        color_continuous_scale="Greens",
        title=f"{selected_metric} by Year",
        custom_data=[
            sorted_years["Hours worked"],            # [0] Hours worked
            sorted_years["Billable hours"],          # [1] Billable hours
            sorted_years["Billability %"],           # [2] Billability %
            sorted_years["Number of projects"],      # [3] Number of projects
            sorted_years["Number of customers"],     # [4] Number of customers
            sorted_years["Effective rate"],           # [5] Effective hourly rate
            sorted_years["Revenue"],                 # [6] Revenue (moved to keep consistent with other charts)
            sorted_years["Billable rate"],           # [7] Billable hourly rate
            sorted_years["Number of people"],        # [8] Number of people
        ]
    )

    # Improve layout for better readability
    fig_bar.update_layout(
        xaxis_title="",
        yaxis_title=selected_metric,
        xaxis={
            'categoryorder':'total ascending',  # Ensure years are in ascending order
            'tickmode': 'array',
            'tickvals': sorted_years['Year'],  # Ensure all years are shown
            'tickangle': 0
        }
    )

    # Render the chart (this will apply styling from chart_styles)
    render_chart(fig_bar, "year")
    
    # Display year data table with all metrics
    st.subheader("Year Data Table")
    
    # Sort by year in ascending order
    sorted_year_agg = year_agg.sort_values("Year")
    
    # Reorder columns for better presentation
    sorted_year_agg = sorted_year_agg[['Year',
                                      'Number of projects', 'Number of customers', 'Number of people',
                                      'Hours worked', 'Billable hours', 
                                      'Non-billable hours', 'Billability %',
                                      'Revenue', 'Billable rate', 'Effective rate']]

    # Use the column configuration from chart_styles
    from utils.chart_styles import create_column_config

    # Display the table with column configurations
    st.dataframe(
        sorted_year_agg,
        use_container_width=True,
        hide_index=True,
        column_config=create_column_config(sorted_year_agg)
    )


def render_monthly_trends_chart(filtered_df, aggregate_by_month_year, render_chart, get_category_colors):
    """
    Renders a line chart showing monthly trends with each year as a separate line.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_month_year: Function to aggregate data by month and year
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    #st.subheader("Monthly Trends Across Years")
    
    # Add metric selection dropdown
    metric_options = [
        "Hours worked",
        "Billable hours", 
        "Billability %",
        "Billable rate",
        "Effective rate",
        "Revenue",
        "Number of projects",
        "Number of customers"
    ]
    
    selected_metric = st.selectbox(
        "Select metric to visualize:",
        options=metric_options,
        index=0,  # Default to Hours worked
        key="monthly_trend_metric_selector"
    )
    
    # Import currency formatting from chart_styles
    from utils.chart_styles import get_currency_formatting
    symbol, position, _ = get_currency_formatting()
    
    # Aggregate data by month and year
    month_year_agg = aggregate_by_month_year(filtered_df)
    
    # Sort by month and year for consistent display
    month_year_agg = month_year_agg.sort_values(["Year", "Month"])
    
    # Extract the list of unique years from the data
    years = month_year_agg['Year'].unique()
    
    # Create a new figure object
    fig = go.Figure()
    
    # Define correct month order
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Calculate monthly averages across all years and reindex to correct month order
    monthly_avg = month_year_agg.groupby('Month name')[selected_metric].mean()
    monthly_avg = monthly_avg.reindex(month_order)
    
    # Define a list of distinct colors for better differentiation
    distinct_colors = [
        '#1f77b4',  # Blue
        '#ff7f0e',  # Orange
        '#2ca02c',  # Green
        '#d62728',  # Red
        '#9467bd',  # Purple
        '#8c564b',  # Brown
        '#e377c2',  # Pink
        '#7f7f7f',  # Gray
        '#bcbd22',  # Olive
        '#17becf',  # Teal
        '#ff9896',  # Light red
        '#98df8a',  # Light green
        '#c5b0d5',  # Light purple
        '#c49c94',  # Light brown
        '#f7b6d2',  # Light pink
        '#dbdb8d',  # Light olive
        '#9edae5',  # Light teal
        '#ad494a',  # Dark red
        '#5254a3',  # Indigo
        '#f98400'   # Dark orange
    ]
    
    # Create formatted hover templates based on metric type
    def create_metric_hover_template(is_average=False):
        prefix = "<b>Average Across All Years</b><br>" if is_average else "<b>Year: %{fullData.name}</b><br>"
        base_template = prefix + "<b>Month: %{x}</b><br>" + f"{selected_metric}: "
        
        if "hours" in selected_metric.lower():
            value_format = "%{y:,.0f} hrs"
        elif "billability" in selected_metric.lower():
            value_format = "%{y:,.1f}%"
        elif "rate" in selected_metric.lower():
            if position == 'before':
                value_format = f"{symbol}%{{y:,.0f}}/hr"
            else:
                value_format = f"%{{y:,.0f}} {symbol}/hr"
        elif "revenue" in selected_metric.lower():
            if position == 'before':
                value_format = f"{symbol}%{{y:,.0f}}"
            else:
                value_format = f"%{{y:,.0f}} {symbol}"
        else:
            value_format = "%{y:,.0f}"
            
        return base_template + value_format
    
    # Add each year's trace to the figure with distinct colors
    for i, year in enumerate(years):
        # Use modulo to cycle through colors if more years than colors
        color_idx = i % len(distinct_colors)
        color = distinct_colors[color_idx]
        
        year_data = month_year_agg[month_year_agg['Year'] == year].sort_values('Month')
        
        fig.add_trace(go.Scatter(
            x=year_data['Month name'],
            y=year_data[selected_metric],
            name=str(int(year)),
            mode='lines+markers',
            line=dict(color=color, width=2),
            marker=dict(size=8),
            hovertemplate=create_metric_hover_template() + "<extra></extra>"
        ))
    
    # Add the average line after all year lines (so it appears first in legend)
    fig.add_trace(go.Scatter(
        x=monthly_avg.index.tolist(),
        y=monthly_avg.values.tolist(),
        name="AVG - All Years",
        mode='lines+markers',
        line=dict(color='black', width=3, dash='dash'),
        marker=dict(size=10, symbol='star'),
        hovertemplate=create_metric_hover_template(is_average=True) + "<extra></extra>"
    ))
    
    # Update layout
    fig.update_layout(
        title=f"{selected_metric} by Month Across Years",
        xaxis_title="Month",
        yaxis_title=selected_metric,
        legend_title="Year",
        xaxis=dict(
            categoryorder='array',
            categoryarray=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ),
        # Move legend to right side and adjust order
        legend=dict(
            yanchor="top",
            y=0.90,
            xanchor="right",
            x=1.10,
            traceorder="reversed"
        )
    )
    
    # Render the chart using the chart_styles
    render_chart(fig, "monthly_trends")
    
    # Show a table with the data
    with st.expander("View Monthly Data Table"):
        # Create a pivot table for display
        display_pivot = month_year_agg.pivot_table(
            index='Month name',
            columns='Year',
            values=selected_metric,
            aggfunc='sum'
        )
        
        # Sort months in correct order
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        display_pivot = display_pivot.reindex(month_order)
        
        # Add average row to the pivot table
        avg_row = display_pivot.mean().round(0).astype(int)
        display_pivot.loc['Average'] = avg_row
        
        # Display the table
        from utils.chart_styles import create_column_config
        
        # Create a temporary DataFrame with the right structure for column config
        temp_df = pd.DataFrame()
        for year in display_pivot.columns:
            temp_df[str(int(year))] = display_pivot[year]
            
        # Display the table with formatting based on metric type
        st.dataframe(
            display_pivot, 
            use_container_width=True
        )
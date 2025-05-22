# customer_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px

def render_customer_tab(filtered_df, aggregate_by_customer, render_chart, get_category_colors):
    """
    Renders the customer analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_customer: Function to aggregate data by customer
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    #st.subheader("Customer Analysis")
    
    # Add metric selection dropdown
    metric_options = [
        "Hours worked",
        "Billable hours", 
        "Billability %",
        "Billable rate",
        "Effective rate",
        "Revenue"
    ]
    
    selected_metric = st.selectbox(
        "Select metric to visualize:",
        options=metric_options,
        index=0,  # Default to Hours worked
        key="customer_metric_selector"
    )
    
    # Aggregate by customer
    customer_agg = aggregate_by_customer(filtered_df)
    
    # Filter out zero values for the selected metric
    filtered_customer_agg = customer_agg[customer_agg[selected_metric] > 0]
    
    # Show warning if some customers were filtered out
    if len(filtered_customer_agg) < len(customer_agg):
        st.warning(f"{len(customer_agg) - len(filtered_customer_agg)} customers with zero {selected_metric} were excluded from visualization.")
    
    # Customer treemap - now using filtered data
    if not filtered_customer_agg.empty:
        fig = px.treemap(
            filtered_customer_agg,
            path=["Customer name"],
            values=selected_metric,
            color=selected_metric,
            color_continuous_scale="Blues",
            custom_data=[
                filtered_customer_agg["Hours worked"],
                filtered_customer_agg["Billable hours"],
                filtered_customer_agg["Billability %"],
                filtered_customer_agg["Number of projects"],
                filtered_customer_agg["Billable rate"],
                filtered_customer_agg["Effective rate"],
                filtered_customer_agg["Revenue"]
            ],
            title=f"Customer {selected_metric} Distribution"
        )
        render_chart(fig, "customer")
    else:
        st.error(f"No customers have values greater than zero for {selected_metric}.")
    
    # Add additional metric selection for bar chart
    bar_metric_options = [
        "Hours worked",
        "Billable hours", 
        "Billability %",
        "Billable rate",
        "Effective rate",
        "Revenue"
    ]
    
    bar_selected_metric = st.selectbox(
        "Select metric for bar chart:",
        options=bar_metric_options,
        index=0,  # Default to Hours worked
        key="customer_bar_metric_selector"
    )
    
    # Customer bar chart
    # Sort customers by selected metric in descending order
    sorted_customers = customer_agg.sort_values(bar_selected_metric, ascending=False)

    # Add a slider to control number of customers to display
    if len(customer_agg) > 1:
        num_customers = st.slider(
            "Number of customers to display:",
            min_value=1,
            max_value=min(1000, len(customer_agg)),
            value=min(10, len(customer_agg)),
            step=1,
            key="customer_count_slider"
        )
        # Limit the number of customers based on slider
        limited_customers = sorted_customers.head(num_customers)
    else:
        # If only one customer, no need for slider
        limited_customers = sorted_customers

    # Create the bar chart
    fig_bar = px.bar(
        limited_customers,
        x="Customer name",
        y=bar_selected_metric,
        color=bar_selected_metric,
        color_continuous_scale="Blues",
        title=f"{bar_selected_metric} by Customer",
        custom_data=[
            limited_customers["Hours worked"],        # [0] Hours worked
            limited_customers["Billable hours"],      # [1] Billable hours
            limited_customers["Billability %"],       # [2] Billability %
            limited_customers["Number of projects"],  # [3] Number of projects
            limited_customers["Billable rate"],       # [4] Billable rate
            limited_customers["Effective rate"],      # [5] Effective rate
            limited_customers["Revenue"]              # [6] Revenue
        ]
    )

    # Improve layout for better readability
    fig_bar.update_layout(
        xaxis_title="",
        yaxis_title=bar_selected_metric,
        xaxis={'categoryorder':'total descending'}
    )

    # Render the chart (this will apply styling from chart_styles)
    render_chart(fig_bar, "customer")

    # Display customer data table with all metrics
    st.subheader("Customer Data Table")

    # Sort by hours worked in descending order
    sorted_customer_agg = customer_agg.sort_values("Hours worked", ascending=False)

    # Reorder columns for better presentation
    sorted_customer_agg = sorted_customer_agg[[ 'Customer number', 'Customer name', 
                                            'Number of projects',
                                            'Hours worked', 'Billable hours', 
                                            'Non-billable hours', 'Billability %',
                                            'Revenue', 'Billable rate', 'Effective rate']]

    # Use the column configuration from chart_styles
    from utils.chart_styles import create_column_config
    
    # Display the table with column configurations
    st.dataframe(
        sorted_customer_agg,
        use_container_width=True,
        hide_index=True,
        column_config=create_column_config(sorted_customer_agg)
    )
# people_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px

def render_people_tab(filtered_df, aggregate_by_person, render_chart, get_category_colors):
    """
    Renders the people analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_person: Function to aggregate data by person
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    #st.subheader("People Analysis")
    
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
        key="people_metric_selector"
    )
    
    # Aggregate by person
    person_agg = aggregate_by_person(filtered_df)
    
    # Filter out zero values for the selected metric
    filtered_person_agg = person_agg[person_agg[selected_metric] > 0]
    
    # Show warning if some people were filtered out
    if len(filtered_person_agg) < len(person_agg):
        st.warning(f"{len(person_agg) - len(filtered_person_agg)} people with zero {selected_metric} were excluded from visualization.")
    
    # Person treemap - using filtered data
    if not filtered_person_agg.empty:
        fig = px.treemap(
            filtered_person_agg,
            path=["Person"],
            values=selected_metric,
            color=selected_metric,
            color_continuous_scale="Blues",
            custom_data=[
                filtered_person_agg["Hours worked"],         # [0] Hours worked
                filtered_person_agg["Billable hours"],       # [1] Billable hours
                filtered_person_agg["Billability %"],        # [2] Billability %
                filtered_person_agg["Number of projects"],   # [3] Number of projects
                filtered_person_agg["Billable rate"],        # [4] Billable rate
                filtered_person_agg["Effective rate"],       # [5] Effective rate
                filtered_person_agg["Revenue"]               # [6] Revenue
            ],
            title=f"People {selected_metric} Distribution"
        )
        render_chart(fig, "person")
    else:
        st.error(f"No people have values greater than zero for {selected_metric}.")
    
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
        key="people_bar_metric_selector"
    )
    
    # Sort people by selected metric in descending order
    sorted_people = person_agg.sort_values(bar_selected_metric, ascending=False)

    # Add a slider to control number of people to display
    if len(person_agg) > 1:
        num_people = st.slider(
            "Number of people to display:",
            min_value=1,
            max_value=min(1000, len(person_agg)),
            value=min(10, len(person_agg)),
            step=1,
            key="people_count_slider"
        )
        # Limit the number of people based on slider
        limited_people = sorted_people.head(num_people)
    else:
        # If only one person, no need for slider
        limited_people = sorted_people

    # Create the bar chart
    fig_bar = px.bar(
        limited_people,
        x="Person",
        y=bar_selected_metric,
        color=bar_selected_metric,
        color_continuous_scale="Blues",
        title=f"{bar_selected_metric} by Person",
        custom_data=[
            limited_people["Hours worked"],        # [0] Hours worked
            limited_people["Billable hours"],      # [1] Billable hours
            limited_people["Billability %"],       # [2] Billability %
            limited_people["Number of projects"],  # [3] Number of projects
            limited_people["Billable rate"],       # [4] Billable rate
            limited_people["Effective rate"],      # [5] Effective rate
            limited_people["Revenue"]              # [6] Revenue
        ]
    )

    # Improve layout for better readability
    fig_bar.update_layout(
        xaxis_title="",
        yaxis_title=bar_selected_metric,
        xaxis={'categoryorder':'total descending'}
    )

    # Render the chart (this will apply styling from chart_styles)
    render_chart(fig_bar, "person")

    # Display people data table with all metrics
    st.subheader("People Data Table")
    
    # Sort by hours worked in descending order
    sorted_person_agg = person_agg.sort_values("Hours worked", ascending=False)

    # Use the column configuration from chart_styles
    from utils.chart_styles import create_column_config

    # Display the table with column configurations
    st.dataframe(
        sorted_person_agg,
        use_container_width=True,
        hide_index=True,
        column_config=create_column_config(sorted_person_agg)
    )
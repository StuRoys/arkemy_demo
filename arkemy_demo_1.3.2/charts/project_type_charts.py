# project_type_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px

def render_project_type_tab(filtered_df, aggregate_by_project_type, render_chart, get_category_colors):
    """
    Renders the project type analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_project_type: Function to aggregate data by project type
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    #st.subheader("Project Type Analysis")
    
    # Check if Project type column exists
    if "Project type" in filtered_df.columns:
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
            key="project_type_metric_selector"
        )
        
        # Aggregate by project type
        project_type_agg = aggregate_by_project_type(filtered_df)
        
        # Filter out zero values for the selected metric
        filtered_project_type_agg = project_type_agg[project_type_agg[selected_metric] > 0]
        
        # Show warning if some project types were filtered out
        if len(filtered_project_type_agg) < len(project_type_agg):
            st.warning(f"{len(project_type_agg) - len(filtered_project_type_agg)} project types with zero {selected_metric} were excluded from visualization.")
        
        # Project type treemap - using filtered data
        if not filtered_project_type_agg.empty:
            fig = px.treemap(
                filtered_project_type_agg,
                path=["Project type"],
                values=selected_metric,
                color=selected_metric,
                color_continuous_scale="Greens",
                custom_data=[
                    filtered_project_type_agg["Hours worked"],        # [0] Hours worked
                    filtered_project_type_agg["Billable hours"],      # [1] Billable hours
                    filtered_project_type_agg["Billability %"],       # [2] Billability %
                    filtered_project_type_agg["Number of projects"],  # [3] Number of projects
                    filtered_project_type_agg["Billable rate"],       # [4] Billable rate
                    filtered_project_type_agg["Effective rate"],      # [5] Effective rate
                    filtered_project_type_agg["Revenue"]              # [6] Revenue
                ],
                title=f"Project Type {selected_metric} Distribution"
            )
            render_chart(fig, "project_type")
        else:
            st.error(f"No project types have values greater than zero for {selected_metric}.")
        
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
            key="project_type_bar_metric_selector"
        )
        
        # Sort project types by selected metric in descending order
        sorted_project_types = project_type_agg.sort_values(bar_selected_metric, ascending=False)

        # Add a slider to control number of project types to display
        if len(project_type_agg) > 1:
            num_project_types = st.slider(
                "Number of project types to display:",
                min_value=1,
                max_value=min(1000, len(project_type_agg)),
                value=min(10, len(project_type_agg)),
                step=1,
                key="project_type_count_slider"
            )
            # Limit the number of project types based on slider
            limited_project_types = sorted_project_types.head(num_project_types)
        else:
            # If only one project type, no need for slider
            limited_project_types = sorted_project_types

        # Create the bar chart
        fig_bar = px.bar(
            limited_project_types,
            x="Project type",
            y=bar_selected_metric,
            color=bar_selected_metric,
            color_continuous_scale="Greens",
            title=f"{bar_selected_metric} by Project Type",
            custom_data=[
                limited_project_types["Hours worked"],        # [0] Hours worked
                limited_project_types["Billable hours"],      # [1] Billable hours
                limited_project_types["Billability %"],       # [2] Billability %
                limited_project_types["Number of projects"],  # [3] Number of projects
                limited_project_types["Billable rate"],       # [4] Billable rate
                limited_project_types["Effective rate"],      # [5] Effective rate
                limited_project_types["Revenue"]              # [6] Revenue
            ]
        )

        # Improve layout for better readability
        fig_bar.update_layout(
            xaxis_title="",
            yaxis_title=bar_selected_metric,
            xaxis={'categoryorder':'total descending'}
        )

        # Render the chart (this will apply styling from chart_styles)
        render_chart(fig_bar, "project_type")

        # Display project type data table with all metrics
        st.subheader("Project Type Data Table")
        
        # Sort by hours worked in descending order
        sorted_project_type_agg = project_type_agg.sort_values("Hours worked", ascending=False)

        # Use the column configuration from chart_styles
        from utils.chart_styles import create_column_config

        # Display the table with column configurations
        st.dataframe(
            sorted_project_type_agg,
            use_container_width=True,
            hide_index=True,
            column_config=create_column_config(sorted_project_type_agg)
        )
    else:
        st.warning("Project type information is not available in the data.")
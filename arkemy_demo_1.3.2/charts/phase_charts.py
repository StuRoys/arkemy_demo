# phase_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px

def render_phase_tab(filtered_df, aggregate_by_phase, render_chart, get_category_colors):
    """
    Renders the phase analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_phase: Function to aggregate data by phase
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    #st.subheader("Phase Analysis")
    
    # Check if Phase column exists
    if "Phase" in filtered_df.columns:
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
            key="phase_metric_selector"
        )
        
        # Aggregate by phase
        phase_agg = aggregate_by_phase(filtered_df)
        
        # Filter out zero values for the selected metric
        filtered_phase_agg = phase_agg[phase_agg[selected_metric] > 0]
        
        # Show warning if some phases were filtered out
        if len(filtered_phase_agg) < len(phase_agg):
            st.warning(f"{len(phase_agg) - len(filtered_phase_agg)} phases with zero {selected_metric} were excluded from visualization.")
        
        # Phase treemap - now using filtered data
        if not filtered_phase_agg.empty:
            fig = px.treemap(
                filtered_phase_agg,
                path=["Phase"],
                values=selected_metric,
                color=selected_metric,
                color_continuous_scale="Purples",
                custom_data=[
                    filtered_phase_agg["Hours worked"],        # [0] Hours worked
                    filtered_phase_agg["Billable hours"],      # [1] Billable hours
                    filtered_phase_agg["Billability %"],       # [2] Billability %
                    filtered_phase_agg["Number of projects"],  # [3] Number of projects
                    filtered_phase_agg["Billable rate"],       # [4] Billable rate
                    filtered_phase_agg["Effective rate"],      # [5] Effective rate
                    filtered_phase_agg["Revenue"]              # [6] Revenue
                ],
                title=f"Phase {selected_metric} Distribution"
            )
            render_chart(fig, "phase")
        else:
            st.error(f"No phases have values greater than zero for {selected_metric}.")
        
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
            key="phase_bar_metric_selector"
        )
        
        # Sort phases by selected metric in descending order
        sorted_phases = phase_agg.sort_values(bar_selected_metric, ascending=False)

        # Add a slider to control number of phases to display
        if len(phase_agg) > 1:
            num_phases = st.slider(
                "Number of phases to display:",
                min_value=1,
                max_value=min(1000, len(phase_agg)),
                value=min(10, len(phase_agg)),
                step=1,
                key="phase_count_slider"
            )
            # Limit the number of phases based on slider
            limited_phases = sorted_phases.head(num_phases)
        else:
            # If only one phase, no need for slider
            limited_phases = sorted_phases

        # Create the bar chart
        fig_bar = px.bar(
            limited_phases,
            x="Phase",
            y=bar_selected_metric,
            color=bar_selected_metric,
            color_continuous_scale="Purples",
            title=f"{bar_selected_metric} by Phase",
            custom_data=[
                limited_phases["Hours worked"],        # [0] Hours worked
                limited_phases["Billable hours"],      # [1] Billable hours
                limited_phases["Billability %"],       # [2] Billability %
                limited_phases["Number of projects"],  # [3] Number of projects
                limited_phases["Billable rate"],       # [4] Billable rate
                limited_phases["Effective rate"],      # [5] Effective rate
                limited_phases["Revenue"]              # [6] Revenue
            ]
        )

        # Improve layout for better readability
        fig_bar.update_layout(
            xaxis_title="",
            yaxis_title=bar_selected_metric,
            xaxis={'categoryorder':'total descending'}
        )

        # Render the chart (this will apply styling from chart_styles)
        render_chart(fig_bar, "phase")

        # Display phase data table with all metrics
        st.subheader("Phase Data Table")
        
        # Sort by hours worked in descending order
        sorted_phase_agg = phase_agg.sort_values("Hours worked", ascending=False)

        # Use the column configuration from chart_styles
        from utils.chart_styles import create_column_config

        # Display the table with column configurations
        st.dataframe(
            sorted_phase_agg,
            use_container_width=True,
            hide_index=True,
            column_config=create_column_config(sorted_phase_agg)
        )
    else:
        st.warning("Phase information is not available in the data.")
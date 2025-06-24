# activity_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.chart_helpers import create_standardized_customdata

def render_activity_tab(filtered_df, aggregate_by_activity, render_chart, get_category_colors):
    """
    Renders the activity analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_activity: Function to aggregate data by activity
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    #st.subheader("Activity Analysis")
    
    # Check if Activity column exists
    if "Activity" in filtered_df.columns:
        # Add metric selection dropdown
        metric_options = [
            "Hours worked",
            "Billable hours", 
            "Billability %",
            "Billable rate",
            "Effective rate",
            "Revenue",
            "Total cost",
            "Total profit",
            "Profit margin %"
        ]
        
        # Create columns for horizontal alignment
        col1, col2 = st.columns(2)
        
        with col1:
            selected_metric = st.selectbox(
                "Select metric to visualize:",
                options=metric_options,
                index=0,  # Default to Hours worked
                key="activity_metric_selector"
            )
        
        with col2:
            # Add visualization type selection
            visualization_options = ["Treemap", "Bar chart"]
            
            visualization_type = st.radio(
                "Visualization type:",
                options=visualization_options,
                index=0,  # Default to Treemap
                key="activity_visualization_selector",
                horizontal=True
            )
        
        # Aggregate by activity
        activity_agg = aggregate_by_activity(filtered_df)
        
        # Filter based on selected metric - special handling for profit which can be negative
        if "profit" in selected_metric.lower():
            filtered_activity_agg = activity_agg[activity_agg[selected_metric] != 0]
        else:
            filtered_activity_agg = activity_agg[activity_agg[selected_metric] > 0]
        
        # Show warning if some activities were filtered out
        if len(filtered_activity_agg) < len(activity_agg):
            excluded_count = len(activity_agg) - len(filtered_activity_agg)
            if "profit" in selected_metric.lower():
                st.warning(f"{excluded_count} activities with zero {selected_metric} were excluded from visualization.")
            else:
                st.warning(f"{excluded_count} activities with zero {selected_metric} were excluded from visualization.")
        
        # Render visualization based on type
        if not filtered_activity_agg.empty:
            if visualization_type == "Treemap":
                # Activity treemap - using filtered data with standardized custom data
                fig = px.treemap(
                    filtered_activity_agg,
                    path=["Activity"],
                    values=selected_metric,
                    color=selected_metric,
                    color_continuous_scale="Reds",
                    custom_data=create_standardized_customdata(filtered_activity_agg),
                    title=f"Activity {selected_metric} Distribution"
                )
                render_chart(fig, "activity")
            
            elif visualization_type == "Bar chart":
                # Sort activities by selected metric in descending order
                sorted_activities = activity_agg.sort_values(selected_metric, ascending=False)

                # Add a slider to control number of activities to display
                if len(activity_agg) > 1:
                    num_activities = st.slider(
                        "Number of activities to display:",
                        min_value=1,
                        max_value=min(1000, len(activity_agg)),
                        value=min(10, len(activity_agg)),
                        step=1,
                        key="activity_count_slider"
                    )
                    # Limit the number of activities based on slider
                    limited_activities = sorted_activities.head(num_activities)
                else:
                    # If only one activity, no need for slider
                    limited_activities = sorted_activities

                # Create the bar chart with standardized custom data
                fig_bar = px.bar(
                    limited_activities,
                    x="Activity",
                    y=selected_metric,
                    color=selected_metric,
                    color_continuous_scale="Reds",
                    title=f"{selected_metric} by Activity",
                    custom_data=create_standardized_customdata(limited_activities)
                )

                # Improve layout for better readability
                fig_bar.update_layout(
                    xaxis_title="",
                    yaxis_title=selected_metric,
                    xaxis={'categoryorder':'total descending'}
                )

                # Render the chart (this will apply styling from chart_styles)
                render_chart(fig_bar, "activity")
        else:
            if "profit" in selected_metric.lower():
                st.error(f"No activities have non-zero values for {selected_metric}.")
            else:
                st.error(f"No activities have values greater than zero for {selected_metric}.")

        # Display activity data table with all metrics
        st.subheader("Activity Data Table")
        
        # Sort by hours worked in descending order
        sorted_activity_agg = activity_agg.sort_values("Hours worked", ascending=False)

        # Use the column configuration from chart_styles
        from utils.chart_styles import create_column_config

        # Display the table with column configurations
        st.dataframe(
            sorted_activity_agg,
            use_container_width=True,
            hide_index=True,
            column_config=create_column_config(sorted_activity_agg)
        )
    else:
        st.warning("Activity information is not available in the data.")
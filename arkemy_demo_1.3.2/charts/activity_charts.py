# activity_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px

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
            "Revenue"
        ]
        
        selected_metric = st.selectbox(
            "Select metric to visualize:",
            options=metric_options,
            index=0,  # Default to Hours worked
            key="activity_metric_selector"
        )
        
        # Aggregate by activity
        activity_agg = aggregate_by_activity(filtered_df)
        
        # Filter out zero values for the selected metric
        filtered_activity_agg = activity_agg[activity_agg[selected_metric] > 0]
        
        # Show warning if some activities were filtered out
        if len(filtered_activity_agg) < len(activity_agg):
            st.warning(f"{len(activity_agg) - len(filtered_activity_agg)} activities with zero {selected_metric} were excluded from visualization.")
        
        # Activity treemap - using filtered data
        if not filtered_activity_agg.empty:
            fig = px.treemap(
                filtered_activity_agg,
                path=["Activity"],
                values=selected_metric,
                color=selected_metric,
                color_continuous_scale="Reds",
                custom_data=[
                    filtered_activity_agg["Hours worked"],        # [0] Hours worked
                    filtered_activity_agg["Billable hours"],      # [1] Billable hours
                    filtered_activity_agg["Billability %"],       # [2] Billability %
                    filtered_activity_agg["Number of projects"],  # [3] Number of projects
                    filtered_activity_agg["Billable rate"],       # [4] Billable rate
                    filtered_activity_agg["Effective rate"],      # [5] Effective rate
                    filtered_activity_agg["Revenue"]              # [6] Revenue
                ],
                title=f"Activity {selected_metric} Distribution"
            )
            render_chart(fig, "activity")
        else:
            st.error(f"No activities have values greater than zero for {selected_metric}.")
        
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
            key="activity_bar_metric_selector"
        )
        
        # Sort activities by selected metric in descending order
        sorted_activities = activity_agg.sort_values(bar_selected_metric, ascending=False)

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

        # Create the bar chart
        fig_bar = px.bar(
            limited_activities,
            x="Activity",
            y=bar_selected_metric,
            color=bar_selected_metric,
            color_continuous_scale="Reds",
            title=f"{bar_selected_metric} by Activity",
            custom_data=[
                limited_activities["Hours worked"],        # [0] Hours worked
                limited_activities["Billable hours"],      # [1] Billable hours
                limited_activities["Billability %"],       # [2] Billability %
                limited_activities["Number of projects"],  # [3] Number of projects
                limited_activities["Billable rate"],       # [4] Billable rate
                limited_activities["Effective rate"],      # [5] Effective rate
                limited_activities["Revenue"]              # [6] Revenue
            ]
        )

        # Improve layout for better readability
        fig_bar.update_layout(
            xaxis_title="",
            yaxis_title=bar_selected_metric,
            xaxis={'categoryorder':'total descending'}
        )

        # Render the chart (this will apply styling from chart_styles)
        render_chart(fig_bar, "activity")

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
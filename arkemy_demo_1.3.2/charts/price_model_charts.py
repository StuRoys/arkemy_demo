# price_model_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px

def render_price_model_tab(filtered_df, aggregate_by_price_model, render_chart, get_category_colors):
    """
    Renders the price model analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_price_model: Function to aggregate data by price model
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    
    # Check if Price model column exists
    if "Price model" in filtered_df.columns:
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
            key="price_model_metric_selector"
        )
        
        # Aggregate by price model
        price_model_agg = aggregate_by_price_model(filtered_df)
        
        # Filter out zero values for the selected metric
        filtered_price_model_agg = price_model_agg[price_model_agg[selected_metric] > 0]
        
        # Show warning if some price models were filtered out
        if len(filtered_price_model_agg) < len(price_model_agg):
            st.warning(f"{len(price_model_agg) - len(filtered_price_model_agg)} price models with zero {selected_metric} were excluded from visualization.")
        
        # Price model treemap - now using filtered data
        if not filtered_price_model_agg.empty:
            fig = px.treemap(
                filtered_price_model_agg,
                path=["Price model"],
                values=selected_metric,
                color=selected_metric,
                color_continuous_scale="YlOrRd",  # Different color scheme than Phase
                custom_data=[
                    filtered_price_model_agg["Hours worked"],        # [0] Hours worked
                    filtered_price_model_agg["Billable hours"],      # [1] Billable hours
                    filtered_price_model_agg["Billability %"],       # [2] Billability %
                    filtered_price_model_agg["Number of projects"],  # [3] Number of projects
                    filtered_price_model_agg["Billable rate"],       # [4] Billable rate
                    filtered_price_model_agg["Effective rate"],      # [5] Effective rate
                    filtered_price_model_agg["Revenue"]              # [6] Revenue
                ],
                title=f"Price Model {selected_metric} Distribution"
            )
            render_chart(fig, "price_model")
        else:
            st.error(f"No price models have values greater than zero for {selected_metric}.")
        
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
            key="price_model_bar_metric_selector"
        )
        
        # Sort price models by selected metric in descending order
        sorted_models = price_model_agg.sort_values(bar_selected_metric, ascending=False)

        # Add a slider to control number of price models to display
        if len(price_model_agg) > 1:
            num_models = st.slider(
                "Number of price models to display:",
                min_value=1,
                max_value=min(1000, len(price_model_agg)),
                value=min(10, len(price_model_agg)),
                step=1,
                key="price_model_count_slider"
            )
            # Limit the number of price models based on slider
            limited_models = sorted_models.head(num_models)
        else:
            # If only one price model, no need for slider
            limited_models = sorted_models

        # Create the bar chart
        fig_bar = px.bar(
            limited_models,
            x="Price model",
            y=bar_selected_metric,
            color=bar_selected_metric,
            color_continuous_scale="YlOrRd",  # Different color scheme than Phase
            title=f"{bar_selected_metric} by Price Model",
            custom_data=[
                limited_models["Hours worked"],        # [0] Hours worked
                limited_models["Billable hours"],      # [1] Billable hours
                limited_models["Billability %"],       # [2] Billability %
                limited_models["Number of projects"],  # [3] Number of projects
                limited_models["Billable rate"],       # [4] Billable rate
                limited_models["Effective rate"],      # [5] Effective rate
                limited_models["Revenue"]              # [6] Revenue
            ]
        )

        # Improve layout for better readability
        fig_bar.update_layout(
            xaxis_title="",
            yaxis_title=bar_selected_metric,
            xaxis={'categoryorder':'total descending'}
        )

        # Render the chart (this will apply styling from chart_styles)
        render_chart(fig_bar, "price_model")

        # Display price model data table with all metrics
        st.subheader("Price Model Data Table")
        
        # Sort by hours worked in descending order
        sorted_price_model_agg = price_model_agg.sort_values("Hours worked", ascending=False)

        # Use the column configuration from chart_styles
        from utils.chart_styles import create_column_config

        # Display the table with column configurations
        st.dataframe(
            sorted_price_model_agg,
            use_container_width=True,
            hide_index=True,
            column_config=create_column_config(sorted_price_model_agg)
        )
    else:
        st.warning("Price model information is not available in the data.")
# ui/dashboard.py
import streamlit as st
from utils.processors import calculate_summary_metrics
from utils.styles import get_tab_css
from charts.summary_kpis import display_summary_metrics
from charts.summary_charts import render_summary_tab
from charts.year_charts import render_year_tab, render_monthly_trends_chart
from charts.customer_charts import render_customer_tab
from charts.project_type_charts import render_project_type_tab
from charts.project_charts import render_project_tab
from charts.phase_charts import render_phase_tab
from charts.activity_charts import render_activity_tab
from charts.people_charts import render_people_tab
from charts.price_model_charts import render_price_model_tab

from utils.processors import (
    aggregate_by_year,
    aggregate_by_month_year,
    aggregate_by_customer,
    aggregate_by_project,
    aggregate_by_project_type,
    aggregate_by_phase,
    aggregate_by_activity,
    aggregate_by_person,
    aggregate_by_price_model
)

from utils.chart_styles import render_chart, get_category_colors
from ui.sidebar import render_sidebar_filters

def render_dashboard():
    """
    Renders the analysis dashboard after data has been loaded.
    """
    # Get data from session state
    transformed_df = st.session_state.transformed_df
    planned_df = st.session_state.transformed_planned_df if st.session_state.planned_csv_loaded else None
    
    # Check if Person type is already in the main dataframe
    has_person_type_in_main = 'Person type' in transformed_df.columns

    # Enrich dataframes with person reference data if available
    if 'person_reference_df' in st.session_state and st.session_state.person_reference_df is not None:
        person_ref_df = st.session_state.person_reference_df
        
        # Enrich main dataframe only if Person type doesn't already exist
        if not has_person_type_in_main:
            from ui.parquet_processor import cached_enrich_person_data
            transformed_df = cached_enrich_person_data(transformed_df, person_ref_df)
            st.session_state.transformed_df = transformed_df
        else:
            # Log that we're using existing Person type from main data
            st.debug.info("Using Person type from main data instead of person reference")
        
        # For planned data, also check if main data has Person type
        if planned_df is not None:
            if has_person_type_in_main and 'Person type' not in planned_df.columns:
                # If main data has Person type but planned doesn't, copy person data from main
                # Create a mapping of person to type from main data
                person_type_map = transformed_df[['Person', 'Person type']].drop_duplicates().set_index('Person')['Person type']
                # Apply mapping to planned data
                planned_df = planned_df.copy()
                planned_df['Person type'] = planned_df['Person'].map(person_type_map)
                st.session_state.transformed_planned_df = planned_df
            elif not has_person_type_in_main and 'Person type' not in planned_df.columns:
                # Fall back to reference data if needed
                from ui.parquet_processor import cached_enrich_person_data
                planned_df = cached_enrich_person_data(planned_df, person_ref_df)
                st.session_state.transformed_planned_df = planned_df

    # Enrich dataframes with project reference data if available
    if 'project_reference_df' in st.session_state and st.session_state.project_reference_df is not None:
        project_ref_df = st.session_state.project_reference_df
        
        # Enrich main dataframe
        from ui.parquet_processor import cached_enrich_project_data
        transformed_df = cached_enrich_project_data(transformed_df, project_ref_df)
        st.session_state.transformed_df = transformed_df
        
        # Enrich planned dataframe if available
        if planned_df is not None:
            planned_df = cached_enrich_project_data(planned_df, project_ref_df)
            st.session_state.transformed_planned_df = planned_df
    
    # Apply filters from the sidebar to the dataframes
    filtered_df, filtered_planned_df, filter_settings = render_sidebar_filters(transformed_df, planned_df)
    
    # Check if filtered dataframe is empty
    has_data = not filtered_df.empty
    
    if not has_data:
        st.warning("No data in selected range")
        return
        
    # Calculate summary metrics
    metrics = calculate_summary_metrics(filtered_df)

    # Apply custom tab styling
    st.markdown(get_tab_css(), unsafe_allow_html=True)
    
    # Create top-level tabs
    company_tab, project_tab, people_tab, clients_tab = st.tabs([
        "Company",
        "Projects", 
        "People",
        "Clients"
    ])

    # Tab 1: Company (formerly Summary)
    with company_tab:
        # Create sub-tabs for Company section
        kpi_tab, top10_tab, period_tab = st.tabs(["KPIs", "Top 10", "Period"])
        
        # Company > KPIs (formerly Summary content)
        with kpi_tab:
            display_summary_metrics(metrics)
            
        # Company > Top 10 (formerly Tab 2 content)
        with top10_tab:
            render_summary_tab(
                filtered_df=filtered_df,
                filter_settings=filter_settings
            )
            
        # Company > Period (formerly Tab 3 content)
        with period_tab:
            # Create sub-tabs for Period section
            year_tab, month_tab = st.tabs(["Yearly View", "Monthly Trends"])
            
            with year_tab:
                render_year_tab(
                    filtered_df=filtered_df,
                    aggregate_by_year=aggregate_by_year,
                    render_chart=render_chart,
                    get_category_colors=get_category_colors
                )
            
            with month_tab:
                render_monthly_trends_chart(
                    filtered_df=filtered_df,
                    aggregate_by_month_year=aggregate_by_month_year,
                    render_chart=render_chart,
                    get_category_colors=get_category_colors
                )

    # Tab 2: Project
    with project_tab:
        # Create sub-tabs for Project section - ADD Price Models tab here
        projects_tab, project_types_tab, price_models_tab, activities_tab, phases_tab = st.tabs([
            "Project details", "Project types", "Price models", "Activity types", "Project Phases"
        ])
        
        # Project > Projects (formerly Tab 5 content)
        with projects_tab:
            render_project_tab(
                filtered_df=filtered_df,
                aggregate_by_project=aggregate_by_project,
                render_chart=render_chart,
                get_category_colors=get_category_colors,
                planned_df=filtered_planned_df
            )
            
        # Project > Project types (formerly Tab 6 content)
        with project_types_tab:
            render_project_type_tab(
                filtered_df=filtered_df,
                aggregate_by_project_type=aggregate_by_project_type,
                render_chart=render_chart,
                get_category_colors=get_category_colors
            )
        
        # Price models tab (new)
        with price_models_tab:
            render_price_model_tab(
                filtered_df=filtered_df,
                aggregate_by_price_model=aggregate_by_price_model,
                render_chart=render_chart,
                get_category_colors=get_category_colors
            )
     
        # Project > Activities (formerly Tab 8 content)
        with activities_tab:
            render_activity_tab(
                filtered_df=filtered_df,
                aggregate_by_activity=aggregate_by_activity,
                render_chart=render_chart,
                get_category_colors=get_category_colors
            )

        # Project > Phases (formerly Tab 7 content)
        with phases_tab:
            render_phase_tab(
                filtered_df=filtered_df,
                aggregate_by_phase=aggregate_by_phase,
                render_chart=render_chart,
                get_category_colors=get_category_colors
            )            

    # Tab 3: People (formerly Tab 9)
    with people_tab:
        render_people_tab(
            filtered_df=filtered_df,
            aggregate_by_person=aggregate_by_person,
            render_chart=render_chart,
            get_category_colors=get_category_colors
        )
            
    # Tab 4: Clients (formerly Tab 4: Customers)
    with clients_tab:
        render_customer_tab(
            filtered_df=filtered_df,
            aggregate_by_customer=aggregate_by_customer,
            render_chart=render_chart,
            get_category_colors=get_category_colors
        )
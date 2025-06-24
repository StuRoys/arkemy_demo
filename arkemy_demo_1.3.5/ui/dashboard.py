# dashboard.py
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

from charts.capacity_charts import render_capacity_tab
from utils.chart_styles import render_chart, get_category_colors
from ui.sidebar import render_sidebar_filters

def render_dashboard():
    """
    Renders the analysis dashboard after data has been loaded.
    """
    # Initialize navigation session state
    if 'main_nav' not in st.session_state:
        st.session_state.main_nav = "Company"
    if 'company_nav' not in st.session_state:
        st.session_state.company_nav = "KPIs"
    if 'period_nav' not in st.session_state:
        st.session_state.period_nav = "Yearly View"
    if 'project_nav' not in st.session_state:
        st.session_state.project_nav = "Project details"
    if 'prev_project_nav' not in st.session_state:
        st.session_state.prev_project_nav = "Project details"
    if 'project_nav_counter' not in st.session_state:
        st.session_state.project_nav_counter = 0
    if 'period_nav_counter' not in st.session_state:
        st.session_state.period_nav_counter = 0
    if 'prev_period_nav' not in st.session_state:
        st.session_state.prev_period_nav = "Yearly View"
    if 'people_nav' not in st.session_state:
        st.session_state.people_nav = "Team Overview"
    if 'reports_nav' not in st.session_state:
        st.session_state.reports_nav = "Capacity"
    
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
            st.info("Using Person type from main data instead of person reference")
        
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
    
    # Check if either actual or planned dataframe has data
    has_actual_data = not filtered_df.empty
    has_planned_data = filtered_planned_df is not None and not filtered_planned_df.empty
    has_data = has_actual_data or has_planned_data

    if not has_data:
        st.warning("No data in selected range")
        return
        
    # Calculate summary metrics
    metrics = calculate_summary_metrics(filtered_df)

    # Apply custom tab styling
    st.markdown(get_tab_css(), unsafe_allow_html=True)
    
    # Main navigation
    st.markdown('<div class="nav-main">', unsafe_allow_html=True)
    main_nav = st.radio(
        "Navigation",
        ["Company", "Projects", "People", "Clients", "Reports (BETA)"],
        index=["Company", "Projects", "People", "Clients", "Reports (BETA)"].index(st.session_state.main_nav),
        key='main_nav',
        horizontal=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Company Section
    if main_nav == "Company":
        st.markdown('<div class="nav-sub">', unsafe_allow_html=True)
        company_nav = st.radio(
            "Company View",
            ["KPIs", "Top 10", "Period"],
            index=["KPIs", "Top 10", "Period"].index(st.session_state.company_nav),
            key='company_nav',
            horizontal=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if company_nav == "KPIs":
            display_summary_metrics(metrics)
            
        elif company_nav == "Top 10":
            render_summary_tab(
                filtered_df=filtered_df,
                filter_settings=filter_settings
            )
            
        elif company_nav == "Period":
            st.markdown('<div class="nav-tertiary">', unsafe_allow_html=True)
            period_nav = st.radio(
                "Period View",
                ["Yearly View", "Monthly Trends"],
                index=["Yearly View", "Monthly Trends"].index(st.session_state.period_nav),
                key='period_nav',
                horizontal=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Update session state and counter when period nav changes
            if st.session_state.prev_period_nav != period_nav:
                st.session_state.prev_period_nav = period_nav
                st.session_state.period_nav_counter = st.session_state.get('period_nav_counter', 0) + 1
                # Force a rerun to ensure clean state
                st.rerun()
            
            if period_nav == "Yearly View":
                render_year_tab(
                    filtered_df=filtered_df,
                    aggregate_by_year=aggregate_by_year,
                    render_chart=render_chart,
                    get_category_colors=get_category_colors
                )
            
            elif period_nav == "Monthly Trends":
                render_monthly_trends_chart(
                    filtered_df=filtered_df,
                    aggregate_by_month_year=aggregate_by_month_year,
                    render_chart=render_chart,
                    get_category_colors=get_category_colors
                )

    # Projects Section
    elif main_nav == "Projects":
        st.markdown('<div class="nav-sub">', unsafe_allow_html=True)
        
        # Use a different key for the radio widget to avoid conflicts
        project_nav = st.radio(
            "Project View",
            ["Project details", "Project types", "Price models", "Activity types", "Project Phases"],
            index=["Project details", "Project types", "Price models", "Activity types", "Project Phases"].index(st.session_state.project_nav),
            key='project_nav_radio',  # Different key from session state
            horizontal=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Update session state and counter when tab changes
        if st.session_state.project_nav != project_nav:
            st.session_state.prev_project_nav = st.session_state.project_nav
            st.session_state.project_nav = project_nav
            st.session_state.project_nav_counter = st.session_state.get('project_nav_counter', 0) + 1
            # Force a rerun to ensure clean state
            st.rerun()
        
        # Render content based on selected tab
        if project_nav == "Project details":
            render_project_tab(
                filtered_df=filtered_df,
                aggregate_by_project=aggregate_by_project,
                render_chart=render_chart,
                get_category_colors=get_category_colors,
                planned_df=filtered_planned_df,
                filter_settings=filter_settings
            )
            
        elif project_nav == "Project types":
            render_project_type_tab(
                filtered_df=filtered_df,
                aggregate_by_project_type=aggregate_by_project_type,
                render_chart=render_chart,
                get_category_colors=get_category_colors
            )
        
        elif project_nav == "Price models":
            render_price_model_tab(
                filtered_df=filtered_df,
                aggregate_by_price_model=aggregate_by_price_model,
                render_chart=render_chart,
                get_category_colors=get_category_colors
            )
     
        elif project_nav == "Activity types":
            render_activity_tab(
                filtered_df=filtered_df,
                aggregate_by_activity=aggregate_by_activity,
                render_chart=render_chart,
                get_category_colors=get_category_colors
            )

        elif project_nav == "Project Phases":
            render_phase_tab(
                filtered_df=filtered_df,
                aggregate_by_phase=aggregate_by_phase,
                render_chart=render_chart,
                get_category_colors=get_category_colors
            )            

    # People Section
    elif main_nav == "People":
        # Determine available people navigation options
        people_options = ["Team Overview"]
        
        # Only show sub-navigation if we have multiple options
        if len(people_options) > 1:
            st.markdown('<div class="nav-sub">', unsafe_allow_html=True)
            people_nav = st.radio(
                "People View",
                people_options,
                index=people_options.index(st.session_state.people_nav) if st.session_state.people_nav in people_options else 0,
                key='people_nav',
                horizontal=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            people_nav = "Team Overview"
        
        if people_nav == "Team Overview":
            render_people_tab(
                filtered_df=filtered_df,
                aggregate_by_person=aggregate_by_person,
                render_chart=render_chart,
                get_category_colors=get_category_colors
            )
            
    # Clients Section
    elif main_nav == "Clients":
        render_customer_tab(
            filtered_df=filtered_df,
            aggregate_by_customer=aggregate_by_customer,
            render_chart=render_chart,
            get_category_colors=get_category_colors
        )
    
    # Reports Section
    elif main_nav == "Reports (BETA)":
        st.markdown('<div class="nav-sub">', unsafe_allow_html=True)
        reports_nav = st.radio(
            "Reports View",
            ["Capacity"],
            index=["Capacity"].index(st.session_state.reports_nav),
            key='reports_nav',
            horizontal=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if reports_nav == "Capacity":
            render_capacity_tab(filtered_df=filtered_df, filter_settings=filter_settings, planned_df=filtered_planned_df)
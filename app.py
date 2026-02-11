"""
Sales Analytics Dashboard
Main Streamlit application for analyzing business-product category relationships
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

from src.data_processor import process_sales_data, merge_business_categories
from src.business_classifier import (
    create_business_mapping,
    load_business_mapping,
    get_unique_customers,
)
from src import analytics
import config

# Page configuration
st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "sales_data" not in st.session_state:
    st.session_state.sales_data = None
if "business_mapping" not in st.session_state:
    st.session_state.business_mapping = None
if "processed_data" not in st.session_state:
    st.session_state.processed_data = None


def load_sample_data():
    """Load sample data for demonstration"""
    try:
        df = process_sales_data("data/sample_sales.csv")
        mapping = load_business_mapping("data/business_mapping.csv")
        df = merge_business_categories(df, mapping)
        return df, mapping
    except Exception as e:
        st.error(f"Error loading sample data: {str(e)}")
        return None, None


def main():
    st.title("📊 Sales Analytics Dashboard")
    st.markdown(
        "Analyze which business categories purchase which product categories to identify growth opportunities"
    )

    # Sidebar for data upload and configuration
    with st.sidebar:
        st.header("📁 Data Upload")
        
        # Option to use sample data
        use_sample = st.checkbox("Use Sample Data", value=False)
        
        if use_sample:
            if st.button("Load Sample Data"):
                df, mapping = load_sample_data()
                if df is not None:
                    st.session_state.sales_data = df
                    st.session_state.business_mapping = mapping
                    st.session_state.processed_data = df
                    st.success("Sample data loaded successfully!")
                    st.rerun()
        
        # Upload sales data
        uploaded_file = st.file_uploader(
            "Upload Sales Data (CSV)",
            type=["csv"],
            help="CSV file with columns: customer_id, product_id, product_category, transaction_date, sales_amount",
        )
        
        if uploaded_file is not None:
            try:
                df = process_sales_data(uploaded_file)
                st.session_state.sales_data = df
                st.success(f"Loaded {len(df)} transactions")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
        
        # Upload business mapping
        st.header("🏢 Business Classification")
        mapping_file = st.file_uploader(
            "Upload Business Mapping (CSV)",
            type=["csv"],
            help="CSV file with columns: customer_id, business_category",
        )
        
        if mapping_file is not None:
            try:
                mapping = load_business_mapping(mapping_file)
                st.session_state.business_mapping = mapping
                st.success(f"Loaded mapping for {len(mapping)} customers")
            except Exception as e:
                st.error(f"Error loading mapping: {str(e)}")
        
        # Auto-classify option
        if st.session_state.sales_data is not None:
            if st.button("Auto-classify Businesses"):
                customers = get_unique_customers(st.session_state.sales_data)
                mapping = create_business_mapping(
                    customers,
                    mapping_file=None,
                    use_keywords=True,
                )
                st.session_state.business_mapping = mapping
                st.success(f"Classified {len(mapping)} customers")
                st.rerun()
        
        # Manual mapping interface
        if (
            st.session_state.sales_data is not None
            and st.session_state.business_mapping is None
        ):
            st.info("Upload a mapping file or use auto-classify to proceed")
    
    # Main content area
    if st.session_state.sales_data is None:
        st.info(
            "👈 Upload sales data using the sidebar, or check 'Use Sample Data' to explore with example data."
        )
        return
    
    # Merge business categories if mapping exists
    if st.session_state.business_mapping is not None:
        # Check if we need to merge (if processed_data is None or has missing categories)
        needs_merge = False
        if st.session_state.processed_data is None:
            needs_merge = True
        elif "business_category" not in st.session_state.processed_data.columns:
            needs_merge = True
        elif st.session_state.processed_data["business_category"].isna().any():
            needs_merge = True
        
        if needs_merge:
            df = merge_business_categories(
                st.session_state.sales_data, st.session_state.business_mapping
            )
            st.session_state.processed_data = df
    else:
        st.warning(
            "⚠️ Business categories not assigned. Upload a mapping file or use auto-classify in the sidebar."
        )
        df = st.session_state.sales_data.copy()
        df["business_category"] = "Unknown"
        st.session_state.processed_data = df
    
    df = st.session_state.processed_data
    
    # Filters
    st.header("🔍 Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        business_categories = ["All"] + sorted(df["business_category"].unique().tolist())
        selected_business = st.selectbox("Business Category", business_categories)
    
    with col2:
        product_categories = ["All"] + sorted(df["product_category"].unique().tolist())
        selected_product = st.selectbox("Product Category", product_categories)
    
    with col3:
        if "transaction_date" in df.columns and df["transaction_date"].notna().any():
            min_date = df["transaction_date"].min().date()
            max_date = df["transaction_date"].max().date()
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
        else:
            date_range = None
    
    # Apply filters
    filtered_df = df.copy()
    if selected_business != "All":
        filtered_df = filtered_df[filtered_df["business_category"] == selected_business]
    if selected_product != "All":
        filtered_df = filtered_df[filtered_df["product_category"] == selected_product]
    if date_range and len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df["transaction_date"].dt.date >= date_range[0])
            & (filtered_df["transaction_date"].dt.date <= date_range[1])
        ]
    
    # Overview Section
    st.header("📈 Overview")
    stats = analytics.get_summary_statistics(filtered_df)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Revenue", f"${stats['total_revenue']:,.2f}")
    with col2:
        st.metric("Total Transactions", f"{stats['total_transactions']:,}")
    with col3:
        st.metric("Unique Customers", f"{stats['unique_customers']:,}")
    with col4:
        st.metric("Product Categories", f"{stats['unique_product_categories']:,}")
    with col5:
        st.metric(
            "Avg Transaction", f"${stats['average_transaction_value']:,.2f}"
        )
    
    # Category Matrix Heatmap
    st.header("🔥 Category Matrix")
    st.markdown(
        "Heatmap showing revenue by Business Category × Product Category combination"
    )
    
    try:
        matrix = analytics.calculate_category_matrix(filtered_df)
        
        # Create heatmap
        fig = px.imshow(
            matrix,
            labels=dict(x="Product Category", y="Business Category", color="Revenue"),
            x=matrix.columns,
            y=matrix.index,
            color_continuous_scale=config.HEATMAP_COLORS,
            aspect="auto",
            text_auto=".0f",
        )
        fig.update_layout(height=600, title="Revenue Heatmap")
        st.plotly_chart(fig, use_container_width=True)
        
        # Show matrix table
        with st.expander("View Matrix Table"):
            st.dataframe(matrix, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating heatmap: {str(e)}")
    
    # Top Combinations
    st.header("🏆 Top Combinations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        metric_choice = st.selectbox(
            "Rank by", ["revenue", "count", "avg_value"], key="top_metric"
        )
    
    with col2:
        n_top = st.slider("Number of top combinations", 5, 50, 10, key="n_top")
    
    try:
        top_combinations = analytics.get_top_combinations(
            filtered_df, n=n_top, metric=metric_choice
        )
        
        # Bar chart
        if metric_choice == "revenue":
            y_col = "total_revenue"
            y_label = "Total Revenue ($)"
        elif metric_choice == "count":
            y_col = "transaction_count"
            y_label = "Transaction Count"
        else:
            y_col = "avg_value"
            y_label = "Average Value ($)"
        
        fig = px.bar(
            top_combinations,
            x="business_category",
            y=y_col,
            color="product_category",
            title=f"Top {n_top} Combinations by {metric_choice.title()}",
            labels={"business_category": "Business Category", y_col: y_label},
            barmode="group",
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Table
        st.dataframe(top_combinations, use_container_width=True)
    except Exception as e:
        st.error(f"Error calculating top combinations: {str(e)}")
    
    # Opportunity Analysis
    st.header("💡 Growth Opportunities")
    st.markdown(
        "Business categories that buy few product categories represent expansion opportunities"
    )
    
    try:
        opportunities = analytics.identify_opportunities(filtered_df)
        
        # Bar chart
        fig = px.bar(
            opportunities,
            x="business_category",
            y="opportunity_score",
            title="Opportunity Score by Business Category",
            labels={
                "business_category": "Business Category",
                "opportunity_score": "Opportunity Score",
            },
            color="opportunity_score",
            color_continuous_scale="Viridis",
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Table
        st.dataframe(opportunities, use_container_width=True)
    except Exception as e:
        st.error(f"Error calculating opportunities: {str(e)}")
    
    # Trend Analysis
    if "transaction_date" in filtered_df.columns and filtered_df["transaction_date"].notna().any():
        st.header("📅 Trends Over Time")
        
        period = st.selectbox("Time Period", ["D", "W", "M", "Q", "Y"], index=2)
        
        try:
            trends = analytics.calculate_trends(filtered_df, period=period)
            
            # Line chart
            fig = px.line(
                trends,
                x="period",
                y="sales_amount",
                color="business_category",
                line_group="product_category",
                title=f"Revenue Trends by {period} Period",
                labels={
                    "period": "Period",
                    "sales_amount": "Revenue ($)",
                    "business_category": "Business Category",
                    "product_category": "Product Category",
                },
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Pivot table view
            with st.expander("View Trend Table"):
                pivot_trends = trends.pivot_table(
                    index="period",
                    columns=["business_category", "product_category"],
                    values="sales_amount",
                    fill_value=0,
                )
                st.dataframe(pivot_trends, use_container_width=True)
        except Exception as e:
            st.error(f"Error calculating trends: {str(e)}")
    
    # Export Section
    st.header("💾 Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export category matrix
        try:
            matrix = analytics.calculate_category_matrix(filtered_df)
            csv_matrix = matrix.to_csv()
            st.download_button(
                label="Download Category Matrix (CSV)",
                data=csv_matrix,
                file_name=f"category_matrix_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        except:
            pass
    
    with col2:
        # Export top combinations
        try:
            top_combinations = analytics.get_top_combinations(filtered_df, n=100)
            csv_top = top_combinations.to_csv(index=False)
            st.download_button(
                label="Download Top Combinations (CSV)",
                data=csv_top,
                file_name=f"top_combinations_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        except:
            pass


if __name__ == "__main__":
    main()


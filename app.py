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
from src import location_analytics
from src import outreach_automation
from src import brand_product_matcher
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
            help="CSV with customer_id, business_category; optional column business_sub_category",
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
    has_sub_category = "business_sub_category" in df.columns
    n_filter_cols = 4 if has_sub_category else 3
    cols = st.columns(n_filter_cols)

    with cols[0]:
        business_categories = ["All"] + sorted(df["business_category"].unique().tolist())
        selected_business = st.selectbox("Business Category", business_categories)

    if has_sub_category:
        with cols[1]:
            if selected_business == "All":
                sub_opts = ["All"] + sorted(df["business_sub_category"].unique().tolist())
            else:
                subset = df[df["business_category"] == selected_business]
                sub_opts = ["All"] + sorted(subset["business_sub_category"].unique().tolist())
            selected_sub = st.selectbox("Business Sub-Category", sub_opts)

    with cols[2] if has_sub_category else cols[1]:
        product_categories = ["All"] + sorted(df["product_category"].unique().tolist())
        selected_product = st.selectbox("Product Category", product_categories)

    with cols[3] if has_sub_category else cols[2]:
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
    if has_sub_category and selected_sub != "All":
        filtered_df = filtered_df[filtered_df["business_sub_category"] == selected_sub]
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

    n_metrics = 6 if "unique_business_sub_categories" in stats else 5
    overview_cols = st.columns(n_metrics)
    with overview_cols[0]:
        st.metric("Total Revenue", f"${stats['total_revenue']:,.2f}")
    with overview_cols[1]:
        st.metric("Total Transactions", f"{stats['total_transactions']:,}")
    with overview_cols[2]:
        st.metric("Unique Customers", f"{stats['unique_customers']:,}")
    with overview_cols[3]:
        st.metric("Product Categories", f"{stats['unique_product_categories']:,}")
    with overview_cols[4]:
        st.metric(
            "Avg Transaction", f"${stats['average_transaction_value']:,.2f}"
        )
    if "unique_business_sub_categories" in stats:
        with overview_cols[5]:
            st.metric("Business Sub-Categories", f"{stats['unique_business_sub_categories']:,}")
    
    # Category Matrix Heatmap
    st.header("🔥 Category Matrix")
    st.markdown(
        "Heatmap showing revenue by Business Category × Product Category combination"
    )

    matrix_level = "category"
    if has_sub_category:
        matrix_level = st.radio(
            "View by",
            options=["Business Category", "Business Sub-Category"],
            index=0,
            key="matrix_level",
            horizontal=True,
        )
        matrix_level = "sub_category" if "Sub-Category" in matrix_level else "category"

    try:
        if matrix_level == "sub_category":
            matrix = analytics.calculate_sub_category_matrix(filtered_df)
            y_label = "Business Sub-Category"
        else:
            matrix = analytics.calculate_category_matrix(filtered_df)
            y_label = "Business Category"
        fig = px.imshow(
            matrix,
            labels=dict(x="Product Category", y=y_label, color="Revenue"),
            x=matrix.columns,
            y=matrix.index,
            color_continuous_scale=config.HEATMAP_COLORS,
            aspect="auto",
            text_auto=".0f",
        )
        fig.update_layout(height=600, title="Revenue Heatmap")
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("View Matrix Table"):
            st.dataframe(matrix, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating heatmap: {str(e)}")
    
    # Top Combinations
    st.header("🏆 Top Combinations")

    top_level = "category"
    if has_sub_category:
        top_level = st.radio(
            "Level",
            options=["Business Category", "Business Sub-Category"],
            index=0,
            key="top_level",
            horizontal=True,
        )
        top_level = "sub_category" if "Sub-Category" in top_level else "category"

    col1, col2 = st.columns(2)
    with col1:
        metric_choice = st.selectbox(
            "Rank by", ["revenue", "count", "avg_value"], key="top_metric"
        )
    with col2:
        n_top = st.slider("Number of top combinations", 5, 50, 10, key="n_top")

    try:
        top_combinations = analytics.get_top_combinations(
            filtered_df, n=n_top, metric=metric_choice, level=top_level
        )
        x_col = "business_sub_category" if "business_sub_category" in top_combinations.columns else "business_category"
        x_label = "Business Sub-Category" if x_col == "business_sub_category" else "Business Category"

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
            x=x_col,
            y=y_col,
            color="product_category",
            title=f"Top {n_top} Combinations by {metric_choice.title()}",
            labels={x_col: x_label, y_col: y_label},
            barmode="group",
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

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
        
        period_labels = {"D": "Day", "W": "Week", "M": "Month", "Q": "Quarter", "Y": "Year"}
        period = st.selectbox(
            "Time Period",
            ["D", "W", "M", "Q", "Y"],
            index=2,
            format_func=lambda x: period_labels[x],
        )
        
        try:
            trends = analytics.calculate_trends(filtered_df, period=period)
            
            # Line chart
            fig = px.line(
                trends,
                x="period",
                y="sales_amount",
                color="business_category",
                line_group="product_category",
                title=f"Revenue Trends by {period_labels[period]}",
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
    
    # Location-Based Recommendations
    if "location" in df.columns or ("city" in df.columns and "state" in df.columns):
        st.header("📍 Location-Based Recommendations")
        st.markdown(
            "Find similar businesses in nearby locations that might want to purchase the same products"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            business_cats = sorted(df["business_category"].unique().tolist())
            selected_biz_cat = st.selectbox(
                "Business Category",
                business_cats,
                key="loc_biz_cat"
            )
        
        with col2:
            product_cats = sorted(df["product_category"].unique().tolist())
            selected_prod_cat = st.selectbox(
                "Product Category",
                product_cats,
                key="loc_prod_cat"
            )
        
        with col3:
            # Get unique locations
            if "location" in df.columns:
                locations = sorted([str(loc) for loc in df["location"].unique() 
                                  if loc and str(loc) != "nan" and str(loc) != ""])
            elif "city" in df.columns and "state" in df.columns:
                # Create unique location combinations
                location_set = set()
                for _, row in df[["city", "state"]].drop_duplicates().iterrows():
                    city = str(row["city"]) if pd.notna(row["city"]) else ""
                    state = str(row["state"]) if pd.notna(row["state"]) else ""
                    if city and state and city != "nan" and state != "nan":
                        location_set.add(f"{city}, {state}")
                locations = sorted(list(location_set))
            else:
                locations = []
            
            selected_location = st.selectbox(
                "Location (City, State)",
                locations,
                key="loc_select"
            )
        
        if st.button("Find Similar Businesses", key="find_similar"):
            try:
                recommendations = location_analytics.find_similar_businesses_by_location(
                    df,
                    business_category=selected_biz_cat,
                    product_category=selected_prod_cat,
                    location=selected_location,
                    n_recommendations=20
                )
                
                if len(recommendations) > 0:
                    st.success(f"Found {len(recommendations)} similar businesses in nearby locations")
                    
                    # Display recommendations
                    st.dataframe(
                        recommendations[["customer_id", "location", "business_category", 
                                       "current_product_categories", "total_revenue"]],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Chart showing opportunities by location
                    if len(recommendations) > 0:
                        fig = px.bar(
                            recommendations.head(10),
                            x="location",
                            y="total_revenue",
                            color="current_product_categories",
                            title="Top Recommended Businesses by Location",
                            labels={
                                "location": "Location",
                                "total_revenue": "Total Revenue ($)",
                                "current_product_categories": "Product Categories"
                            }
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(
                        f"No similar businesses found in {selected_location}. "
                        "Try expanding your search or selecting a different location."
                    )
            except Exception as e:
                st.error(f"Error finding recommendations: {str(e)}")
        
        # Location Insights
        st.subheader("🌍 Location Insights")
        try:
            location_insights = location_analytics.get_location_insights(df)
            
            if location_insights:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Top Locations by Number of Businesses**")
                    if "top_locations" in location_insights:
                        top_locs = pd.DataFrame(
                            list(location_insights["top_locations"].items()),
                            columns=["Location", "Number of Businesses"]
                        )
                        st.dataframe(top_locs, use_container_width=True, hide_index=True)
                
                with col2:
                    st.write("**Top Locations by Revenue**")
                    if "top_sales_locations" in location_insights:
                        top_sales = pd.DataFrame(
                            list(location_insights["top_sales_locations"].items()),
                            columns=["Location", "Total Revenue"]
                        )
                        top_sales["Total Revenue"] = top_sales["Total Revenue"].apply(lambda x: f"${x:,.2f}")
                        st.dataframe(top_sales, use_container_width=True, hide_index=True)
        except Exception as e:
            st.info("Location insights not available. Make sure your data includes location information.")
    
    # Automated Outreach Section
    if "location" in df.columns or ("city" in df.columns and "state" in df.columns):
        st.header("📧 Automated Outreach & Regional Targeting")
        st.markdown(
            "Find target businesses for automated outreach based on store type, products, and regional preferences"
        )
        
        tab1, tab2, tab3, tab4 = st.tabs(["Target Finder", "Regional Analysis", "Brand Product Matcher", "Outreach Export"])
        
        with tab1:
            st.subheader("Find Target Businesses for Outreach")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                biz_cats = sorted(df["business_category"].unique().tolist())
                outreach_biz_cat = st.selectbox(
                    "Business Category to Target",
                    biz_cats,
                    key="outreach_biz"
                )
            
            with col2:
                prod_cats = sorted(df["product_category"].unique().tolist())
                outreach_prod_cat = st.selectbox(
                    "Product Category to Promote",
                    prod_cats,
                    key="outreach_prod"
                )
            
            with col3:
                # Get unique states
                if "state" in df.columns:
                    states = sorted([s for s in df["state"].unique() if s and str(s) != "nan"])
                elif "location" in df.columns:
                    states = sorted(list(set([loc.split(",")[-1].strip() for loc in df["location"].unique() if loc and "," in str(loc)])))
                else:
                    states = []
                
                outreach_state = st.selectbox(
                    "Target State (Optional)",
                    [None] + states,
                    key="outreach_state"
                )
            
            max_targets = st.slider("Maximum Targets", 10, 100, 25, key="max_targets")
            
            if st.button("Generate Outreach List", key="generate_outreach"):
                try:
                    targets = outreach_automation.generate_outreach_list(
                        df,
                        business_category=outreach_biz_cat,
                        product_category=outreach_prod_cat,
                        location_filter=outreach_state,
                        max_results=max_targets
                    )
                    
                    if len(targets) > 0:
                        st.success(f"Found {len(targets)} target businesses for outreach!")
                        
                        # Display targets
                        st.dataframe(
                            targets[["customer_id", "location", "current_products", 
                                    "recommended_product", "similar_products", "total_revenue", 
                                    "opportunity_score"]],
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Store in session state for export
                        st.session_state.outreach_targets = targets
                        
                        # Summary stats
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Targets", len(targets))
                        with col2:
                            st.metric("Avg Revenue", f"${targets['total_revenue'].mean():,.2f}")
                        with col3:
                            st.metric("Unique Locations", targets["location"].nunique())
                    else:
                        st.info("No target businesses found. Try different criteria.")
                except Exception as e:
                    st.error(f"Error generating outreach list: {str(e)}")
        
        with tab2:
            st.subheader("Regional Product Preferences")
            st.markdown("See which products are popular in different states/regions")
            
            if st.button("Analyze Regional Preferences", key="analyze_regional"):
                try:
                    regional_data = outreach_automation.analyze_regional_preferences(df)
                    
                    if regional_data and "top_products_by_state" in regional_data:
                        # Display top products by state
                        for state, products in list(regional_data["top_products_by_state"].items())[:10]:
                            with st.expander(f"📍 {state}"):
                                products_df = pd.DataFrame(products)
                                st.dataframe(
                                    products_df,
                                    use_container_width=True,
                                    hide_index=True
                                )
                        
                        # Chart: Product popularity by state
                        if "regional_data" in regional_data:
                            regional_df = regional_data["regional_data"]
                            
                            # Top states by revenue
                            top_states = regional_df.groupby("state")["total_revenue"].sum().nlargest(10)
                            
                            fig = px.bar(
                                x=top_states.index,
                                y=top_states.values,
                                title="Top States by Total Revenue",
                                labels={"x": "State", "y": "Total Revenue ($)"}
                            )
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Product category by state heatmap
                            pivot_regional = regional_df.pivot_table(
                                index="state",
                                columns="product_category",
                                values="total_revenue",
                                fill_value=0
                            )
                            
                            fig2 = px.imshow(
                                pivot_regional.head(15),
                                labels=dict(x="Product Category", y="State", color="Revenue"),
                                aspect="auto",
                                title="Product Category Revenue by State"
                            )
                            fig2.update_layout(height=600)
                            st.plotly_chart(fig2, use_container_width=True)
                except Exception as e:
                    st.error(f"Error analyzing regional preferences: {str(e)}")
        
        with tab3:
            st.subheader("Brand Product Matcher")
            st.markdown("Match Faire brand products (like Hilarious Humanitarian) with potential buyers")
            
            # Brand product upload
            st.write("**Upload Brand Products**")
            brand_file = st.file_uploader(
                "Upload Brand Products CSV",
                type=["csv"],
                help="CSV with columns: product_id, product_name, product_category, product_type",
                key="brand_upload"
            )
            
            # Or use default Hilarious Humanitarian data
            use_hilarious = st.checkbox("Use Hilarious Humanitarian Sample Data", value=True, key="use_hilarious")
            
            if brand_file is not None or use_hilarious:
                try:
                    if use_hilarious and brand_file is None:
                        brand_products = brand_product_matcher.load_brand_products("data/hilarious_humanitarian_products.csv")
                        st.success("Loaded Hilarious Humanitarian product data")
                    elif brand_file is not None:
                        # Save uploaded file temporarily
                        import tempfile
                        import os
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
                            tmp_file.write(brand_file.getvalue())
                            tmp_path = tmp_file.name
                        brand_products = brand_product_matcher.load_brand_products(tmp_path)
                        os.unlink(tmp_path)
                        st.success(f"Loaded {len(brand_products)} products from uploaded file")
                    
                    # Display brand products
                    with st.expander("View Brand Products"):
                        st.dataframe(brand_products, use_container_width=True, hide_index=True)
                    
                    # Market fit analysis
                    st.subheader("Market Fit Analysis")
                    if st.button("Analyze Market Fit", key="analyze_market_fit"):
                        try:
                            market_fit = brand_product_matcher.analyze_brand_market_fit(df, brand_products)
                            
                            st.metric("Market Fit Score", f"{market_fit['market_fit_score']:.1f}%")
                            
                            # Category breakdown
                            st.write("**Category Breakdown**")
                            for category, data in market_fit["category_breakdown"].items():
                                with st.expander(f"📦 {category}"):
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Buyers", f"{data['num_buyers']:,}")
                                    with col2:
                                        st.metric("Total Revenue", f"${data['total_revenue']:,.2f}")
                                    with col3:
                                        st.metric("Avg Transaction", f"${data['avg_transaction']:,.2f}")
                                    
                                    if data["top_business_types"]:
                                        st.write("**Top Business Types**")
                                        st.json(data["top_business_types"])
                        except Exception as e:
                            st.error(f"Error analyzing market fit: {str(e)}")
                    
                    # Find matches
                    st.subheader("Find Potential Buyers")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        match_states = sorted([s for s in df["state"].unique() if s and str(s) != "nan"]) if "state" in df.columns else []
                        match_state = st.selectbox(
                            "Filter by State (Optional)",
                            [None] + match_states,
                            key="match_state"
                        )
                    
                    with col2:
                        match_biz_cats = sorted(df["business_category"].unique().tolist())
                        match_biz_cat = st.selectbox(
                            "Filter by Business Category (Optional)",
                            [None] + match_biz_cats,
                            key="match_biz_cat"
                        )
                    
                    max_matches = st.slider("Maximum Matches", 10, 100, 30, key="max_matches")
                    
                    if st.button("Find Potential Buyers", key="find_brand_buyers"):
                        try:
                            matches = brand_product_matcher.generate_brand_outreach_list(
                                df,
                                brand_products,
                                location_filter=match_state,
                                business_category_filter=match_biz_cat,
                                max_results=max_matches
                            )
                            
                            if len(matches) > 0:
                                st.success(f"Found {len(matches)} potential buyers for brand products!")
                                
                                # Display matches
                                st.dataframe(
                                    matches[["customer_id", "location", "business_category", 
                                            "brand_category", "recommended_brand_products",
                                            "current_products", "opportunity_score"]],
                                    use_container_width=True,
                                    hide_index=True
                                )
                                
                                # Store for export
                                st.session_state.brand_matches = matches
                                
                                # Summary
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total Matches", len(matches))
                                with col2:
                                    st.metric("Unique Locations", matches["location"].nunique())
                                with col3:
                                    st.metric("Avg Opportunity Score", f"{matches['opportunity_score'].mean():.1f}")
                            else:
                                st.info("No matches found. Try adjusting filters or check if brand products match your sales data categories.")
                        except Exception as e:
                            st.error(f"Error finding matches: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
                
                except Exception as e:
                    st.error(f"Error loading brand products: {str(e)}")
            else:
                st.info("Upload a brand products CSV or use the Hilarious Humanitarian sample data")
        
        with tab4:
            st.subheader("Export Outreach Data")
            
            if "outreach_targets" in st.session_state and len(st.session_state.outreach_targets) > 0:
                targets = st.session_state.outreach_targets
                
                st.info(f"Ready to export {len(targets)} target businesses")
                
                export_format = st.selectbox(
                    "Export Format",
                    ["CSV", "JSON", "Email Templates"],
                    key="export_format"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if export_format == "CSV":
                        csv_data = targets.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv_data,
                            file_name=f"outreach_targets_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    elif export_format == "JSON":
                        json_data = targets.to_json(orient="records", indent=2)
                        st.download_button(
                            label="Download JSON",
                            data=json_data,
                            file_name=f"outreach_targets_{datetime.now().strftime('%Y%m%d')}.json",
                            mime="application/json"
                        )
                    else:  # Email Templates
                        email_data = outreach_automation.export_outreach_data(targets, format="email_list")
                        st.download_button(
                            label="Download Email Templates",
                            data=email_data,
                            file_name=f"email_templates_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain"
                        )
                
                with col2:
                    # Preview email template
                    if export_format == "Email Templates" and len(targets) > 0:
                        sample_email = outreach_automation.generate_email_template(
                            targets.iloc[0]["customer_id"],
                            targets.iloc[0]["business_category"],
                            targets.iloc[0]["recommended_product"],
                            targets.iloc[0]["location"],
                            targets.iloc[0]["current_products"],
                            targets.iloc[0]["similar_products"]
                        )
                        st.text_area("Sample Email Template", sample_email, height=200)
            else:
                st.info("Generate an outreach list first using the 'Target Finder' or 'Brand Product Matcher' tab")
            
            # Brand matches export
            if "brand_matches" in st.session_state and len(st.session_state.brand_matches) > 0:
                st.divider()
                st.subheader("Export Brand Matches")
                
                brand_matches = st.session_state.brand_matches
                st.info(f"Ready to export {len(brand_matches)} brand product matches")
                
                brand_export_format = st.selectbox(
                    "Export Format",
                    ["CSV", "JSON"],
                    key="brand_export_format"
                )
                
                if brand_export_format == "CSV":
                    brand_csv = brand_matches.to_csv(index=False)
                    st.download_button(
                        label="Download Brand Matches CSV",
                        data=brand_csv,
                        file_name=f"brand_matches_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key="download_brand_csv"
                    )
                else:
                    brand_json = brand_matches.to_json(orient="records", indent=2)
                    st.download_button(
                        label="Download Brand Matches JSON",
                        data=brand_json,
                        file_name=f"brand_matches_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json",
                        key="download_brand_json"
                    )
    
    # Brand-Specific Matching Section
    st.header("🎯 Brand-Specific Product Matching")
    st.markdown(
        "Match your brand's products with businesses that would be perfect customers"
    )
    
    # Load brand products if available
    brand_file = "data/hilarious_humanitarian_products.csv"
    brand_products_available = False
    
    try:
        import os
        if os.path.exists(brand_file):
            brand_products = brand_matching.load_brand_products(brand_file)
            brand_products_available = True
            st.success(f"✅ Loaded {len(brand_products)} products from Hilarious Humanitarian")
    except Exception as e:
        st.info("💡 Upload a brand product CSV file to use brand-specific matching")
    
    if brand_products_available:
        tab1, tab2, tab3 = st.tabs(["Find Matches", "Regional Fit", "Export Matches"])
        
        with tab1:
            st.subheader("Find Businesses for Your Brand")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Business categories to target
                all_biz_cats = sorted(df["business_category"].unique().tolist())
                selected_biz_cats = st.multiselect(
                    "Business Categories to Target",
                    all_biz_cats,
                    default=["Gift Shop", "Bookstore & Gifts", "Stationery Store"] if "Gift Shop" in all_biz_cats else all_biz_cats[:3],
                    key="brand_biz_cats"
                )
            
            with col2:
                # Location filter
                if "state" in df.columns:
                    states = sorted([s for s in df["state"].unique() if s and str(s) != "nan"])
                elif "location" in df.columns:
                    states = sorted(list(set([loc.split(",")[-1].strip() for loc in df["location"].unique() if loc and "," in str(loc)])))
                else:
                    states = []
                
                brand_location = st.selectbox(
                    "Target State (Optional)",
                    [None] + states,
                    key="brand_location"
                )
            
            brand_max_results = st.slider("Maximum Matches", 10, 100, 30, key="brand_max")
            
            if st.button("Find Brand Matches", key="find_brand_matches"):
                try:
                    matches = brand_matching.find_businesses_for_brand(
                        df,
                        brand_products,
                        business_categories=selected_biz_cats if selected_biz_cats else None,
                        location_filter=brand_location,
                        min_match_score=0.3
                    )
                    
                    if len(matches) > 0:
                        st.success(f"Found {len(matches)} businesses that match your brand!")
                        
                        # Display matches
                        display_cols = ["customer_id", "business_category", "location", 
                                      "current_product_categories", "match_score", 
                                      "recommended_products", "total_revenue"]
                        st.dataframe(
                            matches[display_cols].head(brand_max_results),
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Store in session state
                        st.session_state.brand_matches = matches.head(brand_max_results)
                        
                        # Summary metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Matches", len(matches))
                        with col2:
                            st.metric("Avg Match Score", f"{matches['match_score'].mean():.2%}")
                        with col3:
                            st.metric("Unique Locations", matches["location"].nunique())
                        
                        # Chart: Match score distribution
                        fig = px.histogram(
                            matches.head(brand_max_results),
                            x="match_score",
                            nbins=20,
                            title="Match Score Distribution",
                            labels={"match_score": "Match Score", "count": "Number of Businesses"}
                        )
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No matches found. Try adjusting your criteria.")
                except Exception as e:
                    st.error(f"Error finding matches: {str(e)}")
        
        with tab2:
            st.subheader("Regional Fit Analysis")
            st.markdown("See which states/regions are the best fit for your brand")
            
            if st.button("Analyze Regional Fit", key="analyze_regional_fit"):
                try:
                    regional_fit = brand_matching.analyze_brand_regional_fit(df, brand_products)
                    
                    if regional_fit:
                        # Create DataFrame for display
                        fit_data = []
                        for state, data in regional_fit.items():
                            fit_data.append({
                                "State": state,
                                "Total Businesses": data["total_businesses"],
                                "Businesses with Overlap": data["businesses_with_overlap"],
                                "Category Overlap": data["category_overlap"],
                                "Fit Score": f"{data['fit_score']:.2%}"
                            })
                        
                        fit_df = pd.DataFrame(fit_data)
                        # Sort by fit score (convert percentage to float for sorting)
                        fit_df["Fit_Score_Num"] = fit_df["Fit Score"].str.rstrip('%').astype('float') / 100
                        fit_df = fit_df.sort_values("Fit_Score_Num", ascending=False).drop("Fit_Score_Num", axis=1)
                        
                        st.dataframe(fit_df.head(20), use_container_width=True, hide_index=True)
                        
                        # Chart: Top states by fit score
                        top_states = fit_df.head(15).copy()
                        top_states["Fit_Score_Num"] = top_states["Fit Score"].str.rstrip('%').astype('float')
                        fig = px.bar(
                            top_states,
                            x="State",
                            y="Fit_Score_Num",
                            title="Top States by Brand Fit Score",
                            labels={"Fit_Score_Num": "Fit Score (%)"}
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Regional analysis not available. Make sure your data includes location information.")
                except Exception as e:
                    st.error(f"Error analyzing regional fit: {str(e)}")
        
        with tab3:
            st.subheader("Export Brand Matches")
            
            if "brand_matches" in st.session_state and len(st.session_state.brand_matches) > 0:
                matches = st.session_state.brand_matches
                
                st.info(f"Ready to export {len(matches)} brand matches")
                
                export_format = st.selectbox(
                    "Export Format",
                    ["CSV", "JSON"],
                    key="brand_export_format"
                )
                
                if export_format == "CSV":
                    csv_data = matches.to_csv(index=False)
                    st.download_button(
                        label="Download Matches (CSV)",
                        data=csv_data,
                        file_name=f"brand_matches_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    json_data = matches.to_json(orient="records", indent=2)
                    st.download_button(
                        label="Download Matches (JSON)",
                        data=json_data,
                        file_name=f"brand_matches_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
                
                # Show brand product summary
                st.subheader("Brand Products Summary")
                st.dataframe(
                    brand_products[["product_name", "product_category"]],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Find brand matches first using the 'Find Matches' tab")
    
    # Export Section
    st.header("💾 Export Results")

    col1, col2 = st.columns(2)
    with col1:
        try:
            if matrix_level == "sub_category":
                matrix_export = analytics.calculate_sub_category_matrix(filtered_df)
            else:
                matrix_export = analytics.calculate_category_matrix(filtered_df)
            csv_matrix = matrix_export.to_csv()
            st.download_button(
                label="Download Category Matrix (CSV)",
                data=csv_matrix,
                file_name=f"category_matrix_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        except Exception:
            pass

    with col2:
        try:
            top_export = analytics.get_top_combinations(
                filtered_df, n=100, level=top_level
            )
            csv_top = top_export.to_csv(index=False)
            st.download_button(
                label="Download Top Combinations (CSV)",
                data=csv_top,
                file_name=f"top_combinations_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        except Exception:
            pass


if __name__ == "__main__":
    main()


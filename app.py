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
from src import product_level_analytics
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
        """
        **Welcome!** This dashboard helps you understand which types of businesses buy which products, 
        so you can target the right customers and grow your sales.
        
        👉 **Start by loading your sales data** in the sidebar, or use the sample data to explore.
        """
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
        st.subheader("🏢 Business Types (Optional)")
        st.markdown("""
        **Why this matters:** Knowing what type of store each customer is helps you 
        find similar stores to target.
        """)
        
        mapping_file = st.file_uploader(
            "📋 Upload Business Types (CSV)",
            type=["csv"],
            help="A file matching customer names to their business type (e.g., 'Gift Shop', 'Bookstore')"
        )
        
        if mapping_file is not None:
            try:
                mapping = load_business_mapping(mapping_file)
                st.session_state.business_mapping = mapping
                st.success(f"✅ Loaded business types for {len(mapping)} customers")
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")
        
        # Auto-classify option
        if st.session_state.sales_data is not None:
            st.markdown("**Don't have business types?**")
            if st.button("🤖 Auto-Detect Business Types", help="We'll guess based on customer names"):
                customers = get_unique_customers(st.session_state.sales_data)
                mapping = create_business_mapping(
                    customers,
                    mapping_file=None,
                    use_keywords=True,
                )
                st.session_state.business_mapping = mapping
                st.success(f"✅ Classified {len(mapping)} customers automatically")
                st.rerun()
        
        # Manual mapping interface
        if (
            st.session_state.sales_data is not None
            and st.session_state.business_mapping is None
        ):
            st.info("💡 Tip: Upload business types or click 'Auto-Detect' to unlock more features")
    
    # Main content area
    if st.session_state.sales_data is None:
        st.info(
            """
            👈 **Get Started:** 
            - Check "Try with Sample Data" in the sidebar to see how it works, OR
            - Upload your own sales data file
            
            Once data is loaded, you'll see insights about which businesses buy which products!
            """
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
    st.header("🔍 Filter Your Data")
    st.markdown("**Narrow down what you're looking at** - Focus on specific store types, products, or time periods")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        business_categories = ["All"] + sorted(df["business_category"].unique().tolist())
        selected_business = st.selectbox(
            "🏪 Store Type", 
            business_categories,
            help="Filter to see only specific types of stores (e.g., just Gift Shops)"
        )
    
    with col2:
        product_categories = ["All"] + sorted(df["product_category"].unique().tolist())
        selected_product = st.selectbox(
            "📦 Product Category", 
            product_categories,
            help="Filter to see only specific products (e.g., just Women's accessories)"
        )
    
    with col3:
        if "transaction_date" in df.columns and df["transaction_date"].notna().any():
            min_date = df["transaction_date"].min().date()
            max_date = df["transaction_date"].max().date()
            date_range = st.date_input(
                "📅 Time Period",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                help="See sales from a specific time period"
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
    st.header("📈 Your Sales Overview")
    st.markdown("**Quick snapshot of your business** - See how you're doing overall")
    
    stats = analytics.get_summary_statistics(filtered_df)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("💰 Total Revenue", f"${stats['total_revenue']:,.2f}", help="All sales combined")
    with col2:
        st.metric("🛒 Total Orders", f"{stats['total_transactions']:,}", help="Number of purchases")
    with col3:
        st.metric("👥 Customers", f"{stats['unique_customers']:,}", help="Unique businesses buying from you")
    with col4:
        st.metric("📦 Product Types", f"{stats['unique_product_categories']:,}", help="Different product categories sold")
    with col5:
        st.metric(
            "💵 Avg Order Size", f"${stats['average_transaction_value']:,.2f}", help="Average amount per purchase"
        )
    
    # Category Matrix Heatmap
    st.header("🔥 Which Stores Buy Which Products?")
    st.markdown("""
    **What this shows:** This heatmap shows you which types of businesses buy which product categories.
    
    **How to read it:**
    - 🔴 **Dark red** = High sales (lots of money)
    - 🟡 **Yellow** = Medium sales
    - ⚪ **White** = Low or no sales
    
    **Why it matters:** Find your best matches! If "Gift Shops" buy lots of "Women's accessories", 
    you should target more Gift Shops for those products.
    """)
    
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
    st.header("🏆 Your Best Seller Combinations")
    st.markdown("""
    **What this shows:** The best matches between business types and products.
    
    **Use this to:** Focus your sales efforts on combinations that already work well!
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        metric_choice = st.selectbox(
            "Sort by", 
            ["revenue", "count", "avg_value"],
            format_func=lambda x: {"revenue": "💰 Total Sales", "count": "📊 Number of Orders", "avg_value": "💵 Average Order Size"}[x],
            key="top_metric",
            help="Choose how to rank the combinations"
        )
    
    with col2:
        n_top = st.slider("Show top", 5, 50, 10, key="n_top", help="How many top combinations to display")
    
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
    st.header("💡 Where to Grow Next")
    st.markdown("""
    **What this shows:** Business types that buy fewer products from you = **big opportunities!**
    
    **Example:** If "Bookstores" only buy 2 product types but you sell 5, you can sell them 3 more!
    
    **Use this to:** Target businesses that could buy more from you.
    """)
    
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
        
        with st.expander("View Opportunities Table"):
            st.dataframe(opportunities, use_container_width=True)
    except Exception as e:
        st.error(f"Error calculating opportunities: {str(e)}")
    
    # Trend Analysis
    if "transaction_date" in filtered_df.columns and filtered_df["transaction_date"].notna().any():
        st.header("📅 Sales Trends Over Time")
        st.markdown("""
        **What this shows:** How your sales change over time by business type and product.
        
        **Use this to:** See seasonal patterns and plan for busy/slow periods.
        """)
        
        period = st.selectbox(
            "View by", 
            ["D", "W", "M", "Q", "Y"], 
            index=2,
            format_func=lambda x: {"D": "Daily", "W": "Weekly", "M": "Monthly", "Q": "Quarterly", "Y": "Yearly"}[x],
            help="Choose how to group the time periods"
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
        st.header("📍 Find Similar Stores Nearby")
        st.markdown("""
        **What this does:** Finds stores like your existing customers in the same area.
        
        **Example:** If "Gift Shop in New York" buys your products, find other Gift Shops in New York!
        
        **Why it works:** Stores in the same area often have similar customers and needs.
        """)
        
        st.markdown("**Choose what to search for:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            business_cats = sorted(df["business_category"].unique().tolist())
            selected_biz_cat = st.selectbox(
                "🏪 What type of store?",
                business_cats,
                key="loc_biz_cat",
                help="Example: Gift Shop, Bookstore"
            )
        
        with col2:
            product_cats = sorted(df["product_category"].unique().tolist())
            selected_prod_cat = st.selectbox(
                "📦 What product?",
                product_cats,
                key="loc_prod_cat",
                help="Example: Women's accessories"
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
                "📍 Which location?",
                locations,
                key="loc_select",
                help="Pick a city/state to search in"
            )
        
        st.divider()
        if st.button("🔍 Find Similar Stores", key="find_similar", type="primary"):
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
    
    # Specific Product Analysis Section
    if "product_name" in df.columns and ("location" in df.columns or ("city" in df.columns and "state" in df.columns)):
        st.header("🛍️ Specific Product Analysis by Area")
        st.markdown("""
        **What this does:** See which **specific products** sell best in which areas, then find stores in those areas that should buy them too.
        
        **Example:** "Tote Bag" sells great in California → Find other stores in California that don't buy Tote Bags yet!
        """)
        
        tab1, tab2, tab3 = st.tabs(["Product Popularity by Area", "Find Stores for Product", "Area Product Recommendations"])
        
        with tab1:
            st.subheader("📊 Which Products Sell Where?")
            st.markdown("**Pick a product to see where it's most popular**")
            
            # Get unique products
            products = sorted(df["product_name"].unique().tolist())
            
            col1, col2 = st.columns(2)
            
            with col1:
                selected_product = st.selectbox(
                    "🛍️ Choose a Product",
                    products,
                    key="product_popularity",
                    help="Select a product to see where it sells best"
                )
            
            with col2:
                area_filter = st.selectbox(
                    "📍 Filter by Area (Optional)",
                    [None] + sorted([s for s in df["state"].unique() if s and str(s) != "nan"]) if "state" in df.columns else [None],
                    key="product_area_filter",
                    help="Leave blank to see all areas"
                )
            
            if st.button("🔍 Analyze Product Popularity", key="analyze_product_pop", type="primary"):
                try:
                    analysis = product_level_analytics.analyze_product_popularity_by_area(
                        df,
                        product_name=selected_product,
                        area=area_filter
                    )
                    
                    if "error" not in analysis:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("💰 Total Sales", f"${analysis['total_sales']:,.2f}")
                        with col2:
                            st.metric("🛒 Total Orders", f"{analysis['total_orders']:,}")
                        with col3:
                            st.metric("🏪 Stores Buying", f"{analysis['unique_stores']:,}")
                        
                        st.markdown(f"**📍 Top Areas for '{selected_product}':**")
                        
                        if analysis["top_areas"]:
                            top_areas_df = pd.DataFrame(analysis["top_areas"])
                            st.dataframe(
                                top_areas_df,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "location": "Location",
                                    "total_revenue": st.column_config.NumberColumn("Total Sales", format="$%.2f"),
                                    "num_orders": "Orders",
                                    "avg_order": st.column_config.NumberColumn("Avg Order", format="$%.2f"),
                                    "num_stores": "Stores"
                                }
                            )
                            
                            # Chart
                            fig = px.bar(
                                top_areas_df.head(10),
                                x="location",
                                y="total_revenue",
                                title=f"Sales of '{selected_product}' by Location",
                                labels={"location": "Location", "total_revenue": "Total Sales ($)"}
                            )
                            fig.update_layout(height=400, xaxis_tickangle=-45)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No area data available for this product")
                    else:
                        st.warning(analysis["error"])
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with tab2:
            st.subheader("🎯 Find Stores That Should Buy This Product")
            st.markdown("""
            **What this does:** Finds stores in areas where a product is popular, but they don't buy it yet.
            
            **Example:** "Tote Bag" sells well in New York → Find stores in New York that don't buy Tote Bags!
            """)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                product_to_sell = st.selectbox(
                    "🛍️ Product to Sell",
                    sorted(df["product_name"].unique().tolist()),
                    key="product_to_sell"
                )
            
            with col2:
                target_area = st.selectbox(
                    "📍 Target Area",
                    [None] + sorted([s for s in df["state"].unique() if s and str(s) != "nan"]) if "state" in df.columns else [None],
                    key="target_area",
                    help="Pick an area where this product sells well"
                )
            
            with col3:
                target_biz_type = st.selectbox(
                    "🏪 Store Type (Optional)",
                    [None] + sorted(df["business_category"].unique().tolist()),
                    key="target_biz_type"
                )
            
            max_stores = st.slider("How many stores to find?", 5, 50, 15, key="max_product_stores")
            
            if st.button("🔍 Find Target Stores", key="find_product_stores", type="primary"):
                try:
                    with st.spinner("Finding stores that should buy this product..."):
                        stores = product_level_analytics.find_stores_for_specific_product(
                            df,
                            product_name=product_to_sell,
                            area=target_area,
                            business_category=target_biz_type
                        )
                    
                    if len(stores) > 0:
                        st.success(f"✅ Found {len(stores)} stores that should buy '{product_to_sell}'!")
                        st.markdown(f"""
                        **Why these stores:** They're in areas where '{product_to_sell}' is popular, 
                        or they're the same type of store that buys it elsewhere.
                        """)
                        
                        # Show stores in popular areas first
                        popular_area_stores = stores[stores["area_is_popular"] == True]
                        if len(popular_area_stores) > 0:
                            st.markdown("**⭐ Stores in Popular Areas (Best Targets!):**")
                            st.dataframe(
                                popular_area_stores.head(max_stores)[["customer_id", "location", "business_category", 
                                                                     "products_they_buy", "total_revenue"]],
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "customer_id": "Store Name",
                                    "location": "Location",
                                    "business_category": "Store Type",
                                    "products_they_buy": "What They Buy Now",
                                    "total_revenue": st.column_config.NumberColumn("Their Sales", format="$%.2f")
                                }
                            )
                        
                        # Show other stores
                        other_stores = stores[stores["area_is_popular"] == False]
                        if len(other_stores) > 0:
                            st.markdown("**📋 Other Recommended Stores:**")
                            st.dataframe(
                                other_stores.head(max_stores)[["customer_id", "location", "business_category",
                                                               "products_they_buy", "total_revenue"]],
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "customer_id": "Store Name",
                                    "location": "Location",
                                    "business_category": "Store Type",
                                    "products_they_buy": "What They Buy Now",
                                    "total_revenue": st.column_config.NumberColumn("Their Sales", format="$%.2f")
                                }
                            )
                        
                        # Store for export
                        st.session_state.product_stores = stores.head(max_stores)
                        
                        st.info("💡 **Next step:** Export this list from the 'Outreach Export' tab!")
                    else:
                        st.warning(f"""
                        **No stores found** for '{product_to_sell}'.
                        
                        **Try:**
                        - A different product
                        - Remove area filter
                        - Check if this product sells anywhere
                        """)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with tab3:
            st.subheader("🌍 What Products Should You Sell in This Area?")
            st.markdown("""
            **What this does:** Shows you which products are popular in an area, 
            and which stores in that area should buy them.
            
            **Perfect for:** Planning your product mix for a specific market!
            """)
            
            # Get areas
            if "state" in df.columns:
                areas = sorted([s for s in df["state"].unique() if s and str(s) != "nan"])
            elif "location" in df.columns:
                areas = sorted([loc for loc in df["location"].unique() if loc and str(loc) != "nan" and "," in str(loc)])
            else:
                areas = []
            
            selected_area = st.selectbox(
                "📍 Choose an Area",
                areas,
                key="area_recommendations"
            )
            
            n_products = st.slider("How many top products?", 3, 10, 5, key="n_top_products")
            n_stores = st.slider("Stores per product?", 5, 20, 10, key="n_stores_per_product")
            
            if st.button("🔍 Get Area Recommendations", key="get_area_recs", type="primary"):
                try:
                    with st.spinner(f"Analyzing products in {selected_area}..."):
                        recommendations = product_level_analytics.get_area_product_recommendations(
                            df,
                            area=selected_area,
                            n_products=n_products,
                            n_stores_per_product=n_stores
                        )
                    
                    if recommendations["popular_products"]:
                        st.success(f"✅ Found {len(recommendations['popular_products'])} popular products in {selected_area}!")
                        
                        st.markdown(f"**📦 Top Products in {selected_area}:**")
                        popular_df = pd.DataFrame(recommendations["popular_products"])
                        st.dataframe(
                            popular_df[["product_name", "product_category", "total_revenue", "num_stores", "num_orders"]],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "product_name": "Product",
                                "product_category": "Category",
                                "total_revenue": st.column_config.NumberColumn("Total Sales", format="$%.2f"),
                                "num_stores": "Stores Buying",
                                "num_orders": "Orders"
                            }
                        )
                        
                        # Show recommendations for each product
                        if recommendations["recommendations"]:
                            st.markdown(f"**🎯 Stores to Target in {selected_area}:**")
                            
                            for rec in recommendations["recommendations"]:
                                with st.expander(f"🛍️ {rec['product_name']} - {len(rec['recommended_stores'])} stores to contact"):
                                    st.markdown(f"""
                                    **Why this product:** 
                                    - {rec['popularity_in_area']['num_stores_buying']} stores in {selected_area} already buy it
                                    - ${rec['popularity_in_area']['total_revenue']:,.2f} in total sales
                                    """)
                                    
                                    stores_df = pd.DataFrame(rec["recommended_stores"])
                                    st.dataframe(
                                        stores_df[["customer_id", "location", "business_category", "products_they_buy"]],
                                        use_container_width=True,
                                        hide_index=True,
                                        column_config={
                                            "customer_id": "Store Name",
                                            "location": "Location",
                                            "business_category": "Store Type",
                                            "products_they_buy": "What They Buy"
                                        }
                                    )
                    else:
                        st.warning(f"No product data found for {selected_area}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # Automated Outreach Section
    if "location" in df.columns or ("city" in df.columns and "state" in df.columns):
        st.header("📧 Find New Customers to Contact")
        st.markdown("""
        **What this does:** Helps you find businesses that should buy your products but don't yet.
        
        **How it works:** 
        1. Pick a type of store (like "Gift Shop")
        2. Pick a product you want to sell (like "Women's accessories")
        3. Pick a location (like "California")
        4. Get a list of stores to contact!
        
        **Then:** Export the list and reach out to them with personalized messages.
        """)
        
        tab1, tab2, tab3, tab4 = st.tabs(["Target Finder", "Regional Analysis", "Brand Product Matcher", "Outreach Export"])
        
        with tab1:
            st.subheader("🎯 Step 1: Choose Your Target")
            st.markdown("**Tell us what you want to sell and to whom**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                biz_cats = sorted(df["business_category"].unique().tolist())
                outreach_biz_cat = st.selectbox(
                    "What type of store?",
                    biz_cats,
                    key="outreach_biz",
                    help="Example: Gift Shop, Bookstore, Boutique"
                )
            
            with col2:
                prod_cats = sorted(df["product_category"].unique().tolist())
                outreach_prod_cat = st.selectbox(
                    "What product to sell?",
                    prod_cats,
                    key="outreach_prod",
                    help="Example: Women's accessories, Stationery & writing"
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
                    "Which state? (Optional)",
                    [None] + states,
                    key="outreach_state",
                    help="Leave blank to search everywhere, or pick a specific state"
                )
            
            st.markdown("**How many stores do you want to find?**")
            max_targets = st.slider("Number of stores", 10, 100, 25, key="max_targets", help="More stores = more work, but more potential sales")
            
            st.divider()
            
            if st.button("🔍 Find Target Stores", key="generate_outreach", type="primary"):
                try:
                    with st.spinner("Searching for stores that match your criteria..."):
                        targets = outreach_automation.generate_outreach_list(
                            df,
                            business_category=outreach_biz_cat,
                            product_category=outreach_prod_cat,
                            location_filter=outreach_state,
                            max_results=max_targets
                        )
                    
                    if len(targets) > 0:
                        st.success(f"✅ Found {len(targets)} stores to contact!")
                        st.markdown("""
                        **What you're seeing:** Stores that:
                        - Are the type you selected (e.g., Gift Shop)
                        - Are in the location you picked
                        - **Don't currently buy** the product you want to sell (opportunity!)
                        - Buy similar products (so they're likely interested)
                        """)
                        
                        # Summary stats
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📋 Stores Found", len(targets), help="Number of stores to contact")
                        with col2:
                            st.metric("💰 Avg Sales", f"${targets['total_revenue'].mean():,.2f}", help="How much these stores typically spend")
                        with col3:
                            st.metric("📍 Locations", targets["location"].nunique(), help="Number of different cities/states")
                        
                        st.markdown("**📊 Store Details:**")
                        # Display targets
                        st.dataframe(
                            targets[["customer_id", "location", "current_products", 
                                    "recommended_product", "total_revenue"]],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "customer_id": "Store Name",
                                "location": "Location",
                                "current_products": "What They Buy Now",
                                "recommended_product": "Product to Sell Them",
                                "total_revenue": st.column_config.NumberColumn("Their Sales", format="$%.2f")
                            }
                        )
                        
                        # Store in session state for export
                        st.session_state.outreach_targets = targets
                        
                        st.info("💡 **Next step:** Go to the 'Outreach Export' tab to download this list!")
                    else:
                        st.warning("""
                        **No stores found** with those exact criteria.
                        
                        **Try:**
                        - Different business type
                        - Different product category  
                        - Remove the state filter to search everywhere
                        """)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("Make sure you have business categories loaded. Check the sidebar!")
        
        with tab2:
            st.subheader("🌍 What Sells Where?")
            st.markdown("""
            **What this shows:** Which products sell best in different states/regions.
            
            **Why it matters:** Products that sell well in California might not sell in Texas!
            Use this to customize your product mix by location.
            
            **Example:** If "Women's accessories" sell great in New York but not in Montana,
            focus your marketing differently in each state.
            """)
            
            if st.button("📊 Analyze Regional Sales", key="analyze_regional", type="primary"):
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
            st.subheader("🎯 Match Your Brand Products to Buyers")
            st.markdown("""
            **What this does:** Takes your brand's products (like from Faire) and finds stores that should buy them.
            
            **Perfect for:** When you have a new product line or brand and want to find the best customers.
            
            **Example:** Upload Hilarious Humanitarian products → Find Gift Shops that buy similar products!
            """)
            
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
                    st.subheader("📈 How Well Do These Products Fit Your Market?")
                    st.markdown("""
                    **What this shows:** Whether your brand products match what stores are already buying.
                    
                    **High score = Good fit** → Stores already buy similar products, easy to sell!
                    **Low score = New market** → Different products, might need more education.
                    """)
                    if st.button("🔍 Analyze Market Fit", key="analyze_market_fit", type="primary"):
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
                    st.subheader("🔍 Find Stores That Should Buy These Products")
                    st.markdown("**Narrow down your search (optional):**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        match_states = sorted([s for s in df["state"].unique() if s and str(s) != "nan"]) if "state" in df.columns else []
                        match_state = st.selectbox(
                            "📍 Which state?",
                            [None] + match_states,
                            key="match_state",
                            help="Leave blank to search all states"
                        )
                    
                    with col2:
                        match_biz_cats = sorted(df["business_category"].unique().tolist())
                        match_biz_cat = st.selectbox(
                            "🏪 What type of store?",
                            [None] + match_biz_cats,
                            key="match_biz_cat",
                            help="Leave blank to search all store types"
                        )
                    
                    st.markdown("**How many stores do you want to find?**")
                    max_matches = st.slider("Number of stores", 10, 100, 30, key="max_matches")
                    
                    st.divider()
                    
                    if st.button("🔍 Find Matching Stores", key="find_brand_buyers", type="primary"):
                        try:
                            matches = brand_product_matcher.generate_brand_outreach_list(
                                df,
                                brand_products,
                                location_filter=match_state,
                                business_category_filter=match_biz_cat,
                                max_results=max_matches
                            )
                            
                            if len(matches) > 0:
                                st.success(f"✅ Found {len(matches)} stores that should buy your brand products!")
                                st.markdown("""
                                **What you're seeing:** Stores that:
                                - Buy similar products (so they'll like yours)
                                - Don't buy your brand yet (opportunity!)
                                - Match your filters (location, store type)
                                """)
                                
                                # Summary
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("📋 Stores Found", len(matches))
                                with col2:
                                    st.metric("📍 Locations", matches["location"].nunique())
                                with col3:
                                    st.metric("⭐ Opportunity", f"{matches['opportunity_score'].mean():.1f}", help="Lower = more opportunity")
                                
                                st.markdown("**📊 Store Details:**")
                                # Display matches
                                st.dataframe(
                                    matches[["customer_id", "location", "business_category", 
                                            "brand_category", "recommended_brand_products",
                                            "current_products"]],
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        "customer_id": "Store Name",
                                        "location": "Location",
                                        "business_category": "Store Type",
                                        "brand_category": "Product Category",
                                        "recommended_brand_products": "Products to Sell",
                                        "current_products": "What They Buy Now"
                                    }
                                )
                                
                                # Store for export
                                st.session_state.brand_matches = matches
                                
                                st.info("💡 **Next step:** Go to 'Outreach Export' tab to download this list!")
                            else:
                                st.warning("""
                                **No matches found.** 
                                
                                **Try:**
                                - Removing filters (search everywhere)
                                - Checking if product categories match
                                - Using different brand products
                                """)
                        except Exception as e:
                            st.error(f"Error finding matches: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
                
                except Exception as e:
                    st.error(f"Error loading brand products: {str(e)}")
            else:
                st.info("Upload a brand products CSV or use the Hilarious Humanitarian sample data")
        
        with tab4:
            st.subheader("📥 Download Your Contact List")
            st.markdown("""
            **What this does:** Exports your target store list so you can contact them.
            
            **Choose your format:**
            - **CSV** = Spreadsheet (Excel, Google Sheets)
            - **JSON** = For apps/automation
            - **Email Templates** = Ready-to-send personalized emails
            """)
            
            if "outreach_targets" in st.session_state and len(st.session_state.outreach_targets) > 0:
                targets = st.session_state.outreach_targets
                
                st.success(f"✅ Ready to export {len(targets)} stores!")
                
                export_format = st.selectbox(
                    "📄 Choose Format",
                    ["CSV", "JSON", "Email Templates"],
                    key="export_format",
                    help="CSV works with Excel, Email Templates are ready to send"
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
    st.header("💾 Download Your Reports")
    st.markdown("**Save your analysis** - Download data to use in Excel, share with your team, or import into other tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export category matrix
        try:
            matrix = analytics.calculate_category_matrix(filtered_df)
            csv_matrix = matrix.to_csv()
            st.download_button(
                label="📊 Download Store-Product Matrix",
                data=csv_matrix,
                file_name=f"store_product_matrix_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                help="Spreadsheet showing which stores buy which products"
            )
        except:
            pass
    
    with col2:
        # Export top combinations
        try:
            top_combinations = analytics.get_top_combinations(filtered_df, n=100)
            csv_top = top_combinations.to_csv(index=False)
            st.download_button(
                label="🏆 Download Top Seller Combinations",
                data=csv_top,
                file_name=f"top_combinations_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                help="List of your best store-product matches"
            )
        except:
            pass


if __name__ == "__main__":
    main()


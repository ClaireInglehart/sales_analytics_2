"""
Product-level analytics - Analyze specific products by area and recommend to similar stores
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict


def analyze_product_popularity_by_area(
    df: pd.DataFrame,
    product_name: str = None,
    product_id: str = None,
    area: str = None
) -> Dict:
    """
    Analyze how popular a specific product is in different areas
    
    Args:
        df: Sales DataFrame with product_name, product_id, location
        product_name: Specific product name to analyze
        product_id: Specific product ID to analyze
        area: Optional area filter (state or city, state)
        
    Returns:
        Dictionary with area-based popularity analysis
    """
    filtered_df = df.copy()
    
    # Filter by product if specified
    if product_name:
        filtered_df = filtered_df[filtered_df["product_name"] == product_name]
    elif product_id:
        filtered_df = filtered_df[filtered_df["product_id"] == product_id]
    
    # Filter by area if specified
    if area:
        if "state" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["state"].str.contains(area, case=False, na=False)]
        elif "location" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["location"].str.contains(area, case=False, na=False)]
    
    if len(filtered_df) == 0:
        return {"error": "No data found for the specified criteria"}
    
    # Analyze by location
    if "location" in filtered_df.columns:
        location_analysis = filtered_df.groupby("location").agg({
            "sales_amount": ["sum", "count", "mean"],
            "customer_id": "nunique"
        }).reset_index()
        location_analysis.columns = ["location", "total_revenue", "num_orders", "avg_order", "num_stores"]
    elif "city" in filtered_df.columns and "state" in filtered_df.columns:
        filtered_df["location"] = filtered_df["city"] + ", " + filtered_df["state"]
        location_analysis = filtered_df.groupby("location").agg({
            "sales_amount": ["sum", "count", "mean"],
            "customer_id": "nunique"
        }).reset_index()
        location_analysis.columns = ["location", "total_revenue", "num_orders", "avg_order", "num_stores"]
    else:
        return {"error": "Location data not available"}
    
    # Sort by popularity (total revenue)
    location_analysis = location_analysis.sort_values("total_revenue", ascending=False)
    
    return {
        "product_name": product_name or product_id,
        "total_sales": filtered_df["sales_amount"].sum(),
        "total_orders": len(filtered_df),
        "unique_stores": filtered_df["customer_id"].nunique(),
        "top_areas": location_analysis.head(10).to_dict("records"),
        "all_areas": location_analysis.to_dict("records")
    }


def find_products_popular_in_area(
    df: pd.DataFrame,
    area: str,
    top_n: int = 10
) -> pd.DataFrame:
    """
    Find which products are most popular in a specific area
    
    Args:
        df: Sales DataFrame
        area: Area to analyze (state or city, state)
        top_n: Number of top products to return
        
    Returns:
        DataFrame with top products in that area
    """
    filtered_df = df.copy()
    
    # Filter by area
    if "state" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["state"].str.contains(area, case=False, na=False)]
    elif "location" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["location"].str.contains(area, case=False, na=False)]
    elif "city" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["city"].str.contains(area, case=False, na=False)]
    
    if len(filtered_df) == 0:
        return pd.DataFrame()
    
    # Group by product
    product_analysis = filtered_df.groupby(["product_id", "product_name", "product_category"]).agg({
        "sales_amount": ["sum", "count", "mean"],
        "customer_id": "nunique"
    }).reset_index()
    
    product_analysis.columns = [
        "product_id", "product_name", "product_category",
        "total_revenue", "num_orders", "avg_order", "num_stores"
    ]
    
    # Sort by total revenue
    product_analysis = product_analysis.sort_values("total_revenue", ascending=False)
    
    return product_analysis.head(top_n)


def find_stores_for_specific_product(
    df: pd.DataFrame,
    product_name: str = None,
    product_id: str = None,
    area: str = None,
    business_category: str = None
) -> pd.DataFrame:
    """
    Find stores that should buy a specific product based on:
    - Other stores in the area buying it
    - Same business type buying it elsewhere
    - Similar products they already buy
    
    Args:
        df: Sales DataFrame
        product_name: Product name to recommend
        product_id: Product ID to recommend
        area: Area to focus on (state or city, state)
        business_category: Optional business category filter
        
    Returns:
        DataFrame with recommended stores
    """
    # Find stores that already buy this product
    if product_name:
        product_buyers = df[df["product_name"] == product_name]
    elif product_id:
        product_buyers = df[df["product_id"] == product_id]
    else:
        return pd.DataFrame()
    
    if len(product_buyers) == 0:
        return pd.DataFrame()
    
    # Get areas where this product sells well
    if "location" in product_buyers.columns:
        popular_areas = product_buyers.groupby("location")["customer_id"].nunique().nlargest(5).index.tolist()
    elif "city" in product_buyers.columns and "state" in product_buyers.columns:
        product_buyers["location"] = product_buyers["city"] + ", " + product_buyers["state"]
        popular_areas = product_buyers.groupby("location")["customer_id"].nunique().nlargest(5).index.tolist()
    else:
        popular_areas = []
    
    # Get business types that buy this product
    buyer_types = product_buyers["business_category"].value_counts().head(3).index.tolist()
    
    # Find stores that DON'T buy this product but should
    targets = []
    
    # Filter by area if specified
    search_df = df.copy()
    if area:
        if "state" in search_df.columns:
            search_df = search_df[search_df["state"].str.contains(area, case=False, na=False)]
        elif "location" in search_df.columns:
            search_df = search_df[search_df["location"].str.contains(area, case=False, na=False)]
    
    # Filter by business category if specified
    if business_category:
        search_df = search_df[search_df["business_category"] == business_category]
    elif buyer_types:
        # Use top buyer types if not specified
        search_df = search_df[search_df["business_category"].isin(buyer_types)]
    
    # Find stores in popular areas that don't buy this product
    for customer_id in search_df["customer_id"].unique():
        customer_data = search_df[search_df["customer_id"] == customer_id]
        
        # Check if they buy this product
        if product_name:
            buys_product = (customer_data["product_name"] == product_name).any()
        else:
            buys_product = (customer_data["product_id"] == product_id).any()
        
        if not buys_product:
            # Get customer info
            customer_info = customer_data.iloc[0]
            
            # Get location
            if "location" in customer_info:
                loc = customer_info["location"]
            elif "city" in customer_info and "state" in customer_info:
                loc = f"{customer_info['city']}, {customer_info['state']}"
            else:
                loc = "Unknown"
            
            # Check if this area is popular for the product
            area_match = loc in popular_areas if popular_areas else False
            
            # Get what products they do buy
            products_bought = customer_data["product_name"].unique().tolist()
            
            targets.append({
                "customer_id": customer_id,
                "business_category": customer_info.get("business_category", "Unknown"),
                "location": loc,
                "product_to_sell": product_name or product_id,
                "products_they_buy": ", ".join(products_bought[:5]),
                "total_revenue": customer_data["sales_amount"].sum(),
                "area_is_popular": area_match,
                "opportunity_score": len(products_bought)  # Lower = more opportunity
            })
    
    if targets:
        targets_df = pd.DataFrame(targets)
        # Prioritize stores in popular areas
        targets_df = targets_df.sort_values(["area_is_popular", "opportunity_score"], ascending=[False, True])
        return targets_df
    else:
        return pd.DataFrame(columns=[
            "customer_id", "business_category", "location", "product_to_sell",
            "products_they_buy", "total_revenue", "area_is_popular", "opportunity_score"
        ])


def get_area_product_recommendations(
    df: pd.DataFrame,
    area: str,
    n_products: int = 5,
    n_stores_per_product: int = 10
) -> Dict:
    """
    Get product recommendations for an area:
    - Find popular products in that area
    - Find stores in that area that don't buy those products yet
    
    Args:
        df: Sales DataFrame
        area: Area to analyze
        n_products: Number of popular products to analyze
        n_stores_per_product: Number of store recommendations per product
        
    Returns:
        Dictionary with product recommendations
    """
    # Find popular products in this area
    popular_products = find_products_popular_in_area(df, area, top_n=n_products)
    
    if len(popular_products) == 0:
        return {"area": area, "products": [], "recommendations": []}
    
    recommendations = []
    
    for _, product_row in popular_products.iterrows():
        product_name = product_row["product_name"]
        product_id = product_row["product_id"]
        
        # Find stores that should buy this product
        stores = find_stores_for_specific_product(
            df,
            product_name=product_name,
            area=area,
            business_category=None
        )
        
        if len(stores) > 0:
            recommendations.append({
                "product_name": product_name,
                "product_id": product_id,
                "product_category": product_row["product_category"],
                "popularity_in_area": {
                    "total_revenue": product_row["total_revenue"],
                    "num_stores_buying": product_row["num_stores"],
                    "num_orders": product_row["num_orders"]
                },
                "recommended_stores": stores.head(n_stores_per_product).to_dict("records")
            })
    
    return {
        "area": area,
        "popular_products": popular_products.to_dict("records"),
        "recommendations": recommendations
    }


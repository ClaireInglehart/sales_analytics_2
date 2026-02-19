"""
Location-based analytics for finding similar businesses in nearby areas
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict


def find_similar_businesses_by_location(
    df: pd.DataFrame,
    business_category: str,
    product_category: str,
    location: str,
    radius_miles: int = 50,
    n_recommendations: int = 10
) -> pd.DataFrame:
    """
    Find similar businesses in nearby locations that might want to purchase the same products
    
    Args:
        df: DataFrame with sales data including location information
        business_category: The business category to find similar businesses for
        product_category: The product category they're buying
        location: Location identifier (city, state, or "city, state")
        radius_miles: Radius to search for similar businesses (default 50 miles)
        n_recommendations: Number of recommendations to return
        
    Returns:
        DataFrame with recommended businesses and their locations
    """
    if "location" not in df.columns and "city" not in df.columns and "state" not in df.columns:
        raise ValueError("DataFrame must contain location information (location, city, or state column)")
    
    # Parse location
    location_parts = str(location).split(",")
    if len(location_parts) == 2:
        city, state = location_parts[0].strip(), location_parts[1].strip()
    else:
        city = location.strip()
        state = None
    
    # Find businesses that buy the same product category
    product_buyers = df[df["product_category"] == product_category].copy()
    
    # Find businesses of the same category
    same_category_businesses = df[df["business_category"] == business_category].copy()
    
    # Get unique businesses and their locations
    business_locations = {}
    if "location" in df.columns:
        for customer_id in df["customer_id"].unique():
            customer_data = df[df["customer_id"] == customer_id]
            loc = customer_data["location"].iloc[0] if "location" in customer_data.columns else "Unknown"
            business_locations[customer_id] = loc
    elif "city" in df.columns and "state" in df.columns:
        for customer_id in df["customer_id"].unique():
            customer_data = df[df["customer_id"] == customer_id]
            city_val = customer_data["city"].iloc[0] if "city" in customer_data.columns else "Unknown"
            state_val = customer_data["state"].iloc[0] if "state" in customer_data.columns else "Unknown"
            business_locations[customer_id] = f"{city_val}, {state_val}"
    else:
        # Fallback: use customer_id as location identifier
        business_locations = {cid: cid for cid in df["customer_id"].unique()}
    
    # Find businesses in the same or nearby locations
    nearby_businesses = []
    for customer_id, loc in business_locations.items():
        loc_str = str(loc).lower()
        if state:
            # Check if same state
            if state.lower() in loc_str:
                nearby_businesses.append(customer_id)
        elif city:
            # Check if same city or nearby
            if city.lower() in loc_str:
                nearby_businesses.append(customer_id)
        else:
            # If location string matches
            if location.lower() in loc_str:
                nearby_businesses.append(customer_id)
    
    # Find businesses that:
    # 1. Are in nearby locations
    # 2. Are the same business category
    # 3. Don't currently buy this product category (opportunity)
    recommendations = []
    
    for customer_id in nearby_businesses:
        customer_data = df[df["customer_id"] == customer_id]
        customer_category = customer_data["business_category"].iloc[0] if "business_category" in customer_data.columns else None
        
        # Check if they buy this product category
        buys_product = (customer_data["product_category"] == product_category).any()
        
        if customer_category == business_category and not buys_product:
            # This is a potential target
            total_revenue = customer_data["sales_amount"].sum()
            product_categories_bought = customer_data["product_category"].nunique()
            
            recommendations.append({
                "customer_id": customer_id,
                "location": business_locations.get(customer_id, "Unknown"),
                "business_category": customer_category,
                "current_product_categories": product_categories_bought,
                "total_revenue": total_revenue,
                "opportunity_score": product_categories_bought  # Lower = more opportunity
            })
    
    if not recommendations:
        # If no exact matches, find similar business categories in nearby locations
        for customer_id in nearby_businesses:
            customer_data = df[df["customer_id"] == customer_id]
            customer_category = customer_data["business_category"].iloc[0] if "business_category" in customer_data.columns else None
            
            buys_product = (customer_data["product_category"] == product_category).any()
            
            if not buys_product:
                total_revenue = customer_data["sales_amount"].sum()
                product_categories_bought = customer_data["product_category"].nunique()
                
                recommendations.append({
                    "customer_id": customer_id,
                    "location": business_locations.get(customer_id, "Unknown"),
                    "business_category": customer_category,
                    "current_product_categories": product_categories_bought,
                    "total_revenue": total_revenue,
                    "opportunity_score": product_categories_bought
                })
    
    # Convert to DataFrame and sort by opportunity score
    if recommendations:
        rec_df = pd.DataFrame(recommendations)
        rec_df = rec_df.sort_values("opportunity_score").head(n_recommendations)
        return rec_df
    else:
        return pd.DataFrame(columns=["customer_id", "location", "business_category", "current_product_categories", "total_revenue", "opportunity_score"])


def get_location_insights(df: pd.DataFrame) -> Dict:
    """
    Get insights about sales by location
    
    Args:
        df: DataFrame with location information
        
    Returns:
        Dictionary with location-based insights
    """
    insights = {}
    
    if "location" in df.columns or ("city" in df.columns and "state" in df.columns):
        # Count businesses by location
        if "location" in df.columns:
            location_counts = df.groupby("location")["customer_id"].nunique().sort_values(ascending=False)
        else:
            df["location"] = df["city"] + ", " + df["state"]
            location_counts = df.groupby("location")["customer_id"].nunique().sort_values(ascending=False)
        
        insights["top_locations"] = location_counts.head(10).to_dict()
        insights["total_locations"] = len(location_counts)
        
        # Sales by location
        if "location" in df.columns:
            sales_by_location = df.groupby("location")["sales_amount"].sum().sort_values(ascending=False)
        else:
            sales_by_location = df.groupby("location")["sales_amount"].sum().sort_values(ascending=False)
        
        insights["top_sales_locations"] = sales_by_location.head(10).to_dict()
    
    return insights


def find_location_based_opportunities(
    df: pd.DataFrame,
    product_category: str,
    n_results: int = 20
) -> pd.DataFrame:
    """
    Find location-based opportunities: areas where businesses buy this product category
    
    Args:
        df: DataFrame with sales and location data
        product_category: Product category to analyze
        n_results: Number of results to return
        
    Returns:
        DataFrame with location opportunities
    """
    if "location" not in df.columns and ("city" not in df.columns or "state" not in df.columns):
        return pd.DataFrame()
    
    # Create location column if needed
    if "location" not in df.columns:
        df = df.copy()
        df["location"] = df["city"] + ", " + df["state"]
    
    # Find locations where this product category is sold
    product_sales = df[df["product_category"] == product_category].copy()
    
    # Group by location and business category
    opportunities = product_sales.groupby(["location", "business_category"]).agg({
        "customer_id": "nunique",
        "sales_amount": "sum"
    }).reset_index()
    
    opportunities.columns = ["location", "business_category", "num_businesses", "total_revenue"]
    opportunities = opportunities.sort_values("num_businesses", ascending=False)
    
    return opportunities.head(n_results)


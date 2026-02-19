"""
Brand Product Matcher - Match Faire brand products with potential buyers
"""

import pandas as pd
from typing import Dict, List, Tuple
from src import outreach_automation


def load_brand_products(file_path: str) -> pd.DataFrame:
    """
    Load brand products from CSV file
    
    Args:
        file_path: Path to CSV file with product data
        
    Returns:
        DataFrame with product information
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise ValueError(f"Error loading brand products: {str(e)}")


def match_brand_to_buyers(
    sales_df: pd.DataFrame,
    brand_products_df: pd.DataFrame,
    location_filter: str = None,
    business_category_filter: str = None
) -> pd.DataFrame:
    """
    Match brand products with potential buyers based on:
    - Product category similarity
    - Business type
    - Location
    - Current product mix
    
    Args:
        sales_df: Sales data DataFrame
        brand_products_df: Brand products DataFrame
        location_filter: Optional location filter (state or city, state)
        business_category_filter: Optional business category filter
        
    Returns:
        DataFrame with matched businesses and recommendations
    """
    results = []
    
    # Get unique product categories from brand
    brand_categories = brand_products_df["product_category"].unique()
    
    # Filter sales data by location if provided
    filtered_sales = sales_df.copy()
    if location_filter:
        if "state" in filtered_sales.columns:
            filtered_sales = filtered_sales[filtered_sales["state"].str.contains(location_filter, case=False, na=False)]
        elif "location" in filtered_sales.columns:
            filtered_sales = filtered_sales[filtered_sales["location"].str.contains(location_filter, case=False, na=False)]
    
    # Filter by business category if provided
    if business_category_filter:
        filtered_sales = filtered_sales[filtered_sales["business_category"] == business_category_filter]
    
    # For each brand product category, find potential buyers
    for brand_category in brand_categories:
        # Find businesses that buy similar products
        similar_buyers = outreach_automation.find_target_businesses_for_outreach(
            filtered_sales,
            business_category=business_category_filter if business_category_filter else filtered_sales["business_category"].iloc[0],
            product_category=brand_category,
            location=location_filter
        )
        
        # Add brand context
        if len(similar_buyers) > 0:
            brand_products_in_category = brand_products_df[
                brand_products_df["product_category"] == brand_category
            ]
            
            for _, buyer in similar_buyers.iterrows():
                results.append({
                    "customer_id": buyer["customer_id"],
                    "business_category": buyer["business_category"],
                    "location": buyer["location"],
                    "brand_category": brand_category,
                    "recommended_brand_products": ", ".join(brand_products_in_category["product_name"].head(5).tolist()),
                    "current_products": buyer["current_products"],
                    "similar_products": buyer["similar_products"],
                    "total_revenue": buyer["total_revenue"],
                    "opportunity_score": buyer["opportunity_score"],
                    "match_reason": f"Buys similar {brand_category} products"
                })
    
    if results:
        results_df = pd.DataFrame(results)
        # Remove duplicates (same customer might match multiple categories)
        results_df = results_df.drop_duplicates(subset=["customer_id"], keep="first")
        results_df = results_df.sort_values("opportunity_score")
        return results_df
    else:
        return pd.DataFrame(columns=[
            "customer_id", "business_category", "location", "brand_category",
            "recommended_brand_products", "current_products", "similar_products",
            "total_revenue", "opportunity_score", "match_reason"
        ])


def analyze_brand_market_fit(
    sales_df: pd.DataFrame,
    brand_products_df: pd.DataFrame
) -> Dict:
    """
    Analyze how well brand products fit the market
    
    Args:
        sales_df: Sales data DataFrame
        brand_products_df: Brand products DataFrame
        
    Returns:
        Dictionary with market fit analysis
    """
    analysis = {}
    
    # Get brand product categories
    brand_categories = brand_products_df["product_category"].unique()
    
    # Analyze each category
    category_analysis = {}
    for category in brand_categories:
        # Find businesses that buy this category
        buyers = sales_df[sales_df["product_category"] == category]
        
        if len(buyers) > 0:
            category_analysis[category] = {
                "num_buyers": buyers["customer_id"].nunique(),
                "total_revenue": buyers["sales_amount"].sum(),
                "avg_transaction": buyers["sales_amount"].mean(),
                "top_business_types": buyers["business_category"].value_counts().head(5).to_dict(),
                "top_locations": buyers.groupby("location")["sales_amount"].sum().nlargest(5).to_dict() if "location" in buyers.columns else {}
            }
    
    analysis["category_breakdown"] = category_analysis
    
    # Overall market fit score
    total_buyers = sum([cat["num_buyers"] for cat in category_analysis.values()])
    analysis["market_fit_score"] = min(100, (total_buyers / len(sales_df["customer_id"].unique())) * 100) if len(sales_df) > 0 else 0
    
    return analysis


def generate_brand_outreach_list(
    sales_df: pd.DataFrame,
    brand_products_df: pd.DataFrame,
    location_filter: str = None,
    business_category_filter: str = None,
    max_results: int = 50
) -> pd.DataFrame:
    """
    Generate outreach list for brand products
    
    Args:
        sales_df: Sales data DataFrame
        brand_products_df: Brand products DataFrame
        location_filter: Optional location filter
        business_category_filter: Optional business category filter
        max_results: Maximum number of results
        
    Returns:
        DataFrame ready for outreach
    """
    matches = match_brand_to_buyers(
        sales_df,
        brand_products_df,
        location_filter=location_filter,
        business_category_filter=business_category_filter
    )
    
    if len(matches) > 0:
        matches["outreach_priority"] = matches["opportunity_score"].rank(ascending=True)
        matches["personalization_note"] = (
            f"Based on your current product mix ({matches['current_products']}), "
            f"we recommend {matches['brand_category']} products: {matches['recommended_brand_products']}"
        )
        
        return matches.head(max_results)
    else:
        return matches


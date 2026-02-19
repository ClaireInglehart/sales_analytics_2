"""
Brand-specific product matching and outreach recommendations
"""

import pandas as pd
from typing import Dict, List, Tuple
from src import outreach_automation


def load_brand_products(brand_file: str) -> pd.DataFrame:
    """
    Load brand product data from CSV
    
    Args:
        brand_file: Path to brand products CSV
        
    Returns:
        DataFrame with brand products
    """
    try:
        products = pd.read_csv(brand_file)
        return products
    except Exception as e:
        raise ValueError(f"Error loading brand products: {str(e)}")


def find_businesses_for_brand(
    sales_df: pd.DataFrame,
    brand_products_df: pd.DataFrame,
    business_categories: List[str] = None,
    location_filter: str = None,
    min_match_score: float = 0.5
) -> pd.DataFrame:
    """
    Find businesses that would be good matches for a brand's products
    
    Args:
        sales_df: Sales DataFrame with customer data
        brand_products_df: Brand products DataFrame
        business_categories: List of business categories to target (None = all)
        location_filter: Optional location filter (state or city, state)
        min_match_score: Minimum match score (0-1)
        
    Returns:
        DataFrame with matched businesses and recommendations
    """
    # Get brand product categories
    brand_categories = brand_products_df["product_category"].unique().tolist()
    
    # Find businesses that buy similar product categories
    matches = []
    
    # Filter by business category if specified
    if business_categories:
        filtered_df = sales_df[sales_df["business_category"].isin(business_categories)].copy()
    else:
        filtered_df = sales_df.copy()
    
    # Filter by location if specified
    if location_filter:
        if "state" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["state"].str.contains(location_filter, case=False, na=False)]
        elif "location" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["location"].str.contains(location_filter, case=False, na=False)]
    
    # Analyze each unique customer
    for customer_id in filtered_df["customer_id"].unique():
        customer_data = filtered_df[filtered_df["customer_id"] == customer_id]
        
        # Get customer's current product categories
        customer_categories = set(customer_data["product_category"].unique())
        brand_categories_set = set(brand_categories)
        
        # Calculate match score
        # 1. Do they buy any of the brand's product categories?
        category_overlap = len(customer_categories & brand_categories_set)
        
        # 2. Do they NOT buy this brand's products? (opportunity)
        buys_brand_category = category_overlap > 0
        
        # 3. Calculate similarity score
        if len(customer_categories) > 0:
            match_score = category_overlap / max(len(customer_categories), len(brand_categories_set))
        else:
            match_score = 0
        
        # Find recommended products from brand
        recommended_products = []
        for cat in brand_categories:
            if cat in customer_categories:
                # They buy this category, recommend brand products in this category
                cat_products = brand_products_df[brand_products_df["product_category"] == cat]
                recommended_products.extend(cat_products["product_name"].head(3).tolist())
        
        # If no overlap, recommend top products from brand
        if not recommended_products:
            recommended_products = brand_products_df["product_name"].head(5).tolist()
        
        # Get location
        if "location" in customer_data.columns:
            location = customer_data["location"].iloc[0]
        elif "city" in customer_data.columns and "state" in customer_data.columns:
            location = f"{customer_data['city'].iloc[0]}, {customer_data['state'].iloc[0]}"
        else:
            location = "Unknown"
        
        matches.append({
            "customer_id": customer_id,
            "business_category": customer_data["business_category"].iloc[0],
            "location": location,
            "current_product_categories": ", ".join(sorted(customer_categories)),
            "brand_product_categories": ", ".join(brand_categories),
            "category_overlap": category_overlap,
            "match_score": match_score,
            "recommended_products": " | ".join(recommended_products[:5]),
            "total_revenue": customer_data["sales_amount"].sum(),
            "product_diversity": len(customer_categories),
            "opportunity_score": len(customer_categories) if buys_brand_category else len(customer_categories) + 10
        })
    
    if matches:
        matches_df = pd.DataFrame(matches)
        # Filter by minimum match score
        matches_df = matches_df[matches_df["match_score"] >= min_match_score]
        # Sort by opportunity score (lower = more opportunity)
        matches_df = matches_df.sort_values("opportunity_score")
        return matches_df
    else:
        return pd.DataFrame(columns=[
            "customer_id", "business_category", "location", "current_product_categories",
            "brand_product_categories", "category_overlap", "match_score",
            "recommended_products", "total_revenue", "product_diversity", "opportunity_score"
        ])


def analyze_brand_regional_fit(
    sales_df: pd.DataFrame,
    brand_products_df: pd.DataFrame
) -> Dict:
    """
    Analyze which regions/states would be good fits for the brand
    
    Args:
        sales_df: Sales DataFrame
        brand_products_df: Brand products DataFrame
        
    Returns:
        Dictionary with regional analysis
    """
    brand_categories = set(brand_products_df["product_category"].unique())
    
    # Create state column if needed
    if "state" not in sales_df.columns and "location" in sales_df.columns:
        sales_df = sales_df.copy()
        sales_df["state"] = sales_df["location"].str.split(",").str[-1].str.strip()
    
    if "state" not in sales_df.columns:
        return {}
    
    regional_analysis = {}
    
    for state in sales_df["state"].unique():
        if not state or str(state) == "nan":
            continue
            
        state_data = sales_df[sales_df["state"] == state]
        
        # Get product categories sold in this state
        state_categories = set(state_data["product_category"].unique())
        
        # Calculate overlap with brand categories
        overlap = len(state_categories & brand_categories)
        overlap_pct = (overlap / len(brand_categories)) * 100 if brand_categories else 0
        
        # Get businesses that buy similar categories
        businesses_with_overlap = state_data[
            state_data["product_category"].isin(brand_categories)
        ]["customer_id"].nunique()
        
        total_businesses = state_data["customer_id"].nunique()
        
        # Calculate fit score (0-1 scale)
        category_fit = overlap_pct / 100 if brand_categories else 0
        business_fit = businesses_with_overlap / total_businesses if total_businesses > 0 else 0
        fit_score = (category_fit * 0.6) + (business_fit * 0.4)  # Weighted combination
        
        regional_analysis[state] = {
            "total_businesses": total_businesses,
            "businesses_with_overlap": businesses_with_overlap,
            "overlap_percentage": overlap_pct,
            "category_overlap": overlap,
            "total_brand_categories": len(brand_categories),
            "fit_score": fit_score
        }
    
    return regional_analysis


def generate_brand_outreach_list(
    sales_df: pd.DataFrame,
    brand_products_df: pd.DataFrame,
    business_categories: List[str] = None,
    location_filter: str = None,
    max_results: int = 50
) -> pd.DataFrame:
    """
    Generate outreach list specifically for a brand
    
    Args:
        sales_df: Sales DataFrame
        brand_products_df: Brand products DataFrame
        business_categories: Business categories to target
        location_filter: Location filter
        max_results: Maximum results
        
    Returns:
        DataFrame ready for outreach
    """
    matches = find_businesses_for_brand(
        sales_df,
        brand_products_df,
        business_categories=business_categories,
        location_filter=location_filter,
        min_match_score=0.3  # Lower threshold for brand matching
    )
    
    if len(matches) > 0:
        # Add outreach-specific columns
        matches["outreach_message"] = matches.apply(
            lambda row: f"Based on your current product mix ({row['current_product_categories']}), "
                       f"we think you'd love our {', '.join(brand_products_df['product_category'].unique()[:2])} products!",
            axis=1
        )
        
        return matches.head(max_results)
    else:
        return matches


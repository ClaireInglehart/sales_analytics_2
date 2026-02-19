"""
Automated outreach and product recommendation system
"""

import pandas as pd
from typing import Dict, List, Tuple
from collections import defaultdict
import json


def find_similar_products(
    df: pd.DataFrame,
    product_category: str,
    n_similar: int = 5
) -> List[str]:
    """
    Find similar products based on what businesses buy together
    
    Args:
        df: Sales DataFrame
        product_category: Product category to find similar products for
        n_similar: Number of similar products to return
        
    Returns:
        List of similar product categories
    """
    # Find businesses that buy this product category
    buyers = df[df["product_category"] == product_category]["customer_id"].unique()
    
    # Find what other products these businesses buy
    buyer_products = df[df["customer_id"].isin(buyers)]["product_category"].value_counts()
    
    # Remove the original product category
    buyer_products = buyer_products[buyer_products.index != product_category]
    
    # Return top similar products
    return buyer_products.head(n_similar).index.tolist()


def find_target_businesses_for_outreach(
    df: pd.DataFrame,
    business_category: str,
    product_category: str,
    location: str = None,
    state: str = None,
    region: str = None
) -> pd.DataFrame:
    """
    Find target businesses for automated outreach
    
    Args:
        df: Sales DataFrame with location data
        business_category: Type of business to target
        product_category: Product category to promote
        location: Specific location (city, state)
        state: State to target
        region: Region to target (e.g., "Southeast", "West Coast")
        
    Returns:
        DataFrame with target businesses and recommendations
    """
    # Filter by location if provided
    filtered_df = df.copy()
    
    if location:
        if "location" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["location"].str.contains(location, case=False, na=False)]
        elif "city" in filtered_df.columns and "state" in filtered_df.columns:
            city, state_part = location.split(",") if "," in location else (location, "")
            filtered_df = filtered_df[
                filtered_df["city"].str.contains(city.strip(), case=False, na=False)
            ]
    elif state:
        if "state" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["state"].str.contains(state, case=False, na=False)]
        elif "location" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["location"].str.contains(state, case=False, na=False)]
    
    # Find businesses of the target category
    target_businesses = filtered_df[filtered_df["business_category"] == business_category].copy()
    
    # Find businesses that DON'T currently buy this product category
    customers = target_businesses["customer_id"].unique()
    targets = []
    
    for customer_id in customers:
        customer_data = filtered_df[filtered_df["customer_id"] == customer_id]
        buys_product = (customer_data["product_category"] == product_category).any()
        
        if not buys_product:
            # Get customer info
            customer_info = customer_data.iloc[0]
            
            # Find what products they DO buy
            products_bought = customer_data["product_category"].unique().tolist()
            
            # Find similar products to recommend
            similar_products = find_similar_products(filtered_df, product_category, n_similar=3)
            
            # Get location
            if "location" in customer_info:
                loc = customer_info["location"]
            elif "city" in customer_info and "state" in customer_info:
                loc = f"{customer_info['city']}, {customer_info['state']}"
            else:
                loc = "Unknown"
            
            targets.append({
                "customer_id": customer_id,
                "business_category": business_category,
                "location": loc,
                "current_products": ", ".join(products_bought),
                "recommended_product": product_category,
                "similar_products": ", ".join(similar_products),
                "total_revenue": customer_data["sales_amount"].sum(),
                "product_diversity": len(products_bought),
                "opportunity_score": len(products_bought)  # Lower = more opportunity
            })
    
    if targets:
        targets_df = pd.DataFrame(targets)
        targets_df = targets_df.sort_values("opportunity_score")
        return targets_df
    else:
        return pd.DataFrame(columns=[
            "customer_id", "business_category", "location", "current_products",
            "recommended_product", "similar_products", "total_revenue",
            "product_diversity", "opportunity_score"
        ])


def analyze_regional_preferences(
    df: pd.DataFrame
) -> Dict:
    """
    Analyze product preferences by region/state
    
    Args:
        df: Sales DataFrame with location data
        
    Returns:
        Dictionary with regional product preferences
    """
    if "state" not in df.columns and "location" not in df.columns:
        return {}
    
    # Create state column if needed
    if "state" not in df.columns and "location" in df.columns:
        df = df.copy()
        # Extract state from location (format: "City, State")
        df["state"] = df["location"].astype(str).str.split(",").str[-1].str.strip()
        df["state"] = df["state"].replace("nan", "")
    
    # Group by state and product category
    regional_prefs = df.groupby(["state", "product_category"]).agg({
        "sales_amount": "sum",
        "customer_id": "nunique"
    }).reset_index()
    
    regional_prefs.columns = ["state", "product_category", "total_revenue", "num_businesses"]
    
    # Get top products by state
    top_products_by_state = {}
    for state in regional_prefs["state"].unique():
        state_data = regional_prefs[regional_prefs["state"] == state]
        top_products = state_data.nlargest(5, "total_revenue")
        top_products_by_state[state] = top_products[["product_category", "total_revenue", "num_businesses"]].to_dict("records")
    
    return {
        "top_products_by_state": top_products_by_state,
        "regional_data": regional_prefs
    }


def generate_outreach_list(
    df: pd.DataFrame,
    business_category: str,
    product_category: str,
    location_filter: str = None,
    max_results: int = 50
) -> pd.DataFrame:
    """
    Generate a list of businesses for automated outreach
    
    Args:
        df: Sales DataFrame
        business_category: Business category to target
        product_category: Product category to promote
        location_filter: Optional location filter (state or city, state)
        max_results: Maximum number of results
        
    Returns:
        DataFrame ready for outreach
    """
    targets = find_target_businesses_for_outreach(
        df,
        business_category=business_category,
        product_category=product_category,
        location=location_filter
    )
    
    # Add outreach-specific columns
    if len(targets) > 0:
        targets["outreach_priority"] = targets["opportunity_score"].rank(ascending=True)
        targets["personalization_note"] = (
            f"Similar {business_category}s in your area are purchasing {product_category}. "
            f"You currently purchase: {targets['current_products']}"
        )
        
        return targets.head(max_results)
    else:
        return targets


def generate_email_template(
    customer_id: str,
    business_category: str,
    product_category: str,
    location: str,
    current_products: str,
    similar_products: str
) -> str:
    """
    Generate personalized email template for outreach
    
    Args:
        customer_id: Customer ID/name
        business_category: Their business category
        product_category: Product to recommend
        location: Their location
        current_products: Products they currently buy
        similar_products: Similar products to recommend
        
    Returns:
        Email template string
    """
    template = f"""
Subject: Product Recommendation for {customer_id}

Dear {customer_id},

We noticed that other {business_category}s in {location} are finding great success with our {product_category} line.

Based on your current product mix ({current_products}), we believe {product_category} would be an excellent addition to your inventory.

Other similar products that might interest you:
{similar_products}

Would you like to learn more about our {product_category} offerings? We'd be happy to provide samples or a personalized consultation.

Best regards,
Your Sales Team
"""
    return template.strip()


def export_outreach_data(
    targets_df: pd.DataFrame,
    format: str = "csv"
) -> str:
    """
    Export outreach data in various formats
    
    Args:
        targets_df: DataFrame with target businesses
        format: Export format ('csv', 'json', 'email_list')
        
    Returns:
        Exported data as string
    """
    if format == "csv":
        return targets_df.to_csv(index=False)
    elif format == "json":
        return targets_df.to_json(orient="records", indent=2)
    elif format == "email_list":
        # Export as email list
        emails = []
        for _, row in targets_df.iterrows():
            email = generate_email_template(
                row["customer_id"],
                row["business_category"],
                row["recommended_product"],
                row["location"],
                row["current_products"],
                row["similar_products"]
            )
            emails.append(email)
        return "\n\n" + "="*80 + "\n\n".join(emails)
    else:
        return targets_df.to_string()


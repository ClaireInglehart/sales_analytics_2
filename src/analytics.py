"""
Analytics module for calculating business-product category relationships
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from datetime import datetime


def calculate_category_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate cross-tabulation matrix: Business Category × Product Category
    
    Args:
        df: DataFrame with business_category and product_category columns
        
    Returns:
        Pivot table with business categories as rows, product categories as columns
    """
    if "business_category" not in df.columns or "product_category" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'business_category' and 'product_category' columns"
        )
    
    # Create pivot table with revenue sums
    matrix = pd.pivot_table(
        df,
        values="sales_amount",
        index="business_category",
        columns="product_category",
        aggfunc="sum",
        fill_value=0,
    )
    
    return matrix


def calculate_transaction_counts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate transaction counts by business-product category combination
    
    Args:
        df: DataFrame with business_category and product_category columns
        
    Returns:
        Pivot table with transaction counts
    """
    if "business_category" not in df.columns or "product_category" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'business_category' and 'product_category' columns"
        )
    
    # Add count column
    df_count = df.copy()
    df_count["count"] = 1
    
    matrix = pd.pivot_table(
        df_count,
        values="count",
        index="business_category",
        columns="product_category",
        aggfunc="count",
        fill_value=0,
    )
    
    return matrix


def calculate_average_transaction_value(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate average transaction value by business-product category combination
    
    Args:
        df: DataFrame with business_category and product_category columns
        
    Returns:
        Pivot table with average transaction values
    """
    if "business_category" not in df.columns or "product_category" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'business_category' and 'product_category' columns"
        )
    
    matrix = pd.pivot_table(
        df,
        values="sales_amount",
        index="business_category",
        columns="product_category",
        aggfunc="mean",
        fill_value=0,
    )
    
    return matrix


def get_top_combinations(
    df: pd.DataFrame, n: int = 10, metric: str = "revenue"
) -> pd.DataFrame:
    """
    Get top N business-product category combinations
    
    Args:
        df: DataFrame with business_category and product_category columns
        n: Number of top combinations to return
        metric: Metric to rank by ('revenue', 'count', 'avg_value')
        
    Returns:
        DataFrame with top combinations
    """
    if "business_category" not in df.columns or "product_category" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'business_category' and 'product_category' columns"
        )
    
    # Group by combination
    grouped = df.groupby(["business_category", "product_category"]).agg(
        {
            "sales_amount": ["sum", "mean", "count"],
        }
    )
    grouped.columns = ["total_revenue", "avg_value", "transaction_count"]
    grouped = grouped.reset_index()
    
    # Select metric for ranking
    if metric == "revenue":
        sort_col = "total_revenue"
    elif metric == "count":
        sort_col = "transaction_count"
    elif metric == "avg_value":
        sort_col = "avg_value"
    else:
        sort_col = "total_revenue"
    
    # Sort and get top N
    top = grouped.nlargest(n, sort_col)
    
    return top


def identify_opportunities(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify business categories that buy few product categories (expansion opportunities)
    
    Args:
        df: DataFrame with business_category and product_category columns
        
    Returns:
        DataFrame with opportunity analysis
    """
    if "business_category" not in df.columns or "product_category" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'business_category' and 'product_category' columns"
        )
    
    # Count unique product categories per business category
    business_product_counts = (
        df.groupby("business_category")["product_category"]
        .nunique()
        .reset_index()
        .rename(columns={"product_category": "product_categories_bought"})
    )
    
    # Get total unique product categories available
    total_product_categories = df["product_category"].nunique()
    
    # Calculate opportunity score (inverse of coverage)
    business_product_counts["total_product_categories"] = total_product_categories
    business_product_counts["opportunity_score"] = (
        total_product_categories - business_product_counts["product_categories_bought"]
    ) / total_product_categories
    
    # Sort by opportunity score
    business_product_counts = business_product_counts.sort_values(
        "opportunity_score", ascending=False
    )
    
    return business_product_counts


def calculate_trends(df: pd.DataFrame, period: str = "M") -> pd.DataFrame:
    """
    Calculate trends over time by business-product category combination
    
    Args:
        df: DataFrame with transaction_date, business_category, and product_category
        period: Time period for aggregation ('D', 'W', 'M', 'Q', 'Y')
        
    Returns:
        DataFrame with time series data
    """
    if "transaction_date" not in df.columns:
        raise ValueError("DataFrame must contain 'transaction_date' column")
    
    if "business_category" not in df.columns or "product_category" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'business_category' and 'product_category' columns"
        )
    
    # Ensure transaction_date is datetime
    df = df.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    
    # Create period column
    df["period"] = df["transaction_date"].dt.to_period(period)
    
    # Group by period and categories
    trends = (
        df.groupby(["period", "business_category", "product_category"])["sales_amount"]
        .sum()
        .reset_index()
    )
    
    # Convert period to string for easier handling
    trends["period"] = trends["period"].astype(str)
    
    return trends


def get_summary_statistics(df: pd.DataFrame) -> Dict:
    """
    Get summary statistics for the sales data
    
    Args:
        df: Sales DataFrame
        
    Returns:
        Dictionary with summary statistics
    """
    stats = {
        "total_revenue": df["sales_amount"].sum(),
        "total_transactions": len(df),
        "unique_customers": df["customer_id"].nunique(),
        "unique_products": df["product_id"].nunique(),
        "unique_business_categories": df["business_category"].nunique()
        if "business_category" in df.columns
        else 0,
        "unique_product_categories": df["product_category"].nunique(),
        "average_transaction_value": df["sales_amount"].mean(),
        "date_range": {
            "start": df["transaction_date"].min().strftime("%Y-%m-%d")
            if "transaction_date" in df.columns
            else None,
            "end": df["transaction_date"].max().strftime("%Y-%m-%d")
            if "transaction_date" in df.columns
            else None,
        },
    }
    
    return stats


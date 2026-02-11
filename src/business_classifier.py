"""
Business classification module for mapping customers to business categories
"""

import pandas as pd
from typing import Dict, Optional, Union
import config


def load_business_mapping(file_path: Union[str, object]) -> Dict[str, str]:
    """
    Load business category mapping from CSV file or file-like object
    
    Expected CSV format:
    customer_id,business_category
    
    Args:
        file_path: Path to CSV mapping file or file-like object (e.g., from Streamlit uploader)
        
    Returns:
        Dictionary mapping customer_id to business_category
    """
    try:
        df = pd.read_csv(file_path)
        
        # Handle different column name variations
        customer_col = None
        category_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if "customer" in col_lower or "client" in col_lower:
                customer_col = col
            if "business" in col_lower or "category" in col_lower:
                category_col = col
        
        if customer_col is None or category_col is None:
            raise ValueError(
                f"CSV must contain customer and business category columns. "
                f"Found: {', '.join(df.columns)}"
            )
        
        mapping = dict(zip(df[customer_col].astype(str), df[category_col].astype(str)))
        return mapping
    except Exception as e:
        raise ValueError(f"Error loading business mapping file: {str(e)}")


def classify_by_keywords(customer_name: str) -> Optional[str]:
    """
    Classify business category based on keywords in customer name
    
    Args:
        customer_name: Name or ID of the customer
        
    Returns:
        Business category if matched, None otherwise
    """
    customer_lower = str(customer_name).lower()
    
    # Check each category's keywords
    for category, keywords in config.BUSINESS_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in customer_lower:
                return category
    
    return None


def create_business_mapping(
    customer_ids: list,
    mapping_file: Optional[str] = None,
    use_keywords: bool = True,
) -> Dict[str, str]:
    """
    Create business category mapping for a list of customers
    
    Args:
        customer_ids: List of customer IDs/names
        mapping_file: Optional path to CSV mapping file
        use_keywords: Whether to use keyword-based classification as fallback
        
    Returns:
        Dictionary mapping customer_id to business_category
    """
    mapping = {}
    
    # Load from file if provided
    if mapping_file:
        file_mapping = load_business_mapping(mapping_file)
        mapping.update(file_mapping)
    
    # Fill in missing classifications using keywords
    if use_keywords:
        for customer_id in customer_ids:
            if customer_id not in mapping:
                classified = classify_by_keywords(customer_id)
                if classified:
                    mapping[customer_id] = classified
                else:
                    mapping[customer_id] = "Other"
    
    # Ensure all customers have a category
    for customer_id in customer_ids:
        if customer_id not in mapping:
            mapping[customer_id] = "Other"
    
    return mapping


def get_unique_customers(df: pd.DataFrame) -> list:
    """
    Extract unique customer IDs from sales DataFrame
    
    Args:
        df: Sales DataFrame
        
    Returns:
        List of unique customer IDs
    """
    if "customer_id" not in df.columns:
        raise ValueError("DataFrame must contain 'customer_id' column")
    
    return df["customer_id"].unique().tolist()


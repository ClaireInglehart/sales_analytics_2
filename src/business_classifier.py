"""
Business classification module for mapping customers to business categories
"""

import pandas as pd
from typing import Dict, Optional, Tuple, Union
import config

# Mapping: customer_id -> (business_category, business_sub_category or None)
BusinessMappingType = Dict[str, Tuple[str, Optional[str]]]


def load_business_mapping(file_path: Union[str, object]) -> BusinessMappingType:
    """
    Load business category mapping from CSV file or file-like object.

    Expected CSV format:
    customer_id,business_category[,business_sub_category]

    Args:
        file_path: Path to CSV mapping file or file-like object (e.g., from Streamlit uploader)

    Returns:
        Dictionary mapping customer_id to (business_category, business_sub_category or None).
        If business_sub_category column is missing or blank, sub_category is None.
    """
    try:
        df = pd.read_csv(file_path)

        # Handle different column name variations
        customer_col = None
        category_col = None
        sub_category_col = None

        for col in df.columns:
            col_lower = col.lower()
            if "customer" in col_lower or "client" in col_lower:
                customer_col = col
            if "business" in col_lower and "sub" not in col_lower and "category" in col_lower:
                category_col = col
            if "sub" in col_lower and ("category" in col_lower or "business" in col_lower):
                sub_category_col = col

        if customer_col is None or category_col is None:
            raise ValueError(
                f"CSV must contain customer and business category columns. "
                f"Found: {', '.join(df.columns)}"
            )

        mapping: BusinessMappingType = {}
        for _, row in df.iterrows():
            cid = str(row[customer_col]).strip()
            cat = str(row[category_col]).strip() if pd.notna(row[category_col]) else ""
            sub = None
            if sub_category_col is not None and sub_category_col in df.columns:
                val = row[sub_category_col]
                if pd.notna(val) and str(val).strip():
                    sub = str(val).strip()
            mapping[cid] = (cat, sub)
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
) -> BusinessMappingType:
    """
    Create business category mapping for a list of customers.

    Args:
        customer_ids: List of customer IDs/names
        mapping_file: Optional path to CSV mapping file
        use_keywords: Whether to use keyword-based classification as fallback

    Returns:
        Dictionary mapping customer_id to (business_category, business_sub_category or None).
        Auto-classify sets sub_category to None.
    """
    mapping: BusinessMappingType = {}

    # Load from file if provided
    if mapping_file:
        file_mapping = load_business_mapping(mapping_file)
        mapping.update(file_mapping)

    # Fill in missing classifications using keywords (sub_category always None)
    if use_keywords:
        for customer_id in customer_ids:
            if customer_id not in mapping:
                classified = classify_by_keywords(customer_id)
                mapping[customer_id] = (classified if classified else "Other", None)

    # Ensure all customers have a category
    for customer_id in customer_ids:
        if customer_id not in mapping:
            mapping[customer_id] = ("Other", None)

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


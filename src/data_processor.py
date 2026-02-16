"""
Data processing module for loading and cleaning sales data
"""

import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Union
import config


def load_sales_data(file_path: Union[str, object]) -> pd.DataFrame:
    """
    Load sales data from CSV file or file-like object
    
    Args:
        file_path: Path to the CSV file or file-like object (e.g., from Streamlit uploader)
        
    Returns:
        DataFrame with sales data
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise ValueError(f"Error loading CSV file: {str(e)}")


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to match expected format
    
    Args:
        df: DataFrame with potentially non-standard column names
        
    Returns:
        DataFrame with normalized column names
    """
    df = df.copy()
    column_mapping = {}
    
    for standard_name, possible_names in config.COLUMN_MAPPINGS.items():
        for col in df.columns:
            if col.lower() in [name.lower() for name in possible_names]:
                column_mapping[col] = standard_name
                break
    
    df = df.rename(columns=column_mapping)
    return df


def validate_columns(df: pd.DataFrame) -> List[str]:
    """
    Validate that required columns are present
    
    Args:
        df: DataFrame to validate
        
    Returns:
        List of missing columns (empty if all present)
    """
    missing_columns = []
    for col in config.REQUIRED_COLUMNS:
        if col not in df.columns:
            missing_columns.append(col)
    return missing_columns


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse transaction_date column to datetime
    
    Args:
        df: DataFrame with transaction_date column
        
    Returns:
        DataFrame with parsed dates
    """
    df = df.copy()
    if "transaction_date" in df.columns:
        for date_format in config.DATE_FORMATS:
            try:
                df["transaction_date"] = pd.to_datetime(
                    df["transaction_date"], format=date_format, errors="coerce"
                )
                if df["transaction_date"].notna().sum() > 0:
                    break
            except:
                continue
        # Fallback to pandas auto-detection
        if df["transaction_date"].isna().all():
            df["transaction_date"] = pd.to_datetime(
                df["transaction_date"], errors="coerce"
            )
    return df


def clean_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean sales data: remove nulls, convert types, etc.
    
    Args:
        df: Raw sales DataFrame
        
    Returns:
        Cleaned DataFrame
    """
    df = df.copy()
    
    # Remove rows with missing critical data
    df = df.dropna(subset=["customer_id", "product_id", "sales_amount"])
    
    # Ensure sales_amount is numeric
    if "sales_amount" in df.columns:
        df["sales_amount"] = pd.to_numeric(df["sales_amount"], errors="coerce")
        df = df.dropna(subset=["sales_amount"])
        # Remove negative or zero amounts (assuming they're errors)
        df = df[df["sales_amount"] > 0]
    
    # Ensure product_category is string
    if "product_category" in df.columns:
        df["product_category"] = df["product_category"].astype(str).str.strip()
        df = df[df["product_category"] != "nan"]
    
    # Ensure customer_id is string
    if "customer_id" in df.columns:
        df["customer_id"] = df["customer_id"].astype(str).str.strip()
    
    # Ensure product_id is string
    if "product_id" in df.columns:
        df["product_id"] = df["product_id"].astype(str).str.strip()
    
    return df


def process_sales_data(file_path: Union[str, object]) -> pd.DataFrame:
    """
    Complete pipeline: load, normalize, validate, parse dates, and clean
    
    Args:
        file_path: Path to CSV file or file-like object (e.g., from Streamlit uploader)
        
    Returns:
        Processed DataFrame ready for analysis
    """
    # Load data
    df = load_sales_data(file_path)
    
    # Normalize column names
    df = normalize_column_names(df)
    
    # Validate columns
    missing = validate_columns(df)
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(missing)}. "
            f"Found columns: {', '.join(df.columns)}"
        )
    
    # Parse dates
    df = parse_dates(df)
    
    # Clean data
    df = clean_sales_data(df)
    
    return df


def merge_business_categories(
    df: pd.DataFrame, business_mapping: Dict[str, tuple]
) -> pd.DataFrame:
    """
    Merge business category information into sales data.

    Args:
        df: Sales DataFrame
        business_mapping: Dictionary mapping customer_id to (business_category, business_sub_category or None).
                          From load_business_mapping or create_business_mapping.

    Returns:
        DataFrame with business_category and optionally business_sub_category columns added.
        When sub_category is None, business_sub_category is set to "Unspecified".
    """
    df = df.copy()

    def get_category(cid):
        pair = business_mapping.get(str(cid), ("Unknown", None))
        return pair[0]

    def get_sub_category(cid):
        pair = business_mapping.get(str(cid), ("Unknown", None))
        return pair[1] if pair[1] is not None else "Unspecified"

    df["business_category"] = df["customer_id"].map(get_category)
    df["business_sub_category"] = df["customer_id"].map(get_sub_category)
    return df


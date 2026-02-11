"""
Configuration settings for the Sales Analytics Dashboard
"""

# Default business categories
DEFAULT_BUSINESS_CATEGORIES = [
    "Retail",
    "Healthcare",
    "Manufacturing",
    "Technology",
    "Finance",
    "Education",
    "Real Estate",
    "Hospitality",
    "Transportation",
    "Construction",
    "Food & Beverage",
    "Professional Services",
    "Other"
]

# Expected column names in sales data
REQUIRED_COLUMNS = [
    "customer_id",
    "product_id",
    "product_category",
    "transaction_date",
    "sales_amount"
]

# Column mappings (for flexibility if user has different column names)
COLUMN_MAPPINGS = {
    "customer_id": ["customer_id", "customer", "client_id", "client"],
    "product_id": ["product_id", "product", "item_id", "item"],
    "product_category": ["product_category", "category", "product_type"],
    "transaction_date": ["transaction_date", "date", "sale_date", "purchase_date"],
    "sales_amount": ["sales_amount", "amount", "revenue", "price", "total"]
}

# Date format for parsing
DATE_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%m/%d/%Y %H:%M:%S"
]

# Visualization settings
HEATMAP_COLORS = "YlOrRd"
CHART_HEIGHT = 500
CHART_WIDTH = 800

# Business classification keywords (for auto-classification)
BUSINESS_KEYWORDS = {
    "Retail": ["retail", "store", "shop", "market", "outlet", "merchant"],
    "Healthcare": ["health", "medical", "hospital", "clinic", "pharmacy", "doctor", "nurse"],
    "Manufacturing": ["manufacturing", "factory", "production", "industrial", "manufacturer"],
    "Technology": ["tech", "software", "IT", "computer", "digital", "technology", "tech company"],
    "Finance": ["bank", "financial", "finance", "investment", "accounting", "insurance"],
    "Education": ["school", "university", "education", "college", "academy", "learning"],
    "Real Estate": ["real estate", "property", "realty", "housing", "construction"],
    "Hospitality": ["hotel", "restaurant", "hospitality", "catering", "tourism"],
    "Transportation": ["transport", "logistics", "shipping", "delivery", "freight"],
    "Construction": ["construction", "contractor", "building", "architect"],
    "Food & Beverage": ["food", "restaurant", "cafe", "beverage", "catering"],
    "Professional Services": ["consulting", "legal", "law", "advisory", "services"]
}


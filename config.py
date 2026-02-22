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
    "sales_amount": ["sales_amount", "amount", "revenue", "price", "total"],
    "city": ["city", "customer_city", "buyer_city"],
    "state": ["state", "customer_state", "buyer_state", "province"],
    "location": ["location", "city_state", "full_location"]
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

# Business sub-categories by category (for validation and UI dropdowns).
# Other has no sub-categories (empty list).
BUSINESS_SUB_CATEGORIES = {
    "Retail": [
        "Department Store",
        "Specialty Store",
        "E-commerce",
        "Convenience Store",
        "Boutique",
        "Supermarket",
        "Hardware Store",
        "Gift Shop",
        "Bookstore",
        "Home Goods",
        "Apparel",
        "Pet Store",
    ],
    "Healthcare": [
        "Hospital",
        "Clinic",
        "Pharmacy",
        "Dental",
        "Mental Health",
        "Home Care",
    ],
    "Manufacturing": [
        "Automotive",
        "Electronics",
        "Chemicals",
        "Food Processing",
        "Textiles",
        "Machinery",
    ],
    "Technology": [
        "Software/SaaS",
        "Hardware",
        "IT Services",
        "Telecom",
        "Semiconductors",
    ],
    "Finance": [
        "Banking",
        "Insurance",
        "Investment",
        "Accounting",
        "Fintech",
    ],
    "Education": [
        "K-12",
        "Higher Ed",
        "Vocational",
        "Corporate Training",
        "E-learning",
    ],
    "Real Estate": [
        "Residential",
        "Commercial",
        "Property Management",
        "Development",
    ],
    "Hospitality": [
        "Hotel",
        "Restaurant",
        "Cafe",
        "Catering",
        "Travel/Tourism",
    ],
    "Transportation": [
        "Freight",
        "Passenger",
        "Logistics",
        "Fleet",
    ],
    "Construction": [
        "Residential",
        "Commercial",
        "Civil/Infrastructure",
        "Specialty Trades",
    ],
    "Food & Beverage": [
        "Restaurant",
        "Cafe",
        "Catering",
        "Distribution",
        "Manufacturing",
    ],
    "Professional Services": [
        "Legal",
        "Consulting",
        "Accounting",
        "Marketing",
        "HR",
    ],
    "Other": [],
}

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


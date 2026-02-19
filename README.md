# Sales Analytics Dashboard

A web-based application for analyzing sales data to identify which business categories purchase which product categories, enabling data-driven targeting decisions for future growth.

## Features

- **CSV Data Upload**: Upload your sales data via a simple drag-and-drop interface
- **Business Classification**: 
  - Upload a business mapping file to classify customers
  - Use auto-classification based on keywords in customer names
  - Manual classification interface
- **Interactive Visualizations**:
  - **Category Matrix Heatmap**: Visual representation of revenue by Business Category × Product Category
  - **Top Combinations**: Identify highest-performing business-product category combinations
  - **Growth Opportunities**: Find business categories that buy few products (expansion opportunities)
  - **Trend Analysis**: Time-series view of category relationships over time
- **Data Export**: Download analysis results as CSV files
- **Filtering**: Filter by date range, business category, and product category

## Installation

1. Clone or download this repository

2. **Option A: Install directly (recommended for quick start)**
   ```bash
   python3 -m pip install -r requirements.txt
   ```

3. **Option B: Use a virtual environment (recommended for isolation)**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   # venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

## Usage

1. Start the Streamlit application:
   ```bash
   # If using virtual environment (pip is available):
   streamlit run app.py
   
   # If installing directly (use python3 -m):
   python3 -m streamlit run app.py
   ```

2. The dashboard will open in your web browser (typically at `http://localhost:8501`)

3. **Upload your data**:
   - Use the sidebar to upload a CSV file with your sales data
   - Required columns: `customer_id`, `product_id`, `product_category`, `transaction_date`, `sales_amount`
   - Or check "Use Sample Data" to explore with example data

4. **Classify businesses**:
   - Upload a business mapping CSV file with columns: `customer_id`, `business_category`, and optionally `business_sub_category`
   - Or click "Auto-classify Businesses" to use keyword-based classification
   - The system will automatically classify customers based on keywords in their names

5. **Explore insights**:
   - View the overview statistics
   - Examine the category matrix heatmap
   - Identify top combinations and growth opportunities
   - Analyze trends over time
   - Export results for further analysis

## Data Format

### Sales Data CSV

Your sales data CSV should contain the following columns:

- `customer_id`: Unique identifier for each customer
- `product_id`: Unique identifier for each product
- `product_category`: Category of the product (e.g., "Electronics", "Software", "Office Supplies")
- `transaction_date`: Date of the transaction (various formats supported)
- `sales_amount`: Revenue amount for the transaction

Example:
```csv
customer_id,product_id,product_category,transaction_date,sales_amount
CUST001,PROD001,Electronics,2024-01-15,1250.50
CUST002,PROD002,Software,2024-01-16,3500.00
```

### Business Mapping CSV (Optional)

If you want to manually specify business categories, upload a CSV with:

- `customer_id`: Customer identifier (must match sales data)
- `business_category`: Business category (e.g., "Retail", "Technology", "Healthcare")
- `business_sub_category`: (Optional) Finer segment within the category (e.g., "Hardware Store", "Gift Shop"). If omitted or blank, sub-category is treated as "Unspecified".

Example:
```csv
customer_id,business_category,business_sub_category
CUST001,Retail,Hardware Store
CUST002,Technology,Software/SaaS
CUST003,Retail,Gift Shop
```

## Business Categories and Sub-Categories

The system supports the following default business categories:
- Retail
- Healthcare
- Manufacturing
- Technology
- Finance
- Education
- Real Estate
- Hospitality
- Transportation
- Construction
- Food & Beverage
- Professional Services
- Other

Each category (except Other) has optional **sub-categories** for finer segmentation—e.g. Retail includes Hardware Store, Gift Shop, Bookstore, Home Goods, Apparel, Pet Store, and others. Sub-categories are defined in `config.py` (`BUSINESS_SUB_CATEGORIES`) and can be used in the business mapping CSV. When sub-categories are present, the dashboard shows a sub-category filter and optional views (e.g. heatmap and top combinations by sub-category).

## Project Structure

```
sales-analytics/
├── app.py                 # Main Streamlit application
├── src/
│   ├── __init__.py       # Package initialization
│   ├── data_processor.py  # CSV loading and data cleaning
│   ├── business_classifier.py  # Business category classification
│   └── analytics.py       # Analysis calculations
├── config.py              # Configuration settings
├── data/
│   ├── sample_sales.csv   # Example sales data
│   └── business_mapping.csv  # Example business mapping
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Requirements

- Python 3.8+
- pandas >= 2.0.0
- streamlit >= 1.28.0
- plotly >= 5.17.0
- openpyxl >= 3.1.0

## Troubleshooting

**Issue**: "Missing required columns" error
- **Solution**: Ensure your CSV has the required columns. Column names are case-insensitive and flexible (e.g., "customer" or "client_id" will work for "customer_id")

**Issue**: Business categories not showing
- **Solution**: Upload a business mapping file or use the "Auto-classify Businesses" button in the sidebar

**Issue**: Date parsing errors
- **Solution**: The system supports multiple date formats. If your dates aren't parsing correctly, try formats like YYYY-MM-DD or MM/DD/YYYY

## License

This project is provided as-is for internal use.


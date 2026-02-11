# Faire Wholesale Data Guide for Sales Analytics

## Overview
This guide explains what customer and sales information you can typically access as a vendor on Faire Wholesale, and how to format it for use with this Sales Analytics Dashboard.

## What Information Faire Typically Provides to Vendors

Based on typical B2B wholesale platforms, Faire Wholesale vendors usually have access to:

### 1. **Order/Sales Data**
- Order ID
- Order date
- Product SKU/ID
- Product name
- Product category (if you've categorized your products)
- Quantity sold
- Unit price
- Total order value
- Order status

### 2. **Customer/Buyer Information**
- Customer/buyer name or ID
- Business name (store name)
- Business type/category (e.g., "Boutique", "Gift Shop", "Home Goods Store")
- Location (city, state, country)
- Customer email (sometimes)
- Account creation date
- Order frequency/history

### 3. **Analytics & Reports**
- Sales by product category
- Sales by customer type
- Geographic sales distribution
- Repeat customer metrics
- Seasonal trends

## How to Export Data from Faire

### Step 1: Access Your Vendor Dashboard
1. Log into your Faire vendor account
2. Navigate to **Analytics** or **Reports** section
3. Look for options like:
   - "Export Orders"
   - "Sales Report"
   - "Download CSV"
   - "Export Data"

### Step 2: Export Order Data
Most platforms allow you to:
- Select a date range
- Choose which fields to include
- Export as CSV or Excel

### Step 3: Export Customer Data
You may need to export separately:
- Customer list or buyer directory
- This should include business names and types

## Required Data Fields for This Dashboard

To use your Sales Analytics Dashboard, you'll need CSV files with these columns:

### Sales Data CSV (`sales_data.csv`)
Required columns:
- `customer_id` - Unique identifier for each buyer/store
- `product_id` - Unique identifier for each product/SKU
- `product_category` - Category of product (e.g., "Home Decor", "Jewelry", "Apparel")
- `transaction_date` - Date of the order/sale
- `sales_amount` - Total revenue for that transaction

**Example:**
```csv
customer_id,product_id,product_category,transaction_date,sales_amount
STORE001,SKU-12345,Home Decor,2024-01-15,1250.50
STORE002,SKU-67890,Jewelry,2024-01-16,3500.00
STORE001,SKU-11111,Home Decor,2024-01-18,890.25
```

### Business Mapping CSV (`business_mapping.csv`) - Optional
If Faire provides business type information:
- `customer_id` - Must match customer_id in sales data
- `business_category` - Type of business (e.g., "Retail Boutique", "Gift Shop", "Home Goods Store")

**Example:**
```csv
customer_id,business_category
STORE001,Retail Boutique
STORE002,Gift Shop
STORE003,Home Goods Store
```

## Mapping Faire Data to Dashboard Format

### If Faire Exports Include Business Categories:
1. Export your orders CSV from Faire
2. Export your customer/buyer list CSV (if separate)
3. Map the columns:
   - Faire's "Buyer Name" or "Store Name" → `customer_id`
   - Faire's "Product SKU" → `product_id`
   - Your product categories → `product_category`
   - Faire's "Order Date" → `transaction_date`
   - Faire's "Order Total" or "Line Item Total" → `sales_amount`
   - Faire's "Business Type" → `business_category` (in mapping file)

### If Faire Doesn't Provide Business Categories:
1. Export your orders CSV
2. Export your customer list (with business names)
3. Use the dashboard's **Auto-classify** feature:
   - Upload sales data
   - Click "Auto-classify Businesses" in the sidebar
   - The system will classify businesses based on keywords in their names
4. Or manually create a mapping file with business categories

## Common Faire Business Categories

When classifying your Faire buyers, common categories include:
- **Retail Boutique** - Small independent retail stores
- **Gift Shop** - Stores specializing in gifts
- **Home Goods Store** - Home decor and furnishings
- **Jewelry Store** - Jewelry retailers
- **Apparel Store** - Clothing retailers
- **Beauty/Cosmetics** - Beauty product retailers
- **Specialty Store** - Niche product retailers
- **Online Retailer** - E-commerce businesses
- **Pop-up Shop** - Temporary retail locations
- **Marketplace Vendor** - Other marketplace sellers

## Tips for Getting the Most from Your Data

1. **Regular Exports**: Export data monthly or quarterly to track trends
2. **Product Categorization**: Ensure your products are properly categorized in Faire
3. **Customer Notes**: If Faire allows notes on customers, use them to track business types
4. **Date Ranges**: Export data for meaningful time periods (e.g., last 12 months)
5. **Clean Data**: Remove cancelled orders or refunds before analysis

## What Insights You'll Get

Once you upload your Faire data, the dashboard will show you:

1. **Category Matrix**: Which business types buy which product categories
2. **Top Combinations**: Your best business-product category matches
3. **Growth Opportunities**: Business types buying few of your products (expansion targets)
4. **Trends**: How sales patterns change over time
5. **Targeting Insights**: Which business categories to focus marketing efforts on

## Next Steps

1. **Log into Faire** and explore the Analytics/Reports section
2. **Export your order data** for the last 6-12 months
3. **Export customer/buyer information** if available
4. **Format the data** according to the examples above
5. **Upload to the dashboard** and start analyzing!

## Need Help?

If Faire's export format is different from what's described here:
- Check Faire's vendor help documentation
- Contact Faire vendor support for export options
- The dashboard can handle various column name formats (it auto-detects common variations)

You can also manually adjust the CSV files to match the required format using Excel or Google Sheets.


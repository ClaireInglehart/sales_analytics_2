# Faire Sales Data Export Format Guide

## What Your CSV Export from Faire Should Look Like

When you export sales data from Faire Wholesale as a vendor, your CSV should include the following columns. The app is flexible and will recognize common variations of these column names.

### Required Columns (Minimum)

Your CSV **must** have these columns for the app to work:

| Column Name | Description | Example Values | Alternative Names Accepted |
|------------|-------------|----------------|---------------------------|
| `customer_id` | Unique identifier for each store/buyer | `CUST001`, `STORE-123`, `BookstoreNYC` | `customer`, `client_id`, `client` |
| `product_id` | Unique identifier for each product | `PROD-0001`, `SKU-123`, `HH-001` | `product`, `item_id`, `item`, `sku` |
| `product_category` | Category of the product | `Stickers, pins, & magnets`, `Stationery & writing`, `Party supplies`, `Women's accessories`, `Men's accessories` | `category`, `product_type` |
| `transaction_date` | Date of the sale | `2024-12-22`, `12/22/2024`, `2024-12-22 10:30:00` | `date`, `sale_date`, `purchase_date` |
| `sales_amount` | Revenue from the sale | `188.98`, `45.50`, `1200.00` | `amount`, `revenue`, `price`, `total` |

### Optional (But Recommended) Columns

These columns enhance the app's features (location-based recommendations, area analysis):

| Column Name | Description | Example Values | Alternative Names Accepted |
|------------|-------------|----------------|---------------------------|
| `product_name` | Name of the specific product | `Tote Bag`, `Funny Quote Sticker Pack`, `Gel Pen Set` | `product_name`, `item_name` |
| `city` | City where the buyer/store is located | `Boston`, `New York`, `Los Angeles` | `customer_city`, `buyer_city` |
| `state` | State where the buyer/store is located | `MA`, `NY`, `CA`, `Texas` | `customer_state`, `buyer_state`, `province` |
| `location` | Full location string | `Boston, MA`, `New York, NY` | `city_state`, `full_location` |

### Example CSV Format

Here's what your exported CSV from Faire should look like:

```csv
customer_id,product_id,product_category,product_name,transaction_date,sales_amount,city,state,location
CUST001,PROD-0001,Party supplies,Themed Party Kit,2024-12-22,188.98,Boston,MA,"Boston, MA"
CUST001,PROD-0002,Women's accessories,Hair Scrunchie Pack,2024-07-08,46.66,Boston,MA,"Boston, MA"
CUST002,PROD-0003,Stationery & writing,Gel Pen Set,2024-03-16,125.49,Charlotte,NC,"Charlotte, NC"
CUST003,PROD-0004,Stickers pins & magnets,Funny Quote Sticker Pack,2024-11-05,89.50,Los Angeles,CA,"Los Angeles, CA"
```

### What Faire Actually Exports

**Note:** The exact column names from Faire may vary. Here's what Faire typically exports:

**From Faire's Orders/Transactions Export:**
- Order ID / Transaction ID
- Customer Name / Store Name
- Product Name / SKU
- Product Category (if available)
- Order Date / Purchase Date
- Order Total / Revenue
- Shipping Address (City, State)
- Quantity
- Unit Price

**You may need to:**
1. **Rename columns** to match what the app expects (or use the alternative names)
2. **Add a `product_category` column** if Faire doesn't export it (you can map products to categories)
3. **Create `customer_id`** from customer/store names if Faire only gives you names
4. **Combine city and state** into a `location` column if you want location-based features

### Quick Mapping Guide

If your Faire export has different column names, here's how to map them:

| Faire Export Column | Map to App Column |
|---------------------|-------------------|
| `Store Name` or `Customer Name` | `customer_id` |
| `SKU` or `Product SKU` | `product_id` |
| `Product Name` | `product_name` |
| `Category` or `Product Category` | `product_category` |
| `Order Date` or `Purchase Date` | `transaction_date` |
| `Order Total` or `Revenue` | `sales_amount` |
| `Shipping City` | `city` |
| `Shipping State` | `state` |

### Product Categories from Faire

Make sure your `product_category` column uses these **exact** Faire categories:

- `Stickers, pins, & magnets`
- `Stationery & writing`
- `Party supplies`
- `Women's accessories`
- `Men's accessories`

### Date Format

The app accepts these date formats:
- `YYYY-MM-DD` (e.g., `2024-12-22`) ✅ **Recommended**
- `MM/DD/YYYY` (e.g., `12/22/2024`)
- `DD/MM/YYYY` (e.g., `22/12/2024`)
- `YYYY-MM-DD HH:MM:SS` (e.g., `2024-12-22 10:30:00`)

### Tips for Exporting from Faire

1. **Export all orders/transactions** - not just recent ones (for better analytics)
2. **Include customer/store information** - so you can identify business types
3. **Include product details** - product names and categories help with specific product analysis
4. **Include location data** - city/state enables location-based recommendations
5. **Export as CSV** - the app works best with CSV format

### If Your Export Doesn't Match

The app will try to automatically detect and map columns, but if it can't:
1. **Rename columns** in Excel/Google Sheets before uploading
2. **Add missing columns** manually (like `product_category` if Faire doesn't export it)
3. **Use the Business Mapping file** to add business categories if your sales data doesn't have them

### Need Help?

If your Faire export looks different, you can:
1. Upload it anyway - the app will try to auto-detect columns
2. Check the error messages - they'll tell you what's missing
3. Use the sample data format as a template


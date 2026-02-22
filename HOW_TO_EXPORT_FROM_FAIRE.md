# Step-by-Step Guide: Exporting Sales Data from Faire Wholesale

## Overview
This guide walks you through exporting your sales data from Faire Wholesale as a vendor, then formatting it for use with the Sales Analytics Dashboard.

---

## Step 1: Log into Faire as a Vendor

1. Go to **https://www.faire.com** and log in
2. Make sure you're logged in as a **vendor/brand** (not a retailer)
3. Navigate to your **Vendor Dashboard**

---

## Step 2: Access Your Orders/Sales Data

Faire typically provides sales data in one of these locations:

### Option A: Orders Page
1. Click on **"Orders"** or **"Sales"** in the main navigation
2. You should see a list of all orders from retailers

### Option B: Reports/Analytics Section
1. Look for **"Reports"**, **"Analytics"**, or **"Data"** in the navigation
2. Some vendors have a **"Sales Reports"** or **"Export Data"** section

### Option C: Account Settings
1. Go to **Settings** or **Account Settings**
2. Look for **"Data Export"**, **"Download Reports"**, or **"Export Orders"**

---

## Step 3: Export Your Data

### If Faire Has a Direct Export Button:

1. **Select Date Range** (if available)
   - Choose "All Time" or your desired date range
   - The more data, the better for analytics!

2. **Click "Export" or "Download"**
   - Look for buttons like:
     - "Export to CSV"
     - "Download Orders"
     - "Export Sales Data"
     - "Download Report"

3. **Wait for the file to download**
   - Faire may email you the file or download it directly
   - File name might be: `faire_orders.csv`, `sales_export.csv`, etc.

### If Faire Doesn't Have Direct Export:

**Manual Method:**
1. Go to your Orders page
2. Use your browser's "Select All" (Cmd/Ctrl + A)
3. Copy the data
4. Paste into Excel or Google Sheets
5. Save as CSV

**Note:** This is tedious for large datasets. Contact Faire support if you need bulk export.

---

## Step 4: Check What Columns Faire Exported

Open your downloaded CSV file and check what columns Faire included. Common Faire export columns:

### Typical Faire Export Columns:
- `Order ID` / `Transaction ID`
- `Order Date` / `Purchase Date` / `Date`
- `Store Name` / `Retailer Name` / `Customer Name`
- `Product Name` / `SKU` / `Item Name`
- `Product Category` (may or may not be included)
- `Quantity`
- `Unit Price` / `Price`
- `Order Total` / `Revenue` / `Amount`
- `Shipping Address` / `City` / `State`
- `Store Type` / `Retailer Type` (rarely included)

---

## Step 5: Map Faire Columns to App Format

You need to rename/add columns to match what the app expects. Here's the mapping:

### Required Mapping:

| Faire Column Name | Rename To | Notes |
|------------------|-----------|-------|
| `Store Name` or `Retailer Name` or `Customer Name` | `customer_id` | Use store name as ID, or create unique IDs |
| `SKU` or `Product SKU` or `Product ID` | `product_id` | If missing, use Product Name |
| `Product Category` | `product_category` | **IMPORTANT:** Must use exact Faire categories (see below) |
| `Order Date` or `Purchase Date` | `transaction_date` | Format: YYYY-MM-DD preferred |
| `Order Total` or `Revenue` or `Amount` | `sales_amount` | Total sale amount |

### Optional (But Recommended):

| Faire Column Name | Rename To | Notes |
|------------------|-----------|-------|
| `Product Name` | `product_name` | Specific product name |
| `Shipping City` or `City` | `city` | Buyer's city |
| `Shipping State` or `State` | `state` | Buyer's state |
| Create new column | `location` | Combine: `city, state` (e.g., "Boston, MA") |

---

## Step 6: Format Your CSV File

### Using Excel or Google Sheets:

1. **Open your Faire export CSV**

2. **Rename columns** to match the app format:
   - Select the header row
   - Rename columns as shown in Step 5

3. **Add missing columns** if needed:
   - **`product_category`**: If Faire didn't export this, you'll need to add it manually
     - Use these exact categories:
       - `Stickers, pins, & magnets`
       - `Stationery & writing`
       - `Party supplies`
       - `Women's accessories`
       - `Men's accessories`
   - **`location`**: Create by combining city and state
     - Formula: `=CONCATENATE(B2, ", ", C2)` (where B2=city, C2=state)

4. **Clean up the data**:
   - Remove any empty rows
   - Make sure dates are in format: `YYYY-MM-DD` (e.g., `2024-12-22`)
   - Make sure amounts are numbers (not text with $ signs)

5. **Save as CSV**:
   - File → Save As → CSV (UTF-8)

### Example Transformation:

**Before (Faire Export):**
```csv
Order Date,Store Name,Product Name,SKU,Order Total,Shipping City,Shipping State
2024-12-22,Bookstore NYC,Tote Bag,SKU-123,188.98,Boston,MA
2024-07-08,Gift Shop LA,Sticker Pack,SKU-456,46.66,Los Angeles,CA
```

**After (App Format):**
```csv
customer_id,product_id,product_category,product_name,transaction_date,sales_amount,city,state,location
Bookstore NYC,SKU-123,Women's accessories,Tote Bag,2024-12-22,188.98,Boston,MA,"Boston, MA"
Gift Shop LA,SKU-456,Stickers pins & magnets,Sticker Pack,2024-07-08,46.66,Los Angeles,CA,"Los Angeles, CA"
```

---

## Step 7: Handle Missing Product Categories

**If Faire doesn't export product categories**, you need to add them manually:

1. **Create a `product_category` column** in your CSV
2. **Map each product** to one of these categories:
   - `Stickers, pins, & magnets`
   - `Stationery & writing`
   - `Party supplies`
   - `Women's accessories`
   - `Men's accessories`

**Tips:**
- Use Excel's VLOOKUP or IF statements to auto-categorize
- Create a separate mapping table if you have many products
- You can also categorize by product name keywords

---

## Step 8: Upload to the App

1. **Open the Sales Analytics Dashboard** (http://localhost:8501)
2. **Go to the sidebar** → "Upload Sales Data"
3. **Click "Choose File"** and select your formatted CSV
4. **Click "Load Sales Data"**
5. The app will validate and process your data!

---

## Troubleshooting

### Problem: "Missing required columns"
**Solution:** Check that you renamed columns correctly. The app accepts alternative names (see `FAIRE_EXPORT_FORMAT.md`)

### Problem: "Date format error"
**Solution:** Make sure dates are in `YYYY-MM-DD` format (e.g., `2024-12-22`)

### Problem: "Product category not recognized"
**Solution:** Make sure categories match exactly:
- `Stickers, pins, & magnets` (note the comma and ampersand)
- `Stationery & writing`
- `Party supplies`
- `Women's accessories` (note the apostrophe)
- `Men's accessories` (note the apostrophe)

### Problem: "Faire doesn't export product categories"
**Solution:** 
1. Manually add a `product_category` column
2. Categorize products based on their names or your product catalog
3. Use Excel formulas to speed this up

### Problem: "Can't find export button in Faire"
**Solution:**
1. Contact Faire support: support@faire.com
2. Ask: "How do I export my sales/order data as a vendor?"
3. They may have a specific process or API access

---

## Quick Reference: Final CSV Format

Your final CSV should look like this:

```csv
customer_id,product_id,product_category,product_name,transaction_date,sales_amount,city,state,location
Bookstore NYC,SKU-123,Women's accessories,Tote Bag,2024-12-22,188.98,Boston,MA,"Boston, MA"
Gift Shop LA,SKU-456,Stickers pins & magnets,Sticker Pack,2024-07-08,46.66,Los Angeles,CA,"Los Angeles, CA"
```

**Required columns:** `customer_id`, `product_id`, `product_category`, `transaction_date`, `sales_amount`

**Optional columns:** `product_name`, `city`, `state`, `location`

---

## Need More Help?

- Check `FAIRE_EXPORT_FORMAT.md` for detailed column specifications
- The app will try to auto-detect columns if names are slightly different
- Contact Faire support if you can't find export functionality


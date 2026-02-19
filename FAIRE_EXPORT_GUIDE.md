# Step-by-Step Guide: Exporting Faire Data for Sales Analytics Dashboard

## Quick Start Checklist

- [ ] Export orders/sales data from Faire
- [ ] Export customer/buyer list (if available)
- [ ] Transform data to match dashboard format
- [ ] Upload to dashboard

---

## Step 1: Export Sales Data from Faire

### Where to Find It:
1. Log into your **Faire vendor dashboard**
2. Go to **"Orders"** or **"Sales"** section
3. Look for **"Export"** or **"Download"** button
4. Common locations:
   - Orders → Export Orders
   - Analytics → Sales Report → Export
   - Reports → Order History → Download CSV

### What to Export:
- **Date Range**: Last 6-12 months (or your desired period)
- **File Format**: CSV or Excel
- **Include**: All completed orders (exclude cancelled/refunded)

### What Columns Faire Typically Exports:
- Order ID / Order Number
- Order Date / Purchase Date
- Buyer Name / Store Name / Customer Name
- Product SKU / Product ID / Item ID
- Product Name
- Product Category (if you've categorized products)
- Quantity
- Unit Price
- Line Total / Order Total
- Order Status

---

## Step 2: Map Faire Columns to Dashboard Format

Your dashboard needs these **exact column names**:

| Dashboard Column | Faire Column (Common Names) | Notes |
|-----------------|---------------------------|-------|
| `customer_id` | Buyer Name, Store Name, Customer Name, Buyer ID | Use store/business name or create unique ID |
| `product_id` | Product SKU, Product ID, Item ID, SKU | Unique product identifier |
| `product_category` | Product Category, Category, Product Type | Your product categories |
| `transaction_date` | Order Date, Purchase Date, Date | Format: YYYY-MM-DD or MM/DD/YYYY |
| `sales_amount` | Line Total, Order Total, Amount, Revenue | Total for that line item |

---

## Step 3: Transform Your Faire Data

### Option A: Use Excel/Google Sheets (Easiest)

1. **Open your Faire export CSV**
2. **Create new columns** with the exact names above
3. **Map the data**:
   - Copy "Buyer Name" → `customer_id`
   - Copy "Product SKU" → `product_id`
   - Copy "Product Category" → `product_category`
   - Copy "Order Date" → `transaction_date`
   - Copy "Line Total" → `sales_amount`
4. **Remove unnecessary columns**
5. **Save as CSV** with name: `faire_sales_data.csv`

### Option B: Use the Python Script (Automated)

I've created a script `transform_faire_data.py` that will automatically:
- Detect Faire column names
- Map them to dashboard format
- Clean and validate the data
- Create the properly formatted CSV

**Run it:**
```bash
python3 transform_faire_data.py your_faire_export.csv
```

---

## Step 4: Export Customer/Business Information (Optional but Recommended)

### Where to Find It:
1. Go to **"Customers"** or **"Buyers"** section in Faire
2. Look for **"Export Customer List"** or **"Download Buyers"**

### What You Need:
- Customer/Buyer Name (must match `customer_id` from sales data)
- Business Type / Store Type (if available)
- Business Category (if available)

### Create Business Mapping File:

Create `faire_business_mapping.csv` with:
```csv
customer_id,business_category
Store Name 1,Retail Boutique
Store Name 2,Gift Shop
Store Name 3,Home Goods Store
```

**If Faire doesn't provide business types**, you can:
- Use the dashboard's **Auto-classify** feature
- Manually classify based on store names
- Leave it blank and let the dashboard classify automatically

---

## Step 5: Common Faire Column Name Variations

The dashboard auto-detects these column name variations:

### Customer ID:
- Buyer Name, Store Name, Customer Name, Buyer, Client, Store

### Product ID:
- Product SKU, SKU, Product ID, Item ID, Product Code

### Product Category:
- Product Category, Category, Product Type, Type

### Transaction Date:
- Order Date, Purchase Date, Date, Sale Date, Transaction Date

### Sales Amount:
- Line Total, Order Total, Amount, Revenue, Total, Price

---

## Step 6: Data Quality Checklist

Before uploading, make sure:

- [ ] **No missing values** in customer_id, product_id, sales_amount
- [ ] **Dates are valid** (check for future dates or typos)
- [ ] **Sales amounts are positive** (remove refunds/cancellations)
- [ ] **Product categories are consistent** (e.g., "Home Decor" not "home decor" and "Home Decor")
- [ ] **Customer IDs match** between sales data and business mapping (if using)

---

## Step 7: Upload to Dashboard

1. **Open the dashboard** (should be running at http://localhost:8501)
2. **In the sidebar**, upload your transformed CSV:
   - Click "Upload Sales Data (CSV)"
   - Select `faire_sales_data.csv`
3. **Upload business mapping** (if you created one):
   - Click "Upload Business Mapping (CSV)"
   - Select `faire_business_mapping.csv`
4. **Or use Auto-classify**:
   - Click "Auto-classify Businesses" button
   - The system will classify stores based on keywords

---

## Troubleshooting

### "Missing required columns" error:
- Check that your CSV has columns that match the required names
- The dashboard auto-detects common variations, but if your column names are very different, rename them manually

### Dates not parsing correctly:
- Try formats: YYYY-MM-DD, MM/DD/YYYY, or DD/MM/YYYY
- Make sure dates are in a single column

### Business categories showing as "Unknown":
- Upload a business mapping file, OR
- Use the Auto-classify feature, OR
- Manually create the mapping file

### Data looks wrong:
- Check that sales_amount is numeric (no currency symbols)
- Remove any header rows or summary rows
- Make sure each row is a single transaction

---

## Example: Before and After

### Faire Export (Before):
```csv
Order Date,Buyer Name,Product SKU,Product Name,Category,Quantity,Unit Price,Line Total
2024-01-15,The Gift Shop,SKU-12345,Candle Set,Home Decor,5,25.00,125.00
2024-01-16,Boutique Store,SKU-67890,Necklace,Jewelry,2,175.00,350.00
```

### Dashboard Format (After):
```csv
customer_id,product_id,product_category,transaction_date,sales_amount
The Gift Shop,SKU-12345,Home Decor,2024-01-15,125.00
Boutique Store,SKU-67890,Jewelry,2024-01-16,350.00
```

---

## Need More Help?

- Check `FAIRE_DATA_GUIDE.md` for more details
- The dashboard's column mapping is flexible - it will try to auto-detect your column names
- If you're stuck, share a sample of your Faire export (first few rows) and I can help map it


# Automated Outreach & Regional Targeting Guide

## Overview

The Automated Outreach feature helps you:
1. **Find target businesses** based on store type, products, and location
2. **Analyze regional preferences** to understand what products sell best in different areas
3. **Generate outreach lists** with personalized recommendations
4. **Export data** for automated email campaigns

## Key Features

### 1. Target Finder

**Purpose**: Find businesses that match your criteria but don't currently buy your product.

**How to Use**:
1. Select **Business Category** (e.g., "Independent Bookstore")
2. Select **Product Category** to promote (e.g., "Fiction Books")
3. Optionally select a **State** to target specific region
4. Set **Maximum Targets** (10-100)
5. Click **"Generate Outreach List"**

**What You Get**:
- List of businesses that:
  - Match the business category
  - Are in the target location
  - DON'T currently buy the product (opportunity!)
  - Shows what products they DO buy
  - Includes similar products they might want
  - Ranked by opportunity score

### 2. Regional Analysis

**Purpose**: Understand product preferences by state/region.

**How to Use**:
1. Go to **"Regional Analysis"** tab
2. Click **"Analyze Regional Preferences"**

**What You Get**:
- Top products by state
- Revenue by state
- Product category heatmap showing regional preferences
- Insights like: "Gift shops in Georgia prefer different products than gift shops in California"

**Use Cases**:
- Identify regional product preferences
- Adjust product mix by region
- Understand market differences across states

### 3. Outreach Export

**Purpose**: Export your target list for automated outreach campaigns.

**Export Formats**:

#### CSV Format
- Standard spreadsheet format
- Includes: customer_id, location, current_products, recommended_product, etc.
- Use for: CRM import, spreadsheet analysis, data processing

#### JSON Format
- Structured data format
- Use for: API integration, automated systems, data pipelines

#### Email Templates
- Pre-written email templates
- Personalized for each target business
- Includes:
  - Business name
  - Location context
  - Product recommendations
  - Similar products they might like
- Use for: Email campaigns, personalized outreach

## Example Workflow

### Scenario: Promoting Fiction Books to Bookstores in California

1. **Target Finder**:
   - Business Category: "Independent Bookstore"
   - Product Category: "Fiction Books"
   - State: "CA"
   - Generate list

2. **Review Results**:
   - See 25 bookstores in CA that don't buy Fiction Books
   - Check what products they currently buy
   - See similar products recommended

3. **Regional Analysis**:
   - Check "Regional Analysis" tab
   - See that Fiction Books are popular in CA
   - Compare with other states

4. **Export**:
   - Go to "Outreach Export" tab
   - Choose "Email Templates"
   - Download personalized emails
   - Import into your email system

## Regional Targeting Strategy

### Why Regional Matters

Different regions have different preferences:
- **Gift shops in Georgia** might prefer different products than **gift shops in California**
- **Bookstores in New York** might have different needs than **bookstores in Texas**
- Regional analysis helps you:
  - Customize product recommendations
  - Adjust messaging by region
  - Understand market differences

### Best Practices

1. **Start Broad, Then Narrow**:
   - First analyze regional preferences
   - Then target specific states
   - Finally focus on cities

2. **Use Similar Products**:
   - If a business buys Product A, recommend similar Product B
   - The system automatically finds similar products

3. **Consider Opportunity Score**:
   - Lower score = more opportunity
   - Businesses buying fewer products = more potential

4. **Personalize Outreach**:
   - Use the email templates
   - Mention their current products
   - Reference similar businesses in their area

## Data Requirements

Your sales data should include:
- `customer_id` - Business identifier
- `business_category` - Type of business
- `product_category` - Product category purchased
- `location` or `city` + `state` - Location information
- `sales_amount` - Transaction value

## Tips for Success

1. **Regular Updates**: Export fresh data monthly
2. **Test Different Criteria**: Try different business/product combinations
3. **Track Results**: Monitor which targets convert
4. **Regional Customization**: Adjust products by region based on analysis
5. **Follow Up**: Use the similar products list for follow-up campaigns

## Next Steps

1. **Generate your first outreach list**
2. **Analyze regional preferences** for your products
3. **Export and customize** email templates
4. **Track results** and refine your targeting

## Questions?

- Check the main README.md for general app usage
- Review FAIRE_DATA_GUIDE.md for data format requirements
- The dashboard includes tooltips and help text


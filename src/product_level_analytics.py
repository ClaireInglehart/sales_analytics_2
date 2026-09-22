"""
Product-level analytics - specific products by area and outreach email pitches
"""

import pandas as pd
from typing import Dict, List, Optional


def _first_non_empty(customer_info: pd.Series, candidates: List[str], default: str = "") -> str:
    for col in candidates:
        if col in customer_info.index and pd.notna(customer_info[col]):
            value = str(customer_info[col]).strip()
            if value and value.lower() != "nan":
                return value
    return default


def _build_full_address(customer_info: pd.Series) -> str:
    address_1 = _first_non_empty(customer_info, ["address_1", "Address 1", "address1"])
    address_2 = _first_non_empty(customer_info, ["address_2", "Address 2", "address2"])
    city = _first_non_empty(customer_info, ["city", "City"])
    state = _first_non_empty(customer_info, ["state", "State"])
    zip_code = _first_non_empty(customer_info, ["zip_code", "Zip Code", "zip"])
    country = _first_non_empty(customer_info, ["country", "Country"])

    street = ", ".join([part for part in [address_1, address_2] if part])
    locality = ", ".join([part for part in [city, state, zip_code] if part])
    return ", ".join([part for part in [street, locality, country] if part])


def is_real_product_name(product_name: str) -> bool:
    name = str(product_name or "").strip()
    if not name or name.lower() == "nan":
        return False
    if name.startswith("Order "):
        return False
    return True


def filter_dataframe_to_area(df: pd.DataFrame, area: str) -> pd.DataFrame:
    if not area:
        return df.copy()

    area_df = df.copy()
    if "county" in area_df.columns and area_df["county"].astype(str).str.strip().replace("nan", "").ne("").any():
        area_df["_area"] = (
            area_df["county"].fillna("").astype(str).str.strip()
            + ", "
            + area_df["state"].fillna("").astype(str).str.strip()
        ).str.strip(", ").str.strip()
        return area_df[area_df["_area"] == area].copy()

    if "city" in area_df.columns:
        area_df["_area"] = (
            area_df["city"].fillna("").astype(str).str.strip()
            + ", "
            + area_df["state"].fillna("").astype(str).str.strip()
        ).str.strip(", ").str.strip()
        return area_df[area_df["_area"] == area].copy()

    if "state" in area_df.columns:
        return area_df[area_df["state"] == area].copy()
    if "location" in area_df.columns:
        return area_df[area_df["location"].str.contains(area, case=False, na=False)].copy()
    return area_df


def _order_count(series_df: pd.DataFrame) -> int:
    if "order_number" in series_df.columns:
        return int(series_df["order_number"].nunique())
    return len(series_df)


def find_products_popular_in_area(
    df: pd.DataFrame,
    area: str,
    top_n: int = 10,
    min_stores: int = 2,
) -> pd.DataFrame:
    """Top specific products in an area (by store adoption, then revenue)."""
    filtered_df = filter_dataframe_to_area(df, area)
    if "product_name" not in filtered_df.columns:
        return pd.DataFrame()

    filtered_df = filtered_df[filtered_df["product_name"].map(is_real_product_name)].copy()
    if len(filtered_df) == 0:
        return pd.DataFrame()

    agg_kwargs = {
        "total_revenue": ("sales_amount", "sum"),
        "line_items": ("sales_amount", "count"),
        "num_stores": ("customer_id", "nunique"),
    }
    if "quantity" in filtered_df.columns:
        agg_kwargs["total_units"] = ("quantity", "sum")

    grouped = filtered_df.groupby(["product_id", "product_name"], as_index=False).agg(**agg_kwargs)
    if "order_number" in filtered_df.columns:
        orders = (
            filtered_df.groupby(["product_id", "product_name"])["order_number"]
            .nunique()
            .reset_index(name="num_orders")
        )
        grouped = grouped.merge(orders, on=["product_id", "product_name"], how="left")
    else:
        grouped["num_orders"] = grouped["line_items"]

    grouped = grouped[grouped["num_stores"] >= min_stores]
    grouped = grouped.sort_values(["num_stores", "total_revenue"], ascending=[False, False])
    return grouped.head(top_n).reset_index(drop=True)


def _sample_buyer_stores(area_df: pd.DataFrame, product_name: str, limit: int = 4) -> List[str]:
    buyers = (
        area_df[area_df["product_name"] == product_name]["customer_id"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
    return buyers[:limit]


def generate_product_pitch_email(
    product_name: str,
    area: str,
    buyer_stores: List[str],
    prospect_store: str,
    contact_name: str = "",
    stats: Optional[Dict] = None,
) -> str:
    stats = stats or {}
    stores_count = stats.get("num_stores", len(buyer_stores))
    units = stats.get("total_units")
    revenue = stats.get("total_revenue")

    greeting = contact_name.strip() if contact_name else f"Team at {prospect_store}"
    if buyer_stores:
        if len(buyer_stores) == 1:
            social_proof = f"**{buyer_stores[0]}** in {area} has been stocking it"
        elif len(buyer_stores) == 2:
            social_proof = f"stores like **{buyer_stores[0]}** and **{buyer_stores[1]}** in {area} have been reordering it"
        else:
            others = len(buyer_stores) - 2
            social_proof = (
                f"stores like **{buyer_stores[0]}**, **{buyer_stores[1]}**, "
                f"and {others} others in {area} have been buying it"
            )
    else:
        social_proof = f"similar stores in {area} have been reordering it"

    detail_bits = []
    if stores_count:
        detail_bits.append(f"{stores_count} local stores have ordered it")
    if units:
        detail_bits.append(f"{int(units):,} units sold in the area")
    if revenue:
        detail_bits.append(f"${float(revenue):,.0f} wholesale in local sales")
    detail_line = " — ".join(detail_bits) if detail_bits else ""

    subject = f"Local stores in {area} are selling {product_name}"
    body = (
        f"Subject: {subject}\n\n"
        f"Hi {greeting},\n\n"
        f"I wanted to reach out because {social_proof}.\n\n"
        f"The product is **{product_name}**."
    )
    if detail_line:
        body += f" ({detail_line}.)"
    body += (
        "\n\n"
        "If you're looking for a proven add-on for your shop, we can share wholesale pricing, "
        "photos, and a suggested starter quantity based on what nearby stores are moving.\n\n"
        "Would you like a sample pack or a quick call to pick the best sellers for your shelf?\n\n"
        "Best,\n"
        "Sales Team"
    )
    return body


def build_area_product_pitch_pack(
    df: pd.DataFrame,
    area: str,
    top_n: int = 10,
    min_stores: int = 2,
) -> pd.DataFrame:
    """Products doing well locally, with buyer examples and a reusable email script."""
    area_df = filter_dataframe_to_area(df, area)
    popular = find_products_popular_in_area(df, area, top_n=top_n, min_stores=min_stores)
    if len(popular) == 0:
        return pd.DataFrame()

    rows = []
    for _, row in popular.iterrows():
        product_name = row["product_name"]
        buyers = _sample_buyer_stores(area_df, product_name, limit=4)
        stats = {
            "num_stores": int(row["num_stores"]),
            "total_units": int(row["total_units"]) if "total_units" in row else None,
            "total_revenue": float(row["total_revenue"]),
        }
        rows.append(
            {
                "Product": product_name,
                "Stores in Area": int(row["num_stores"]),
                "Orders in Area": int(row.get("num_orders", row["line_items"])),
                "Units Sold": int(row["total_units"]) if "total_units" in row else "",
                "Revenue": float(row["total_revenue"]),
                "Example Stores That Bought It": ", ".join(buyers),
                "Email Subject": f"Local stores in {area} are selling {product_name}",
                "Email Script (copy for prospects)": generate_product_pitch_email(
                    product_name=product_name,
                    area=area,
                    buyer_stores=buyers,
                    prospect_store="[Store Name]",
                    contact_name="[Contact Name]",
                    stats=stats,
                ),
            }
        )
    return pd.DataFrame(rows)


def build_prospect_product_emails(
    df: pd.DataFrame,
    area: str,
    product_name: str,
    prospect_lines: List[str],
    contacts_lookup: Optional[Dict] = None,
) -> pd.DataFrame:
    """Personalized product pitch emails for pasted prospect stores."""
    contacts_lookup = contacts_lookup or {}
    area_df = filter_dataframe_to_area(df, area)
    product_rows = area_df[area_df["product_name"] == product_name]
    if len(product_rows) == 0:
        return pd.DataFrame()

    buyers = _sample_buyer_stores(area_df, product_name, limit=4)
    stats = {
        "num_stores": int(product_rows["customer_id"].nunique()),
        "total_units": int(product_rows["quantity"].sum()) if "quantity" in product_rows.columns else None,
        "total_revenue": float(product_rows["sales_amount"].sum()),
    }

    existing = set(df["customer_id"].dropna().astype(str).str.strip().str.lower())
    rows = []
    for line in prospect_lines:
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        store = parts[0]
        city = parts[1] if len(parts) > 1 else area
        if store.lower() in existing:
            continue

        key = "".join(ch.lower() for ch in store if ch.isalnum())
        match = contacts_lookup.get(key, {})
        contact_name = match.get("contact_name") or f"Team at {store}"
        email = match.get("email") or ""
        location = f"{city}, {area}" if city else area

        rows.append(
            {
                "Prospect Store": store,
                "Contact Name": contact_name,
                "Email": email,
                "Location": location,
                "Product to Pitch": product_name,
                "Local Proof Stores": ", ".join(buyers),
                "Email Subject": f"Local stores in {area} are selling {product_name}",
                "Email Draft": generate_product_pitch_email(
                    product_name=product_name,
                    area=area,
                    buyer_stores=buyers,
                    prospect_store=store,
                    contact_name=contact_name,
                    stats=stats,
                ),
            }
        )
    return pd.DataFrame(rows)


# --- legacy helpers kept for compatibility ---

def analyze_product_popularity_by_area(
    df: pd.DataFrame,
    product_name: str = None,
    product_id: str = None,
    area: str = None,
) -> Dict:
    filtered_df = df.copy()
    if product_name:
        filtered_df = filtered_df[filtered_df["product_name"] == product_name]
    elif product_id:
        filtered_df = filtered_df[filtered_df["product_id"] == product_id]
    if area:
        filtered_df = filter_dataframe_to_area(filtered_df, area)
    if len(filtered_df) == 0:
        return {"error": "No data found for the specified criteria"}

    if "location" not in filtered_df.columns and "city" in filtered_df.columns and "state" in filtered_df.columns:
        filtered_df["location"] = filtered_df["city"] + ", " + filtered_df["state"]

    location_analysis = filtered_df.groupby("location").agg(
        total_revenue=("sales_amount", "sum"),
        num_orders=("sales_amount", "count"),
        avg_order=("sales_amount", "mean"),
        num_stores=("customer_id", "nunique"),
    ).reset_index().sort_values("total_revenue", ascending=False)

    return {
        "product_name": product_name or product_id,
        "total_sales": filtered_df["sales_amount"].sum(),
        "total_orders": _order_count(filtered_df),
        "unique_stores": filtered_df["customer_id"].nunique(),
        "top_areas": location_analysis.head(10).to_dict("records"),
        "all_areas": location_analysis.to_dict("records"),
    }


def find_stores_for_specific_product(
    df: pd.DataFrame,
    product_name: str = None,
    product_id: str = None,
    area: str = None,
    business_category: str = None,
) -> pd.DataFrame:
    if product_name:
        product_buyers = df[df["product_name"] == product_name]
    elif product_id:
        product_buyers = df[df["product_id"] == product_id]
    else:
        return pd.DataFrame()

    if len(product_buyers) == 0:
        return pd.DataFrame()

    if "location" not in product_buyers.columns and "city" in product_buyers.columns:
        product_buyers = product_buyers.copy()
        product_buyers["location"] = product_buyers["city"] + ", " + product_buyers["state"]
    popular_areas = (
        product_buyers.groupby("location")["customer_id"].nunique().nlargest(5).index.tolist()
        if "location" in product_buyers.columns
        else []
    )
    buyer_types = product_buyers["business_category"].value_counts().head(3).index.tolist() if "business_category" in product_buyers.columns else []

    search_df = filter_dataframe_to_area(df, area) if area else df.copy()
    if business_category:
        search_df = search_df[search_df["business_category"] == business_category]
    elif buyer_types and "business_category" in search_df.columns:
        search_df = search_df[search_df["business_category"].isin(buyer_types)]

    targets = []
    for customer_id in search_df["customer_id"].unique():
        customer_data = search_df[search_df["customer_id"] == customer_id]
        buys_product = (
            (customer_data["product_name"] == product_name).any()
            if product_name
            else (customer_data["product_id"] == product_id).any()
        )
        if buys_product:
            continue
        customer_info = customer_data.iloc[0]
        loc = customer_info.get("location") or f"{customer_info.get('city', '')}, {customer_info.get('state', '')}"
        products_bought = customer_data["product_name"].dropna().astype(str).unique().tolist()[:5]
        targets.append(
            {
                "customer_id": customer_id,
                "business_category": customer_info.get("business_category", "Unknown"),
                "location": loc,
                "full_address": _build_full_address(customer_info),
                "product_to_sell": product_name or product_id,
                "products_they_buy": ", ".join(products_bought),
                "total_revenue": customer_data["sales_amount"].sum(),
                "area_is_popular": loc in popular_areas,
                "opportunity_score": len(products_bought),
            }
        )

    if not targets:
        return pd.DataFrame()
    targets_df = pd.DataFrame(targets)
    return targets_df.sort_values(["area_is_popular", "opportunity_score"], ascending=[False, True])


def get_area_product_recommendations(
    df: pd.DataFrame,
    area: str,
    n_products: int = 5,
    n_stores_per_product: int = 10,
) -> Dict:
    popular_products = find_products_popular_in_area(df, area, top_n=n_products)
    if len(popular_products) == 0:
        return {"area": area, "products": [], "recommendations": []}

    recommendations = []
    for _, product_row in popular_products.iterrows():
        product_name = product_row["product_name"]
        stores = find_stores_for_specific_product(df, product_name=product_name, area=area)
        if len(stores) > 0:
            recommendations.append(
                {
                    "product_name": product_name,
                    "product_id": product_row["product_id"],
                    "popularity_in_area": {
                        "total_revenue": product_row["total_revenue"],
                        "num_stores_buying": product_row["num_stores"],
                        "num_orders": product_row.get("num_orders", product_row["line_items"]),
                    },
                    "recommended_stores": stores.head(n_stores_per_product).to_dict("records"),
                }
            )
    return {
        "area": area,
        "popular_products": popular_products.to_dict("records"),
        "recommendations": recommendations,
    }

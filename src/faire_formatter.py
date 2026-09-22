"""Transform raw Faire order-summary exports into dashboard-ready sales data."""

from __future__ import annotations

import pandas as pd


def infer_product_category(product_name: str) -> str:
    name = str(product_name).lower()
    if any(k in name for k in ["sticker", "button", "pin", "magnet"]):
        return "Stickers, pins, & magnets"
    if any(k in name for k in ["pen", "notepad", "notebook", "journal", "book"]):
        return "Stationery & writing"
    if any(k in name for k in ["party", "balloon", "banner", "confetti"]):
        return "Party supplies"
    if any(k in name for k in ["earring", "necklace", "bracelet", "hair", "scrunchie", "women"]):
        return "Women's accessories"
    if any(k in name for k in ["wallet", "tie", "beard", "men"]):
        return "Men's accessories"
    return "Stickers, pins, & magnets"


def _column_lookup(df: pd.DataFrame) -> dict[str, str]:
    return {str(col).strip().lower(): col for col in df.columns}


def _pick(columns: dict[str, str], *names: str) -> str | None:
    for name in names:
        key = name.lower()
        if key in columns:
            return columns[key]
    return None


def _series(df: pd.DataFrame, columns: dict[str, str], *names: str, default="") -> pd.Series:
    col = _pick(columns, *names)
    if col is None:
        return pd.Series([default] * len(df), index=df.index)
    return df[col]


def _to_number_series(series: pd.Series) -> pd.Series:
    cleaned = (
        series.fillna("")
        .astype(str)
        .str.replace(r"[\$,]", "", regex=True)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")


def _summarize_order_category(series: pd.Series) -> str:
    unique_categories = [value for value in series.dropna().astype(str).str.strip().unique() if value]
    if not unique_categories:
        return "Order"
    if len(unique_categories) == 1:
        return unique_categories[0]
    return "Mixed order"


def is_faire_raw_export(df: pd.DataFrame) -> bool:
    """True when the file looks like a raw Faire orders summary export."""
    columns = _column_lookup(df)
    has_order_number = _pick(columns, "Order Number", "order number") is not None
    has_retailer = _pick(columns, "Retailer Name", "retailer name", "Store Name", "store name") is not None
    has_order_date = _pick(columns, "Order Date", "order date") is not None
    has_product = _pick(columns, "Product Name", "product name") is not None
    return has_order_number and has_retailer and has_order_date and has_product


def format_faire_export(df: pd.DataFrame, aggregate_orders: bool = False) -> pd.DataFrame:
    """Convert raw Faire line-item export into dashboard-ready rows.

    By default keeps one row per product line so specific product names are preserved.
    Set aggregate_orders=True to collapse to one row per order number.
    """
    raw = df.copy()
    columns = _column_lookup(raw)

    retailer_col = _pick(columns, "Retailer Name", "retailer name", "Store Name", "store name")
    order_date_col = _pick(columns, "Order Date", "order date")
    order_number_col = _pick(columns, "Order Number", "order number")
    product_name_col = _pick(columns, "Product Name", "product name")
    sku_col = _pick(columns, "SKU", "sku")
    quantity_col = _pick(columns, "Quantity", "quantity")
    wholesale_col = _pick(columns, "Wholesale Price", "wholesale price")
    retail_col = _pick(columns, "Retail Price", "retail price")
    city_col = _pick(columns, "City", "city")
    state_col = _pick(columns, "State", "state")
    status_col = _pick(columns, "Status", "status")

    if not all([retailer_col, order_date_col, order_number_col, product_name_col, quantity_col, wholesale_col]):
        raise ValueError(
            "This looks like a Faire export but is missing expected columns. "
            f"Found: {', '.join(raw.columns.astype(str))}"
        )

    out = pd.DataFrame()
    out["customer_id"] = raw[retailer_col].astype(str).str.strip()

    sku = _series(raw, columns, "SKU", "sku").fillna("").astype(str).str.strip()
    product_name = raw[product_name_col].fillna("").astype(str).str.strip()
    out["product_id"] = sku.mask(sku.eq(""), product_name)
    out["product_name"] = product_name
    out["product_category"] = out["product_name"].apply(infer_product_category)
    out["transaction_date"] = pd.to_datetime(raw[order_date_col], errors="coerce").dt.strftime("%Y-%m-%d")

    qty = _to_number_series(raw[quantity_col]).fillna(0)
    wholesale_price = _to_number_series(raw[wholesale_col]).fillna(0)
    out["sales_amount"] = (qty * wholesale_price).round(2)

    out["city"] = _series(raw, columns, "City", "city").fillna("").astype(str).str.strip().str.title()
    out["state"] = _series(raw, columns, "State", "state").fillna("").astype(str).str.strip().str.upper()
    out["location"] = (out["city"] + ", " + out["state"]).str.strip(", ")
    out["address_1"] = _series(raw, columns, "Address 1", "address 1").fillna("").astype(str).str.strip()
    out["address_2"] = _series(raw, columns, "Address 2", "address 2").fillna("").astype(str).str.strip()
    out["zip_code"] = _series(raw, columns, "Zip Code", "zip code", "zip").fillna("").astype(str).str.strip()
    out["country"] = _series(raw, columns, "Country", "country").fillna("").astype(str).str.strip()
    out["full_address"] = (
        out["address_1"]
        + out["address_2"].map(lambda x: f", {x}" if x else "")
        + out["city"].map(lambda x: f", {x}" if x else "")
        + out["state"].map(lambda x: f", {x}" if x else "")
        + out["zip_code"].map(lambda x: f" {x}" if x else "")
        + out["country"].map(lambda x: f", {x}" if x else "")
    ).str.strip(", ").str.strip()

    out["order_number"] = raw[order_number_col].fillna("").astype(str).str.strip()
    out["status"] = raw[status_col] if status_col else pd.Series([""] * len(raw), index=raw.index)
    out["quantity"] = qty
    out["wholesale_price"] = wholesale_price
    if retail_col:
        out["retail_price"] = _to_number_series(raw[retail_col]).fillna(0)
    else:
        out["retail_price"] = 0.0
    out["retail_sales_amount"] = (out["quantity"] * out["retail_price"]).round(2)

    out = out[
        out["customer_id"].ne("")
        & out["order_number"].ne("")
        & out["product_name"].ne("")
        & out["transaction_date"].notna()
        & (out["sales_amount"] > 0)
    ].copy()

    out["sales_amount"] = out["sales_amount"].round(2)
    out["wholesale_price"] = out["wholesale_price"].round(2)
    out["retail_price"] = out["retail_price"].round(2)

    if not aggregate_orders:
        return out

    out = (
        out.groupby("order_number", as_index=False)
        .agg(
            customer_id=("customer_id", "first"),
            product_category=("product_category", _summarize_order_category),
            transaction_date=("transaction_date", "first"),
            sales_amount=("sales_amount", "sum"),
            city=("city", "first"),
            state=("state", "first"),
            location=("location", "first"),
            address_1=("address_1", "first"),
            address_2=("address_2", "first"),
            zip_code=("zip_code", "first"),
            country=("country", "first"),
            full_address=("full_address", "first"),
            status=("status", "first"),
            quantity=("quantity", "sum"),
            wholesale_price=("wholesale_price", "mean"),
            retail_price=("retail_sales_amount", "sum"),
        )
        .rename(columns={"order_number": "product_id"})
    )
    out["product_name"] = "Order " + out["product_id"]
    out["order_number"] = out["product_id"]
    out["order_count"] = 1
    out["sales_amount"] = out["sales_amount"].round(2)
    out["wholesale_price"] = out["wholesale_price"].round(2)
    out["retail_price"] = out["retail_price"].round(2)

    return out

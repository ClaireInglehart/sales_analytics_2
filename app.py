"""
Sales Analytics Dashboard
Main Streamlit application for analyzing business-product category relationships
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import math
import urllib.parse
import urllib.request
import json

from src.data_processor import process_sales_data, merge_business_categories
from src.business_classifier import (
    create_business_mapping,
    load_business_mapping,
    get_unique_customers,
)
from src import analytics
from src import location_analytics
from src import outreach_automation
from src import brand_product_matcher
from src import product_level_analytics
import config

st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "sales_data" not in st.session_state:
    st.session_state.sales_data = None
if "business_mapping" not in st.session_state:
    st.session_state.business_mapping = None
if "processed_data" not in st.session_state:
    st.session_state.processed_data = None


def load_sample_data():
    try:
        df = process_sales_data("data/sample_sales.csv")
        mapping = load_business_mapping("data/business_mapping.csv")
        df = merge_business_categories(df, mapping)
        return df, mapping
    except Exception as e:
        st.error(f"Error loading sample data: {str(e)}")
        return None, None


def humanize_column_name(name: str) -> str:
    if not isinstance(name, str):
        return str(name)
    return name.replace("_", " ").strip().title()


def render_table(data, currency_columns=None, rename_map=None, hide_index=True):
    currency_columns = currency_columns or []
    rename_map = rename_map or {}
    display_df = data.copy()
    final_rename = {
        col: rename_map.get(col, humanize_column_name(col))
        for col in display_df.columns
    }
    display_df = display_df.rename(columns=final_rename)
    currency_display_columns = [
        final_rename[col] for col in currency_columns if col in final_rename
    ]
    column_config = {
        col_name: st.column_config.NumberColumn(col_name, format="$%.2f")
        for col_name in currency_display_columns
    }
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=hide_index,
        column_config=column_config if column_config else None,
    )


def _get_states(df):
    if "state" in df.columns:
        return sorted([s for s in df["state"].unique() if s and str(s) != "nan"])
    if "location" in df.columns:
        return sorted(list(set(
            loc.split(",")[-1].strip()
            for loc in df["location"].unique()
            if loc and "," in str(loc)
        )))
    return []


def _has_county_data(df: pd.DataFrame) -> bool:
    return (
        "county" in df.columns
        and df["county"].astype(str).str.strip().replace("nan", "").ne("").any()
    )


def _format_area_label(county: str, state: str) -> str:
    county_clean = str(county or "").strip()
    state_clean = str(state or "").strip()
    if county_clean and state_clean:
        return f"{county_clean}, {state_clean}"
    return county_clean or state_clean


def _get_area_options(df: pd.DataFrame):
    if _has_county_data(df):
        options = (
            df.assign(
                _area=df.apply(
                    lambda row: _format_area_label(row.get("county", ""), row.get("state", "")),
                    axis=1,
                )
            )["_area"]
            .dropna()
            .astype(str)
            .str.strip()
        )
        return sorted([area for area in options.unique().tolist() if area and area != "nan"]), "County"
    if "city" in df.columns:
        options = (
            df.assign(
                _area=df.apply(
                    lambda row: _format_area_label(row.get("city", ""), row.get("state", "")),
                    axis=1,
                )
            )["_area"]
            .dropna()
            .astype(str)
            .str.strip()
        )
        return sorted([area for area in options.unique().tolist() if area and area != "nan"]), "County / City"
    return _get_states(df), "State / Area"


def _filter_df_to_area(df: pd.DataFrame, area_pick: str) -> pd.DataFrame:
    if not area_pick:
        return df.copy()
    area_df = df.copy()
    if _has_county_data(area_df):
        area_df["_area"] = area_df.apply(
            lambda row: _format_area_label(row.get("county", ""), row.get("state", "")),
            axis=1,
        )
        return area_df[area_df["_area"] == area_pick].copy()
    if "city" in area_df.columns:
        area_df["_area"] = area_df.apply(
            lambda row: _format_area_label(row.get("city", ""), row.get("state", "")),
            axis=1,
        )
        return area_df[area_df["_area"] == area_pick].copy()
    if "state" in area_df.columns:
        return area_df[area_df["state"] == area_pick].copy()
    if "location" in area_df.columns:
        return area_df[area_df["location"].str.contains(area_pick, case=False, na=False)].copy()
    return area_df


def _build_smart_recommendations(filtered_df):
    """Auto-compute the best business-type / product-category market signals."""
    biz_product_rev = (
        filtered_df.groupby(["business_category", "product_category"])["sales_amount"]
        .sum()
        .unstack(fill_value=0)
    )
    biz_customer_counts = (
        filtered_df.groupby(["business_category", "product_category"])["customer_id"]
        .nunique()
        .unstack(fill_value=0)
    )
    total_customers_per_biz = (
        filtered_df.groupby("business_category")["customer_id"].nunique()
    )

    recs = []
    for biz in filtered_df["business_category"].unique():
        total_custs = total_customers_per_biz.get(biz, 0)
        if total_custs == 0:
            continue
        for prod in filtered_df["product_category"].unique():
            buyers = biz_customer_counts.loc[biz, prod] if prod in biz_customer_counts.columns and biz in biz_customer_counts.index else 0
            current_rev = biz_product_rev.loc[biz, prod] if prod in biz_product_rev.columns and biz in biz_product_rev.index else 0

            if buyers <= 0:
                continue

            avg_rev = current_rev / buyers
            adoption_pct = buyers / total_custs * 100

            recs.append({
                "Business Type": biz,
                "Product": prod,
                "Stores Buying": int(buyers),
                "Total Stores of Type": int(total_custs),
                "Adoption Rate": f"{adoption_pct:.0f}%",
                "Revenue": float(current_rev),
                "Avg Revenue / Store": float(avg_rev),
            })

    if not recs:
        return pd.DataFrame()

    recs_df = pd.DataFrame(recs)
    return recs_df.sort_values("Avg Revenue / Store", ascending=False).head(20).reset_index(drop=True)


def _build_buyer_profile(df, product_category=None, product_name=None):
    """Build a buyer profile: who buys this product and where."""
    filt = df.copy()
    label = product_category or product_name
    if product_name and "product_name" in filt.columns:
        filt = filt[filt["product_name"] == product_name]
    elif product_category:
        filt = filt[filt["product_category"] == product_category]

    if len(filt) == 0:
        return None

    total_rev = filt["sales_amount"].sum()
    if "order_number" in filt.columns:
        total_orders = int(filt["order_number"].nunique())
    else:
        total_orders = len(filt)
    unique_stores = filt["customer_id"].nunique()
    avg_order = filt["sales_amount"].mean()

    biz_breakdown = (
        filt.groupby("business_category")
        .agg(stores=("customer_id", "nunique"), revenue=("sales_amount", "sum"), orders=("sales_amount", "count"))
        .sort_values("revenue", ascending=False)
        .reset_index()
    )
    biz_breakdown["avg_order"] = biz_breakdown["revenue"] / biz_breakdown["orders"]
    biz_breakdown["pct_of_revenue"] = (biz_breakdown["revenue"] / total_rev * 100).round(1)

    area_breakdown = pd.DataFrame()
    if _has_county_data(filt):
        county_labels = (
            filt["county"].fillna("").astype(str).str.strip()
            + ", "
            + filt["state"].fillna("").astype(str).str.strip()
        ).str.strip(", ").str.strip()
        county_filt = filt.assign(_area=county_labels)
        area_breakdown = (
            county_filt[county_filt["_area"].ne("")]
            .groupby("_area")
            .agg(stores=("customer_id", "nunique"), revenue=("sales_amount", "sum"), orders=("sales_amount", "count"))
            .sort_values("revenue", ascending=False)
            .reset_index()
            .rename(columns={"_area": "area"})
        )
    elif "city" in filt.columns:
        city_labels = (
            filt["city"].fillna("").astype(str).str.strip()
            + ", "
            + filt["state"].fillna("").astype(str).str.strip()
        ).str.strip(", ").str.strip()
        city_filt = filt.assign(_area=city_labels)
        area_breakdown = (
            city_filt[city_filt["_area"].ne("")]
            .groupby("_area")
            .agg(stores=("customer_id", "nunique"), revenue=("sales_amount", "sum"), orders=("sales_amount", "count"))
            .sort_values("revenue", ascending=False)
            .reset_index()
            .rename(columns={"_area": "area"})
        )
    elif "state" in filt.columns:
        area_breakdown = (
            filt.groupby("state")
            .agg(stores=("customer_id", "nunique"), revenue=("sales_amount", "sum"), orders=("sales_amount", "count"))
            .sort_values("revenue", ascending=False)
            .reset_index()
            .rename(columns={"state": "area"})
        )
    elif "location" in filt.columns:
        area_breakdown = (
            filt.groupby("location")
            .agg(stores=("customer_id", "nunique"), revenue=("sales_amount", "sum"), orders=("sales_amount", "count"))
            .sort_values("revenue", ascending=False)
            .reset_index()
            .rename(columns={"location": "area"})
        )
    if len(area_breakdown) > 0:
        area_breakdown["avg_order"] = area_breakdown["revenue"] / area_breakdown["orders"]

    top_biz = biz_breakdown.head(3)["business_category"].tolist()
    top_areas = area_breakdown.head(3)["area"].tolist() if len(area_breakdown) > 0 else []

    summary_parts = [f"**{label}** sells best to **{', '.join(top_biz)}**"]
    if top_areas:
        summary_parts.append(f"in **{', '.join(top_areas)}**")
    summary_parts.append(f"with an average order of **${avg_order:,.2f}**.")
    summary = " ".join(summary_parts)

    return {
        "summary": summary,
        "total_revenue": total_rev,
        "total_orders": total_orders,
        "unique_stores": unique_stores,
        "avg_order": avg_order,
        "biz_breakdown": biz_breakdown,
        "area_breakdown": area_breakdown,
    }


def _build_maps_search_url(query: str) -> str:
    return f"https://www.google.com/maps/search/{urllib.parse.quote_plus(query)}"


def _with_focus_map_terms(query: str, enabled: bool) -> str:
    if not enabled:
        return query
    return f"{query} LGBTQ friendly inclusive progressive woman owned women owned"


@st.cache_data(show_spinner=False, ttl=86400)
def _geocode_place(place_query: str):
    query = str(place_query or "").strip()
    if not query:
        return None
    url = (
        "https://nominatim.openstreetmap.org/search?"
        f"q={urllib.parse.quote_plus(query)}&format=jsonv2&limit=1"
    )
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "sales-analytics-dashboard/1.0 (streamlit local app)",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        if not payload:
            return None
        first = payload[0]
        return (float(first["lat"]), float(first["lon"]))
    except Exception:
        return None


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_miles = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return 2 * radius_miles * math.asin(math.sqrt(a))


def _extract_state_code(area: str) -> str:
    parts = [p.strip() for p in str(area or "").split(",") if p and str(p) != "nan"]
    if not parts:
        return ""
    candidate = parts[-1]
    if len(candidate) == 2 and candidate.isalpha():
        return candidate.upper()
    return ""


def _build_client_geo_points(df: pd.DataFrame):
    if "customer_id" not in df.columns:
        return []
    if "city" not in df.columns:
        return []

    state_series = df["state"] if "state" in df.columns else pd.Series([""] * len(df), index=df.index)
    working = df.assign(
        _city=df["city"].fillna("").astype(str).str.strip(),
        _state=state_series.fillna("").astype(str).str.strip().str.upper(),
    )
    working = working[working["_city"].ne("")].copy()
    if len(working) == 0:
        return []

    grouped = (
        working.groupby("customer_id")
        .agg(
            city=("_city", "first"),
            state=("_state", "first"),
            orders=("customer_id", "count"),
        )
        .reset_index()
    )

    points = []
    for _, row in grouped.iterrows():
        place = f"{row['city']}, {row['state']}".strip(", ").strip()
        coords = _geocode_place(place)
        if not coords:
            continue
        points.append(
            {
                "customer_id": str(row["customer_id"]).strip(),
                "city_state": place,
                "orders": int(row["orders"]),
                "lat": coords[0],
                "lon": coords[1],
                "state": str(row["state"]).strip().upper(),
            }
        )
    return points


def _apply_distance_filter(scored_df: pd.DataFrame, base_df: pd.DataFrame, area: str, max_miles: float):
    if scored_df is None or len(scored_df) == 0:
        return scored_df, "No candidate stores to distance-filter."

    client_points = _build_client_geo_points(base_df)
    if not client_points:
        return scored_df.iloc[0:0].copy(), "Could not geocode current clients for distance filtering."

    state_hint = _extract_state_code(area)
    filtered_clients = [p for p in client_points if not state_hint or p["state"] == state_hint]
    if filtered_clients:
        client_points = filtered_clients

    rows = []
    for _, row in scored_df.iterrows():
        city = str(row.get("City", "")).strip()
        place = f"{city}, {state_hint}".strip(", ").strip() if city else str(area).strip()
        coords = _geocode_place(place)
        if not coords:
            continue

        nearest_name = ""
        nearest_distance = None
        for cp in client_points:
            dist = _haversine_miles(coords[0], coords[1], cp["lat"], cp["lon"])
            if nearest_distance is None or dist < nearest_distance:
                nearest_distance = dist
                nearest_name = cp["customer_id"]

        if nearest_distance is None or nearest_distance > max_miles:
            continue

        enriched = row.to_dict()
        enriched["Nearest Client"] = nearest_name
        enriched["Nearest Client Distance (mi)"] = round(float(nearest_distance), 2)
        rows.append(enriched)

    if not rows:
        return scored_df.iloc[0:0].copy(), f"No candidates found within {max_miles} miles of existing clients."
    return pd.DataFrame(rows), f"Kept {len(rows)} candidates within {max_miles} miles of current clients."


def _get_prospect_segments(product_category: str):
    prod = (product_category or "").lower()
    if "men" in prod and "accessories" in prod:
        return [
            {
                "segment": "Bookstores With Gift Sections",
                "fit_score": 92,
                "why": "Your current buyers often look like indie bookstores and gift-forward shops.",
                "keywords": ["book", "books", "bookstore", "shop", "gift"],
            },
            {
                "segment": "Gift + Lifestyle Boutiques",
                "fit_score": 88,
                "why": "Accessory impulse buys are strong where novelty gifts and lifestyle goods are sold.",
                "keywords": ["gift", "boutique", "market", "lifestyle", "home"],
            },
            {
                "segment": "Menswear Boutiques",
                "fit_score": 84,
                "why": "Menswear stores are a natural fit for repeat accessory purchases.",
                "keywords": ["men", "mens", "apparel", "clothing", "wear"],
            },
            {
                "segment": "Museum / Attraction Gift Shops",
                "fit_score": 76,
                "why": "Tourist and destination gift stores can convert smaller accessories well.",
                "keywords": ["museum", "gallery", "visitor", "souvenir", "gift"],
            },
            {
                "segment": "Outdoor + Travel Retail",
                "fit_score": 70,
                "why": "Travel shoppers frequently add small utility and style accessories.",
                "keywords": ["outdoor", "travel", "adventure", "gear", "camp"],
            },
        ]

    return [
        {
            "segment": "Gift Shops",
            "fit_score": 82,
            "why": "Gift retail tends to support broad accessory and novelty categories.",
            "keywords": ["gift", "shop", "boutique", "market"],
        },
        {
            "segment": "Lifestyle Boutiques",
            "fit_score": 78,
            "why": "Lifestyle stores often carry curated add-on products.",
            "keywords": ["lifestyle", "boutique", "curated", "home"],
        },
        {
            "segment": "Specialty Retail",
            "fit_score": 72,
            "why": "Niche stores can be strong if product positioning matches their audience.",
            "keywords": ["specialty", "local", "indie", "retail"],
        },
    ]


def _build_existing_clients_index(df: pd.DataFrame):
    index = {}
    if "customer_id" not in df.columns:
        return index
    for raw_name in df["customer_id"].dropna().astype(str).unique().tolist():
        clean = raw_name.strip()
        key = _normalize_lookup(clean)
        if key and key not in index:
            index[key] = clean
    return index


def _extract_focus_keywords(raw_keywords: str):
    return [kw.strip().lower() for kw in str(raw_keywords or "").split(",") if kw.strip()]


def _has_focus_keyword_match(text: str, keywords) -> tuple[bool, list]:
    blob = str(text or "").lower()
    hits = [kw for kw in keywords if kw in blob]
    return (len(hits) > 0), hits


def _find_existing_client_match(store_name: str, existing_clients_index):
    key = _normalize_lookup(store_name)
    if not key:
        return ""
    if key in existing_clients_index:
        return existing_clients_index[key]

    for existing_key, existing_name in existing_clients_index.items():
        if key in existing_key or existing_key in key:
            return existing_name
    return ""


def _score_candidate_prospects(
    raw_input: str,
    area: str,
    segments,
    existing_clients_index=None,
    focus_keywords=None,
    require_focus_match: bool = False,
    maps_focus_mode: bool = False,
):
    lines = [line.strip() for line in (raw_input or "").splitlines() if line.strip()]
    if not lines:
        return pd.DataFrame()
    existing_clients_index = existing_clients_index or {}
    focus_keywords = focus_keywords or []

    scored_rows = []
    for line in lines:
        parts = [part.strip() for part in line.split(",")]
        store_name = parts[0] if len(parts) > 0 else ""
        city = parts[1] if len(parts) > 1 and parts[1] else area
        stated_type = parts[2] if len(parts) > 2 else ""
        text_blob = f"{store_name} {stated_type}".lower()

        best_segment = "General Retail"
        best_score = 45
        best_reason = "No direct keyword hit; moderate fit based on broad retail profile."

        for seg in segments:
            kw_hits = [kw for kw in seg["keywords"] if kw in text_blob]
            candidate_score = int(seg["fit_score"] + len(kw_hits) * 7)
            candidate_score = max(20, min(99, candidate_score))
            if candidate_score > best_score:
                best_score = candidate_score
                best_segment = seg["segment"]
                if kw_hits:
                    best_reason = (
                        f"Matched keywords ({', '.join(kw_hits[:3])}) aligned to {seg['segment']}."
                    )
                else:
                    best_reason = seg["why"]

        focus_match, focus_hits = _has_focus_keyword_match(text_blob, focus_keywords)
        if focus_match:
            best_score = min(99, best_score + 12)
            best_reason = (
                f"{best_reason} LGBTQ/liberal focus signal found ({', '.join(focus_hits[:3])})."
            )

        maps_query = _with_focus_map_terms(
            f"{store_name} {city}, {area}",
            enabled=(maps_focus_mode or require_focus_match),
        )
        existing_match = _find_existing_client_match(store_name, existing_clients_index)
        scored_rows.append(
            {
                "Store": store_name,
                "City": city,
                "Input Type": stated_type if stated_type else "Not provided",
                "Predicted Segment": best_segment,
                "Fit Score": best_score,
                "Already Client": bool(existing_match),
                "Client Match": existing_match if existing_match else "",
                "LGBTQ / Liberal Signal": focus_match,
                "Reason": best_reason,
                "Google Maps": _build_maps_search_url(maps_query),
            }
        )

    scored_df = pd.DataFrame(scored_rows)
    if require_focus_match and "LGBTQ / Liberal Signal" in scored_df.columns:
        scored_df = scored_df[scored_df["LGBTQ / Liberal Signal"]].copy()
    return scored_df.sort_values("Fit Score", ascending=False).reset_index(drop=True)


def _normalize_lookup(value: str) -> str:
    if value is None:
        return ""
    return "".join(ch.lower() for ch in str(value).strip() if ch.isalnum())


def _prepare_contacts_lookup(contacts_df: pd.DataFrame):
    if contacts_df is None or len(contacts_df) == 0:
        return {}

    column_map = {col.lower().strip(): col for col in contacts_df.columns}
    business_col = None
    for candidate in ["business", "business_name", "store", "store_name", "customer_id"]:
        if candidate in column_map:
            business_col = column_map[candidate]
            break
    if not business_col:
        return {}

    name_col = None
    for candidate in ["contact_name", "name", "owner_name", "first_name"]:
        if candidate in column_map:
            name_col = column_map[candidate]
            break

    email_col = None
    for candidate in ["email", "contact_email", "owner_email"]:
        if candidate in column_map:
            email_col = column_map[candidate]
            break

    phone_col = None
    for candidate in ["phone", "contact_phone", "owner_phone"]:
        if candidate in column_map:
            phone_col = column_map[candidate]
            break

    lookup = {}
    for _, row in contacts_df.iterrows():
        key = _normalize_lookup(row.get(business_col, ""))
        if not key:
            continue
        lookup[key] = {
            "contact_name": str(row.get(name_col, "")).strip() if name_col else "",
            "email": str(row.get(email_col, "")).strip() if email_col else "",
            "phone": str(row.get(phone_col, "")).strip() if phone_col else "",
        }
    return lookup


def _build_outreach_contacts(targets_df, product_category, area, contacts_lookup=None):
    contacts_lookup = contacts_lookup or {}
    rows = []
    for _, row in targets_df.iterrows():
        business_name = str(row.get("customer_id", "")).strip()
        location = str(row.get("location", "")).strip()
        full_address = str(row.get("full_address", "")).strip()
        if not full_address or full_address.lower() == "nan":
            full_address = location
        lookup = contacts_lookup.get(_normalize_lookup(business_name), {})

        contact_name = lookup.get("contact_name") or f"Team at {business_name}"
        contact_email = lookup.get("email") or ""
        contact_phone = lookup.get("phone") or ""
        current_products = str(row.get("current_products", "")).strip()
        similar_products = str(row.get("similar_products", "")).strip()
        business_category = str(row.get("business_category", "")).strip()

        subject = f"Stores near {area} are selling more {product_category}"
        email_body = outreach_automation.generate_email_template(
            customer_id=contact_name,
            business_category=business_category,
            product_category=product_category,
            location=location,
            current_products=current_products,
            similar_products=similar_products,
        )
        maps_url = _build_maps_search_url(f"{business_name} {location}")

        rows.append(
            {
                "Business": business_name,
                "Contact Name": contact_name,
                "Email": contact_email,
                "Phone": contact_phone,
                "Location": location,
                "Full Address": full_address,
                "Google Maps": maps_url,
                "Current Products": current_products,
                "Recommended Product": product_category,
                "Email Subject": subject,
                "Email Draft": email_body,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    st.title("📊 Sales Analytics Dashboard")
    st.caption("See which businesses are the best fit for each product — and find new customers to target.")

    # ---- Sidebar ----
    with st.sidebar:
        st.header("📁 Data")

        use_sample = st.checkbox("Use Sample Data", value=False)
        if use_sample and st.button("Load Sample Data"):
            df, mapping = load_sample_data()
            if df is not None:
                st.session_state.sales_data = df
                st.session_state.business_mapping = mapping
                st.session_state.processed_data = df
                st.success("Loaded!")
                st.rerun()

        uploaded_file = st.file_uploader(
            "Upload Sales CSV",
            type=["csv", "numbers"],
            help="Upload a Faire orders summary CSV, or an Apple Numbers export (.numbers).",
        )
        if uploaded_file is not None:
            try:
                df = process_sales_data(uploaded_file)
                st.session_state.sales_data = df
                if "order_number" in df.columns:
                    order_count = df["order_number"].nunique()
                    st.success(
                        f"{len(df):,} product lines loaded ({order_count:,} orders, Faire export auto-formatted)"
                    )
                else:
                    st.success(f"{len(df)} transactions loaded")
            except Exception as e:
                st.error(str(e))

        st.divider()
        st.subheader("Business Types")
        mapping_file = st.file_uploader("Upload Business Types CSV", type=["csv"])
        if mapping_file is not None:
            try:
                mapping = load_business_mapping(mapping_file)
                st.session_state.business_mapping = mapping
                st.success(f"Loaded for {len(mapping)} customers")
            except Exception as e:
                st.error(str(e))

        if st.session_state.sales_data is not None:
            if st.button("Auto-Detect Business Types"):
                customers = get_unique_customers(st.session_state.sales_data)
                mapping = create_business_mapping(customers, mapping_file=None, use_keywords=True)
                st.session_state.business_mapping = mapping
                st.success(f"Classified {len(mapping)} customers")
                st.rerun()

    # ---- Guard: no data yet ----
    if st.session_state.sales_data is None:
        st.info("👈 Upload your sales data in the sidebar to get started.")
        return

    # ---- Merge business categories ----
    if st.session_state.business_mapping is not None:
        needs_merge = (
            st.session_state.processed_data is None
            or "business_category" not in st.session_state.processed_data.columns
            or st.session_state.processed_data["business_category"].isna().any()
        )
        if needs_merge:
            st.session_state.processed_data = merge_business_categories(
                st.session_state.sales_data, st.session_state.business_mapping
            )
    else:
        customers = get_unique_customers(st.session_state.sales_data)
        mapping = create_business_mapping(customers, mapping_file=None, use_keywords=True)
        st.session_state.business_mapping = mapping
        st.session_state.processed_data = merge_business_categories(
            st.session_state.sales_data, mapping
        )

    df = st.session_state.processed_data

    # ---- Filters ----
    with st.expander("🔍 Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            biz_options = ["All"] + sorted(df["business_category"].unique().tolist())
            selected_business = st.selectbox("Store Type", biz_options)
        with col2:
            prod_options = ["All"] + sorted(df["product_category"].unique().tolist())
            selected_product = st.selectbox("Product Category", prod_options)
        with col3:
            date_range = None
            if "transaction_date" in df.columns and df["transaction_date"].notna().any():
                min_d, max_d = df["transaction_date"].min().date(), df["transaction_date"].max().date()
                date_range = st.date_input("Time Period", value=(min_d, max_d), min_value=min_d, max_value=max_d)

    filtered_df = df.copy()
    if selected_business != "All":
        filtered_df = filtered_df[filtered_df["business_category"] == selected_business]
    if selected_product != "All":
        filtered_df = filtered_df[filtered_df["product_category"] == selected_product]
    if date_range and len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df["transaction_date"].dt.date >= date_range[0])
            & (filtered_df["transaction_date"].dt.date <= date_range[1])
        ]

    # ==================================================================
    # OVERVIEW
    # ==================================================================
    stats = analytics.get_summary_statistics(filtered_df)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Revenue", f"${stats['total_revenue']:,.0f}")
    c2.metric("Orders", f"{stats['total_transactions']:,}")
    c3.metric("Customers", f"{stats['unique_customers']:,}")
    c4.metric("Product Types", f"{stats['unique_product_categories']:,}")
    c5.metric("Avg Order", f"${stats['average_transaction_value']:,.2f}")

    # ==================================================================
    # MARKET SIGNALS  (auto-computed — no clicks required)
    # ==================================================================
    st.header("🎯 Strongest Market Signals")
    st.caption(
        "Which business types spend the most per store on each product — "
        "look for **new** stores of these types in these areas."
    )

    try:
        recs_df = _build_smart_recommendations(filtered_df)

        if len(recs_df) > 0:
            fig = px.bar(
                recs_df.head(10),
                x="Product",
                y="Avg Revenue / Store",
                color="Business Type",
                barmode="group",
                labels={"Avg Revenue / Store": "Avg Revenue per Store ($)"},
            )
            fig.update_layout(height=420, xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(
                recs_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Revenue": st.column_config.NumberColumn(format="$%.0f"),
                    "Avg Revenue / Store": st.column_config.NumberColumn(format="$%.0f"),
                },
            )
        else:
            st.info("Not enough data to compute recommendations with the current filters.")
    except Exception as e:
        st.error(f"Error computing recommendations: {str(e)}")

    # ==================================================================
    # BEST-SELLING COMBINATIONS
    # ==================================================================
    st.header("🏆 Best-Selling Combinations")
    col1, col2 = st.columns(2)
    with col1:
        metric_choice = st.selectbox(
            "Rank by",
            ["revenue", "count", "avg_value"],
            format_func=lambda x: {"revenue": "Total Sales", "count": "Order Count", "avg_value": "Avg Order Size"}[x],
            key="top_metric",
        )
    with col2:
        n_top = st.slider("Show top", 5, 50, 10, key="n_top")

    try:
        top_combos = analytics.get_top_combinations(filtered_df, n=n_top, metric=metric_choice)
        y_map = {"revenue": ("total_revenue", "Revenue ($)"), "count": ("transaction_count", "Orders"), "avg_value": ("avg_value", "Avg Value ($)")}
        y_col, y_label = y_map[metric_choice]

        fig = px.bar(
            top_combos, x="business_category", y=y_col, color="product_category",
            labels={"business_category": "Business Type", y_col: y_label}, barmode="group",
        )
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

        render_table(top_combos, currency_columns=["total_revenue", "avg_value"],
                     rename_map={"transaction_count": "Orders"}, hide_index=True)
    except Exception as e:
        st.error(f"Error: {str(e)}")

    # ==================================================================
    # SALES TRENDS
    # ==================================================================
    if "transaction_date" in filtered_df.columns and filtered_df["transaction_date"].notna().any():
        st.header("📅 Sales Trends")
        period_labels = {"D": "Daily", "W": "Weekly", "M": "Monthly", "Q": "Quarterly", "Y": "Yearly"}
        period = st.selectbox("Group by", list(period_labels.keys()), index=2,
                              format_func=lambda x: period_labels[x])
        try:
            trends = analytics.calculate_trends(filtered_df, period=period)
            fig = px.line(
                trends, x="period", y="sales_amount", color="business_category",
                line_group="product_category",
                labels={"period": "Period", "sales_amount": "Revenue ($)", "business_category": "Business Type"},
            )
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {str(e)}")

    # ==================================================================
    # FIND NEW CUSTOMERS  (consolidated tabs)
    # ==================================================================
    has_location = "location" in df.columns or ("city" in df.columns and "state" in df.columns)
    has_product_name = "product_name" in df.columns

    if has_location:
        st.header("📧 Find New Customers")
        st.caption(
            "Use your sales data to build a profile of who buys each product and where — "
            "then go find **new** stores that match that profile."
        )

        tab_names = ["Buyer Profile"]
        if has_product_name:
            tab_names.append("Product Deep-Dive")
            tab_names.append("Product Pitches")
        tab_names += ["Area Intelligence", "Store Prospector", "Brand Matcher", "Export"]
        tab_objects = st.tabs(tab_names)
        ti = 0

        # ---- Buyer Profile ----
        with tab_objects[ti]:
            st.caption("Pick a product category to see what type of store buys it and where.")
            profile_prod = st.selectbox(
                "Product Category",
                sorted(df["product_category"].unique().tolist()),
                key="profile_prod",
            )

            profile = _build_buyer_profile(df, product_category=profile_prod)
            if profile:
                st.success(profile["summary"])

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Revenue", f"${profile['total_revenue']:,.0f}")
                m2.metric("Orders", f"{profile['total_orders']:,}")
                m3.metric("Stores Buying", f"{profile['unique_stores']:,}")
                m4.metric("Avg Order", f"${profile['avg_order']:,.2f}")

                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("Top Business Types")
                    biz = profile["biz_breakdown"].head(10)
                    fig = px.bar(
                        biz, x="business_category", y="revenue", color="stores",
                        labels={"business_category": "Business Type", "revenue": "Revenue ($)", "stores": "# Stores"},
                    )
                    fig.update_layout(height=350, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(
                        biz[["business_category", "stores", "revenue", "avg_order", "pct_of_revenue"]].rename(columns={
                            "business_category": "Business Type", "stores": "Stores",
                            "revenue": "Revenue", "avg_order": "Avg Order", "pct_of_revenue": "% of Revenue",
                        }),
                        use_container_width=True, hide_index=True,
                        column_config={
                            "Revenue": st.column_config.NumberColumn(format="$%.0f"),
                            "Avg Order": st.column_config.NumberColumn(format="$%.2f"),
                        },
                    )

                with c2:
                    st.subheader("Top Areas")
                    if len(profile["area_breakdown"]) > 0:
                        areas = profile["area_breakdown"].head(10)
                        fig = px.bar(
                            areas, x="area", y="revenue", color="stores",
                            labels={"area": "Area", "revenue": "Revenue ($)", "stores": "# Stores"},
                        )
                        fig.update_layout(height=350, showlegend=False, xaxis_tickangle=-30)
                        st.plotly_chart(fig, use_container_width=True)
                        st.dataframe(
                            areas[["area", "stores", "revenue", "avg_order"]].rename(columns={
                                "area": "Area", "stores": "Stores", "revenue": "Revenue", "avg_order": "Avg Order",
                            }),
                            use_container_width=True, hide_index=True,
                            column_config={
                                "Revenue": st.column_config.NumberColumn(format="$%.0f"),
                                "Avg Order": st.column_config.NumberColumn(format="$%.2f"),
                            },
                        )
                    else:
                        st.info("No area data available.")

                st.info(
                    f"**Go prospect:** Look for new **{', '.join(profile['biz_breakdown'].head(2)['business_category'].tolist())}** "
                    f"stores in the top areas above. They're the most likely buyers for {profile_prod}."
                )
            else:
                st.warning("No sales data for this product category.")
        ti += 1

        # ---- Product Deep-Dive ----
        if has_product_name:
            with tab_objects[ti]:
                st.caption("Pick a specific product to see its full buyer profile.")
                deep_product = st.selectbox(
                    "Product",
                    sorted(df["product_name"].unique().tolist()),
                    key="deep_product",
                )

                profile = _build_buyer_profile(df, product_name=deep_product)
                if profile:
                    st.success(profile["summary"])

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total Revenue", f"${profile['total_revenue']:,.0f}")
                    m2.metric("Orders", f"{profile['total_orders']:,}")
                    m3.metric("Stores Buying", f"{profile['unique_stores']:,}")
                    m4.metric("Avg Order", f"${profile['avg_order']:,.2f}")

                    c1, c2 = st.columns(2)
                    with c1:
                        st.subheader("Business Types That Buy This")
                        biz = profile["biz_breakdown"].head(10)
                        st.dataframe(
                            biz[["business_category", "stores", "revenue", "avg_order", "pct_of_revenue"]].rename(columns={
                                "business_category": "Business Type", "stores": "Stores",
                                "revenue": "Revenue", "avg_order": "Avg Order", "pct_of_revenue": "% of Revenue",
                            }),
                            use_container_width=True, hide_index=True,
                            column_config={
                                "Revenue": st.column_config.NumberColumn(format="$%.0f"),
                                "Avg Order": st.column_config.NumberColumn(format="$%.2f"),
                            },
                        )
                    with c2:
                        st.subheader("Where It Sells")
                        if len(profile["area_breakdown"]) > 0:
                            areas = profile["area_breakdown"].head(10)
                            st.dataframe(
                                areas[["area", "stores", "revenue", "avg_order"]].rename(columns={
                                    "area": "Area", "stores": "Stores", "revenue": "Revenue", "avg_order": "Avg Order",
                                }),
                                use_container_width=True, hide_index=True,
                                column_config={
                                    "Revenue": st.column_config.NumberColumn(format="$%.0f"),
                                    "Avg Order": st.column_config.NumberColumn(format="$%.2f"),
                                },
                            )
                        else:
                            st.info("No area data available.")

                    top_types = profile["biz_breakdown"].head(2)["business_category"].tolist()
                    top_areas = profile["area_breakdown"].head(3)["area"].tolist() if len(profile["area_breakdown"]) > 0 else []
                    tip = f"**Go prospect:** Look for new **{', '.join(top_types)}** stores"
                    if top_areas:
                        tip += f" in **{', '.join(top_areas)}**"
                    tip += f". Stores like these spend ~**${profile['avg_order']:,.2f}** per order on this product."
                    st.info(tip)
                else:
                    st.warning("No sales data for this product.")
            ti += 1

        # ---- Product Pitches (specific SKUs + email scripts) ----
        if has_product_name:
            with tab_objects[ti]:
                st.caption(
                    "See **exact products** (not categories) that stores in an area already buy — "
                    "then copy email scripts to pitch those same products to new prospect stores."
                )
                pitch_areas, pitch_area_label = _get_area_options(df)
                if not pitch_areas:
                    st.warning("No area data available.")
                elif not product_level_analytics.is_real_product_name(
                    str(df["product_name"].dropna().iloc[0]) if len(df) else ""
                ):
                    st.warning(
                        "Your data only has order-level names (e.g. 'Order ABC123'). "
                        "Re-upload your **raw Faire export** so individual product names (pens, stickers, etc.) are preserved."
                    )
                else:
                    pc1, pc2, pc3 = st.columns(3)
                    with pc1:
                        pitch_area = st.selectbox(
                            pitch_area_label,
                            pitch_areas,
                            key="pitch_area",
                        )
                    with pc2:
                        pitch_top_n = st.slider(
                            "How many products to show",
                            min_value=3,
                            max_value=25,
                            value=10,
                            key="pitch_top_n",
                        )
                    with pc3:
                        pitch_min_stores = st.slider(
                            "Min stores that bought it locally",
                            min_value=1,
                            max_value=10,
                            value=2,
                            key="pitch_min_stores",
                        )

                    pitch_pack = product_level_analytics.build_area_product_pitch_pack(
                        df,
                        pitch_area,
                        top_n=pitch_top_n,
                        min_stores=pitch_min_stores,
                    )

                    if len(pitch_pack) == 0:
                        st.warning(
                            f"No specific products found for {pitch_area} with at least "
                            f"{pitch_min_stores} stores. Try a broader area or lower the minimum."
                        )
                    else:
                        st.subheader(f"Top products in {pitch_area}")
                        st.dataframe(
                            pitch_pack[
                                [
                                    "Product",
                                    "Stores in Area",
                                    "Orders in Area",
                                    "Units Sold",
                                    "Revenue",
                                    "Example Stores That Bought It",
                                ]
                            ],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Revenue": st.column_config.NumberColumn(format="$%.0f"),
                            },
                        )

                        selected_product = st.selectbox(
                            "Pick a product to pitch",
                            pitch_pack["Product"].tolist(),
                            key="pitch_selected_product",
                        )
                        template_row = pitch_pack[pitch_pack["Product"] == selected_product].iloc[0]
                        st.text_area(
                            "Email script template (copy and personalize)",
                            value=template_row["Email Script (copy for prospects)"],
                            height=260,
                            key="pitch_template_preview",
                        )

                        st.divider()
                        st.subheader("Send to prospect stores")
                        st.caption("One store per line: `Store Name, City` — existing clients are skipped automatically.")
                        prospect_lines = st.text_area(
                            "Prospect stores",
                            value="Example Gift Shop, Phoenix\nIndie Bookstore, Tempe",
                            height=120,
                            key="pitch_prospect_lines",
                        )
                        pitch_contact_upload = st.file_uploader(
                            "Optional contact CSV (store, contact_name, email)",
                            type=["csv"],
                            key="pitch_contact_upload",
                        )
                        pitch_contacts = {}
                        if pitch_contact_upload is not None:
                            try:
                                pitch_contacts = _prepare_contacts_lookup(pd.read_csv(pitch_contact_upload))
                            except Exception as e:
                                st.warning(f"Could not read contacts: {e}")

                        if st.button("Generate Product Pitch Emails", key="gen_product_pitch_emails"):
                            lines = [ln.strip() for ln in prospect_lines.splitlines() if ln.strip()]
                            pitch_emails = product_level_analytics.build_prospect_product_emails(
                                df,
                                pitch_area,
                                selected_product,
                                lines,
                                pitch_contacts,
                            )
                            if len(pitch_emails) == 0:
                                st.warning("No net-new prospect emails generated. Add different store names.")
                            else:
                                st.success(f"Generated {len(pitch_emails)} product-specific outreach emails.")
                                st.dataframe(pitch_emails, use_container_width=True, hide_index=True)
                                st.download_button(
                                    "Download Product Pitch Emails CSV",
                                    pitch_emails.to_csv(index=False),
                                    file_name=f"product_pitch_{selected_product[:40].replace(' ', '_')}_{pitch_area.replace(', ', '_')}.csv",
                                    mime="text/csv",
                                    key="dl_product_pitch_csv",
                                )
            ti += 1

        # ---- Area Intelligence ----
        with tab_objects[ti]:
            area_options, area_label = _get_area_options(df)
            st.caption(
                f"Pick a {area_label.lower()} to see what sells there and what types of stores buy."
            )
            if area_options:
                area_pick = st.selectbox(area_label, area_options, key="area_intel")

                area_df = _filter_df_to_area(df, area_pick)

                if len(area_df) > 0:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Revenue in Area", f"${area_df['sales_amount'].sum():,.0f}")
                    m2.metric("Stores in Area", f"{area_df['customer_id'].nunique():,}")
                    m3.metric("Product Types Sold", f"{area_df['product_category'].nunique():,}")

                    c1, c2 = st.columns(2)
                    with c1:
                        st.subheader("Top Products in This Area")
                        prod_area = (
                            area_df.groupby("product_category")
                            .agg(revenue=("sales_amount", "sum"), stores=("customer_id", "nunique"), orders=("sales_amount", "count"))
                            .sort_values("revenue", ascending=False)
                            .reset_index()
                            .head(10)
                        )
                        fig = px.bar(prod_area, x="product_category", y="revenue",
                                     labels={"product_category": "Product", "revenue": "Revenue ($)"})
                        fig.update_layout(height=350, xaxis_tickangle=-30)
                        st.plotly_chart(fig, use_container_width=True)

                    with c2:
                        st.subheader("Top Business Types in This Area")
                        biz_area = (
                            area_df.groupby("business_category")
                            .agg(revenue=("sales_amount", "sum"), stores=("customer_id", "nunique"))
                            .sort_values("revenue", ascending=False)
                            .reset_index()
                            .head(10)
                        )
                        fig = px.bar(biz_area, x="business_category", y="revenue",
                                     labels={"business_category": "Business Type", "revenue": "Revenue ($)"})
                        fig.update_layout(height=350, xaxis_tickangle=-30)
                        st.plotly_chart(fig, use_container_width=True)

                    st.info(
                        f"**Go prospect in {area_pick}:** The strongest combos here are "
                        f"**{prod_area.iloc[0]['product_category']}** sold to "
                        f"**{biz_area.iloc[0]['business_category']}** stores. "
                        f"Find more stores of that type in this area."
                    )
                else:
                    st.warning("No data for this area.")
            else:
                st.info("No state/area data available.")
        ti += 1

        # ---- Store Prospector ----
        with tab_objects[ti]:
            st.caption(
                "Pick a product and county/area, then focus on smaller niche stores with one-click search links."
            )

            sp_c1, sp_c2 = st.columns(2)
            with sp_c1:
                sp_prod = st.selectbox(
                    "Product Category",
                    sorted(df["product_category"].unique().tolist()),
                    key="sp_prod",
                )
            with sp_c2:
                sp_areas, sp_area_label = _get_area_options(df)
                if not sp_areas:
                    st.warning("No area data available for store prospecting.")
                    sp_area = ""
                else:
                    sp_area = st.selectbox(
                        sp_area_label,
                        sp_areas,
                        key="sp_area",
                    )

            profile = _build_buyer_profile(df, product_category=sp_prod)
            existing_clients_index = _build_existing_clients_index(df)

            if profile and len(profile["biz_breakdown"]) > 0 and sp_area:
                area_df = _filter_df_to_area(df, sp_area)
                area_prod_df = area_df[area_df["product_category"] == sp_prod].copy()

                size_c1, size_c2 = st.columns(2)
                with size_c1:
                    exclude_top_pct = st.slider(
                        "Exclude top-selling stores (%)",
                        min_value=0,
                        max_value=60,
                        value=40,
                        key="sp_exclude_top_pct",
                        help="Higher values remove larger stores so recommendations skew toward niche accounts.",
                    )
                with size_c2:
                    max_orders_per_store = st.slider(
                        "Max orders per store (niche focus)",
                        min_value=1,
                        max_value=25,
                        value=5,
                        key="sp_max_orders_per_store",
                    )
                lgbtq_map_mode = st.checkbox(
                    "Bias Google Maps links toward LGBTQ/progressive + woman-owned stores",
                    value=True,
                    key="sp_lgbtq_map_mode",
                )

                top_biz_types = profile["biz_breakdown"].head(5)
                niche_store_count = 0
                if len(area_prod_df) > 0:
                    orders_col = "order_number" if "order_number" in area_prod_df.columns else "sales_amount"
                    store_perf = (
                        area_prod_df.groupby(["customer_id", "business_category"])
                        .agg(
                            orders=(orders_col, "nunique"),
                            revenue=("sales_amount", "sum"),
                        )
                        .reset_index()
                    )
                    store_perf["avg_order"] = store_perf["revenue"] / store_perf["orders"].clip(lower=1)
                    if len(store_perf) > 0:
                        revenue_cap = float(store_perf["revenue"].quantile(max(0.0, 1 - (exclude_top_pct / 100))))
                        niche_perf = store_perf[
                            (store_perf["revenue"] <= revenue_cap)
                            & (store_perf["orders"] <= max_orders_per_store)
                        ].copy()
                        niche_store_count = len(niche_perf)
                        if len(niche_perf) > 0:
                            top_biz_types = (
                                niche_perf.groupby("business_category")
                                .agg(
                                    stores=("customer_id", "nunique"),
                                    revenue=("revenue", "sum"),
                                    orders=("orders", "sum"),
                                )
                                .sort_values("revenue", ascending=False)
                                .reset_index()
                            )
                            top_biz_types["avg_order"] = top_biz_types["revenue"] / top_biz_types["orders"].clip(lower=1)
                            top_biz_types = top_biz_types.head(5)

                prospect_segments = _get_prospect_segments(sp_prod)

                st.markdown(
                    f"Based on your data, **{sp_prod}** sells best to these smaller store types. "
                    f"Click the links below to search Google Maps for new stores in **{sp_area}**."
                )
                if niche_store_count:
                    st.caption(
                        f"Niche store mode is using {niche_store_count} smaller stores in {sp_area} as the reference set."
                    )

                pred_df = pd.DataFrame(
                    [
                        {
                            "Predicted Store Segment": seg["segment"],
                            "Fit Score": seg["fit_score"],
                            "Why It Fits": seg["why"],
                            "Google Maps Search": _build_maps_search_url(
                                _with_focus_map_terms(f"{seg['segment']} in {sp_area}", lgbtq_map_mode)
                            ),
                        }
                        for seg in prospect_segments
                    ]
                )
                st.dataframe(
                    pred_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Fit Score": st.column_config.NumberColumn(
                            "Fit Score",
                            help="Estimated demand fit based on your current buyer pattern.",
                            format="%d",
                        ),
                        "Google Maps Search": st.column_config.LinkColumn(
                            "Google Maps Search",
                            display_text="Open Maps",
                        ),
                    },
                )

                # Build search links for each top business type
                for _, row in top_biz_types.iterrows():
                    biz_type = row["business_category"]
                    stores_buying = int(row["stores"])
                    avg_ord = row["avg_order"]
                    rev = row["revenue"]

                    query = _with_focus_map_terms(f"{biz_type} in {sp_area}", lgbtq_map_mode)
                    maps_url = _build_maps_search_url(query)
                    google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                    faire_query = f"{biz_type} {sp_area}"
                    faire_url = f"https://www.faire.com/search?q={faire_query.replace(' ', '+')}"

                    with st.container(border=True):
                        lc, rc = st.columns([3, 2])
                        with lc:
                            st.markdown(f"### {biz_type}")
                            st.markdown(
                                f"**{stores_buying}** of your existing stores of this type buy {sp_prod}  \n"
                                f"Avg order: **${avg_ord:,.2f}** · Total revenue: **${rev:,.0f}**"
                            )
                        with rc:
                            st.markdown(f"[🗺️ Google Maps]({maps_url})")
                            st.markdown(f"[🔍 Google Search]({google_url})")
                            st.markdown(f"[🛒 Faire Marketplace]({faire_url})")

                if len(area_df) > 0 and "city" in area_df.columns:
                    cities_with_buyers = (
                        area_df[area_df["product_category"] == sp_prod]
                        .groupby("city")
                        .agg(stores=("customer_id", "nunique"), revenue=("sales_amount", "sum"))
                        .sort_values("revenue", ascending=False)
                        .reset_index()
                    )
                    if len(cities_with_buyers) > 0:
                        with st.expander(f"Cities in {sp_area} where you already sell {sp_prod}"):
                            st.dataframe(
                                cities_with_buyers.head(15).rename(columns={
                                    "city": "City", "stores": "Your Stores There", "revenue": "Revenue",
                                }),
                                use_container_width=True, hide_index=True,
                                column_config={"Revenue": st.column_config.NumberColumn(format="$%.0f")},
                            )
                            st.caption("Look for similar store types in nearby cities where you DON'T have buyers yet.")

                    # Find cities in the area where you have NO buyers for this product
                    all_cities = area_df["city"].dropna().unique()
                    buyer_cities = set(cities_with_buyers["city"].tolist()) if len(cities_with_buyers) > 0 else set()
                    untapped_cities = [c for c in all_cities if c not in buyer_cities and c and str(c) != "nan"]

                    if untapped_cities:
                        with st.expander(f"Cities in {sp_area} with stores but NO {sp_prod} sales yet"):
                            top_biz = top_biz_types.iloc[0]["business_category"]
                            for city in sorted(untapped_cities)[:15]:
                                cquery = _with_focus_map_terms(
                                    f"{top_biz} in {city}, {sp_area}",
                                    lgbtq_map_mode,
                                )
                                cmaps = _build_maps_search_url(cquery)
                                st.markdown(f"- **{city}** — [Search for {top_biz} on Maps]({cmaps})")

                with st.expander("Paste real stores and predict who will want this product"):
                    st.caption(
                        "One store per line: `Store Name, City, Optional Store Type`."
                    )
                    sample_text = (
                        "Changing Hands Bookstore, Phoenix, Bookstore\n"
                        "Frances Boutique, Phoenix, Gift Shop\n"
                        "Brick Road Coffee, Tucson, LGBTQ+ Friendly Book + Gift Shop"
                    )
                    prospect_input = st.text_area(
                        "Candidate stores",
                        value=sample_text,
                        key="prospect_score_input",
                        height=130,
                    )
                    focus_keywords_raw = st.text_input(
                        "LGBTQ / liberal / woman-owned focus keywords (comma-separated)",
                        value="lgbtq, lgbt, queer, pride, progressive, liberal, feminist, inclusive, social justice, woman owned, women owned, female owned, womxn owned",
                        key="prospect_focus_keywords",
                    )
                    require_focus_match = st.checkbox(
                        "Only show stores matching LGBTQ / liberal / woman-owned keywords in name/type",
                        value=True,
                        key="require_focus_match",
                    )
                    only_near_existing_clients = st.checkbox(
                        "Only include stores within a few miles of current clients",
                        value=False,
                        key="only_near_existing_clients",
                    )
                    distance_miles = st.slider(
                        "Distance from current client (miles)",
                        min_value=1,
                        max_value=50,
                        value=5,
                        key="distance_miles",
                        disabled=not only_near_existing_clients,
                    )
                    st.caption("Existing clients are automatically excluded from predictor results.")
                    if st.button("Predict Store Fit", key="predict_store_fit_btn"):
                        focus_keywords = _extract_focus_keywords(focus_keywords_raw)
                        scored_df = _score_candidate_prospects(
                            prospect_input,
                            sp_area,
                            prospect_segments,
                            existing_clients_index,
                            focus_keywords=focus_keywords,
                            require_focus_match=require_focus_match,
                            maps_focus_mode=lgbtq_map_mode,
                        )
                        if len(scored_df) == 0:
                            if require_focus_match:
                                st.warning(
                                    "No stores matched your LGBTQ/liberal focus keywords. "
                                    "Try broader keywords or turn off strict focus mode."
                                )
                            else:
                                st.warning("Add at least one store line to score prospects.")
                        else:
                            already_clients = int(scored_df["Already Client"].sum())
                            scored_df = scored_df[~scored_df["Already Client"]].reset_index(drop=True)
                            if already_clients > 0:
                                st.info(
                                    f"Removed {already_clients} existing clients from candidate list."
                                )
                            if only_near_existing_clients and len(scored_df) > 0:
                                before_distance = len(scored_df)
                                scored_df, distance_msg = _apply_distance_filter(
                                    scored_df,
                                    df,
                                    sp_area,
                                    float(distance_miles),
                                )
                                st.info(
                                    f"{distance_msg} (filtered out {max(before_distance - len(scored_df), 0)})."
                                )
                            st.session_state["latest_scored_prospects"] = scored_df
                            if len(scored_df) == 0:
                                st.warning(
                                    "No net-new stores left after applying your filters. Try broader criteria."
                                )
                            else:
                                st.success(f"Scored {len(scored_df)} net-new candidate stores.")
                                st.dataframe(
                                    scored_df,
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        "Fit Score": st.column_config.ProgressColumn(
                                            "Fit Score",
                                            min_value=0,
                                            max_value=100,
                                            format="%d",
                                        ),
                                        "Google Maps": st.column_config.LinkColumn(
                                            "Google Maps", display_text="Open Store"
                                        ),
                                    },
                                )

                st.divider()
                st.subheader("Outreach Contacts + Email Drafts")
                st.caption(
                    "Build a contact-first list for outreach. If your sales file has no contact names/emails, "
                    "upload a contact CSV to enrich this list."
                )
                contact_upload = st.file_uploader(
                    "Optional contact CSV (columns like business/store, contact_name, email, phone)",
                    type=["csv"],
                    key="contact_enrichment_upload",
                )
                contacts_lookup = {}
                if contact_upload is not None:
                    try:
                        contacts_df = pd.read_csv(contact_upload)
                        contacts_lookup = _prepare_contacts_lookup(contacts_df)
                        st.success(
                            f"Loaded {len(contacts_df)} contact rows for enrichment."
                        )
                    except Exception as e:
                        st.warning(f"Could not read contacts CSV: {str(e)}")

                max_outreach = st.slider(
                    "How many net-new prospects to generate",
                    min_value=5,
                    max_value=150,
                    value=30,
                    key="max_outreach_rows",
                )

                if st.button("Generate Outreach Contact List", key="gen_outreach_contacts"):
                    try:
                        scored_cache = st.session_state.get("latest_scored_prospects")
                        if scored_cache is None or len(scored_cache) == 0:
                            st.warning(
                                "Run 'Predict Store Fit' first so we can build outreach for net-new stores."
                            )
                        else:
                            net_new = scored_cache[~scored_cache["Already Client"]].copy()
                            if len(net_new) == 0:
                                st.warning(
                                    "All scored stores appear to be existing clients. Add different candidates."
                                )
                            else:
                                net_new = net_new.head(max_outreach).reset_index(drop=True)
                                rows = []
                                for _, candidate in net_new.iterrows():
                                    business = str(candidate.get("Store", "")).strip()
                                    city = str(candidate.get("City", "")).strip()
                                    location = f"{city}, {sp_area}" if city else sp_area
                                    predicted_segment = str(candidate.get("Predicted Segment", "")).strip()
                                    fit_score = int(candidate.get("Fit Score", 0))
                                    match = contacts_lookup.get(_normalize_lookup(business), {})
                                    contact_name = match.get("contact_name") or f"Team at {business}"
                                    contact_email = match.get("email") or ""
                                    contact_phone = match.get("phone") or ""
                                    email_subject = f"Nearby stores are selling more {sp_prod}"
                                    email_draft = (
                                        f"Subject: {email_subject}\n\n"
                                        f"Hi {contact_name},\n\n"
                                        f"We noticed stores near {location} similar to yours are performing well with {sp_prod}. "
                                        f"Based on your store profile ({predicted_segment}), we thought you might be interested in adding this line.\n\n"
                                        "If helpful, we can share best-sellers and a starter assortment recommendation.\n\n"
                                        "Best,\nSales Team"
                                    )
                                    rows.append(
                                        {
                                            "Business": business,
                                            "Contact Name": contact_name,
                                            "Email": contact_email,
                                            "Phone": contact_phone,
                                            "Location": location,
                                            "Predicted Segment": predicted_segment,
                                            "Fit Score": fit_score,
                                            "Google Maps": _build_maps_search_url(f"{business} {location}"),
                                            "Email Subject": email_subject,
                                            "Email Draft": email_draft,
                                        }
                                    )

                                contacts_df = pd.DataFrame(rows).sort_values(
                                    "Fit Score", ascending=False
                                )
                                filled_emails = int((contacts_df["Email"].astype(str).str.len() > 0).sum())
                                m1, m2, m3 = st.columns(3)
                                m1.metric("Prospects", len(contacts_df))
                                m2.metric("With Contact Email", filled_emails)
                                m3.metric(
                                    "Need Email Research",
                                    max(len(contacts_df) - filled_emails, 0),
                                )

                                st.dataframe(
                                    contacts_df,
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        "Google Maps": st.column_config.LinkColumn(
                                            "Google Maps", display_text="Open Store"
                                        )
                                    },
                                )

                                st.download_button(
                                    "Download Outreach Contacts CSV",
                                    contacts_df.to_csv(index=False),
                                    file_name=f"outreach_contacts_{sp_prod.replace(' ', '_')}_{sp_area}_{datetime.now().strftime('%Y%m%d')}.csv",
                                    mime="text/csv",
                                    key="dl_outreach_contacts_csv",
                                )
                    except Exception as e:
                        st.error(f"Error generating outreach contacts: {str(e)}")
            else:
                st.warning("No data for this product category.")
        ti += 1

        # ---- Brand Matcher ----
        with tab_objects[ti]:
            st.caption("Upload your brand's product list to find stores that should carry them.")
            brand_file = st.file_uploader("Brand Products CSV", type=["csv"], key="brand_upload")
            use_hilarious = st.checkbox("Use Hilarious Humanitarian sample data", value=True, key="use_hilarious")

            if brand_file is not None or use_hilarious:
                try:
                    if use_hilarious and brand_file is None:
                        brand_products = brand_product_matcher.load_brand_products("data/hilarious_humanitarian_products.csv")
                    else:
                        import tempfile, os
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                            tmp.write(brand_file.getvalue())
                            tmp_path = tmp.name
                        brand_products = brand_product_matcher.load_brand_products(tmp_path)
                        os.unlink(tmp_path)

                    with st.expander("View Brand Products"):
                        render_table(brand_products, hide_index=True)

                    c1, c2 = st.columns(2)
                    with c1:
                        match_state = st.selectbox("State (optional)", [None] + _get_states(df), key="match_state")
                    with c2:
                        match_biz = st.selectbox("Store Type (optional)",
                            [None] + sorted(df["business_category"].unique().tolist()), key="match_biz_cat")
                    max_matches = st.slider("Max results", 10, 100, 30, key="max_matches")

                    if st.button("Find Matching Stores", key="find_brand_buyers", type="primary"):
                        try:
                            matches = brand_product_matcher.generate_brand_outreach_list(
                                df, brand_products, location_filter=match_state,
                                business_category_filter=match_biz, max_results=max_matches,
                            )
                            if len(matches) > 0:
                                st.success(f"Found {len(matches)} matching stores")
                                m1, m2 = st.columns(2)
                                m1.metric("Stores", len(matches))
                                m2.metric("Locations", matches["location"].nunique())

                                mcols = ["customer_id", "business_category", "location"]
                                if "full_address" in matches.columns:
                                    mcols.append("full_address")
                                mcols += ["brand_category", "recommended_brand_products", "current_products"]
                                render_table(
                                    matches[mcols],
                                    rename_map={"customer_id": "Business", "business_category": "Type",
                                                "brand_category": "Category",
                                                "recommended_brand_products": "Products To Sell",
                                                "current_products": "Currently Buys"},
                                    hide_index=True,
                                )
                                st.session_state.brand_matches = matches
                            else:
                                st.warning("No matches. Try different filters.")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
                except Exception as e:
                    st.error(f"Error loading brand products: {str(e)}")
        ti += 1

        # ---- Export ----
        with tab_objects[ti]:
            st.caption("Download buyer profiles or brand match data.")

            # Export buyer profile for any product category
            st.subheader("Export Buyer Profile")
            export_prod = st.selectbox(
                "Product Category to export",
                sorted(df["product_category"].unique().tolist()),
                key="export_profile_prod",
            )
            ep = _build_buyer_profile(df, product_category=export_prod)
            if ep:
                rows = []
                for _, r in ep["biz_breakdown"].iterrows():
                    for _, a in ep["area_breakdown"].iterrows() if len(ep["area_breakdown"]) > 0 else pd.DataFrame([{"area": "All"}]).iterrows():
                        rows.append({
                            "Product Category": export_prod,
                            "Business Type": r["business_category"],
                            "Area": a.get("area", "All"),
                            "Biz Revenue": r["revenue"],
                            "Biz Stores": r["stores"],
                            "Biz Avg Order": r["avg_order"],
                        })
                export_df = pd.DataFrame(rows)
                st.download_button(
                    "Download Buyer Profile CSV", export_df.to_csv(index=False),
                    file_name=f"buyer_profile_{export_prod.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv", key="dl_profile",
                )
                st.dataframe(export_df.head(20), use_container_width=True, hide_index=True)

            # Brand matches export
            if "brand_matches" in st.session_state and len(st.session_state.brand_matches) > 0:
                st.divider()
                bm = st.session_state.brand_matches
                st.subheader(f"Brand Matches — {len(bm)} stores")
                bfmt = st.selectbox("Format", ["CSV", "JSON"], key="brand_export_format")
                if bfmt == "CSV":
                    st.download_button("Download CSV", bm.to_csv(index=False),
                        file_name=f"brand_matches_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv", key="dl_brand_csv")
                else:
                    st.download_button("Download JSON", bm.to_json(orient="records", indent=2),
                        file_name=f"brand_matches_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json", key="dl_brand_json")

    # ==================================================================
    # DOWNLOAD REPORTS
    # ==================================================================
    st.header("💾 Download Reports")
    c1, c2 = st.columns(2)
    with c1:
        try:
            matrix = analytics.calculate_category_matrix(filtered_df)
            st.download_button("📊 Store-Product Matrix", matrix.to_csv(),
                file_name=f"matrix_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
        except Exception:
            pass
    with c2:
        try:
            tc = analytics.get_top_combinations(filtered_df, n=100)
            st.download_button("🏆 Top Combinations", tc.to_csv(index=False),
                file_name=f"top_combos_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
        except Exception:
            pass


if __name__ == "__main__":
    main()

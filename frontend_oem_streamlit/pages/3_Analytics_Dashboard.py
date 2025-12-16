import streamlit as st
import pandas as pd

from utils.layout import set_base_page_config, sidebar_section
from api_client import client, normalize_faults
from utils.charts import remaining_life_chart

set_base_page_config()

@st.cache_data(ttl=20)
def load_df(limit: int):
    return normalize_faults(client.get_faults(limit))

def reco(row):
    sev = (row["severity"] or "").lower()
    comp = (row["component"] or "").lower()

    if "coolant" in comp:
        return "Immediate check" if sev in ("critical", "high") else "Service within 2 weeks"
    if "battery" in comp or "alternator" in comp:
        return "Urgent electrical check" if sev in ("critical", "high") else "Check within 1 week"

    if sev == "critical": return "Immediate workshop visit"
    if sev == "high": return "Visit in 1 week"
    if sev == "medium": return "Fix at next service"
    return "Monitor"

def main():
    limit = sidebar_section("Analytics Dashboard")
    st.title("Analytics Dashboard")

    df = load_df(limit)
    if df.empty:
        st.info("No data.")
        return

    st.subheader("Remaining Life by VIN")
    life = (
        df.dropna(subset=["remaining_km"])
        .groupby("vin", as_index=False)["remaining_km"]
        .min()
        .sort_values("remaining_km")
    )

    st.dataframe(life, use_container_width=True, hide_index=True)
    remaining_life_chart(life)

    df["maintenance_reco"] = df.apply(reco, axis=1)
    st.subheader("Maintenance Recommendations")
    st.dataframe(df[["detected_at", "vin", "component", "severity", "remaining_km", "maintenance_reco"]],
                 use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd

from utils.layout import set_base_page_config, sidebar_section
from api_client import client, normalize_faults, build_vehicle_table, compute_fleet_risk_score
from utils.charts import severity_chart, component_chart

set_base_page_config()

@st.cache_data(ttl=20)
def load_df(limit: int):
    return normalize_faults(client.get_faults(limit))

def main():
    limit = sidebar_section("Fleet Overview")
    st.title("Fleet Overview")

    df = load_df(limit)
    vehicles = build_vehicle_table(df)

    if df.empty:
        st.info("No faults yet.")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Vehicles", vehicles["vin"].nunique())
    c2.metric("Vehicles w/ Faults", len(vehicles))
    c3.metric("Critical", (df["severity"].str.lower() == "critical").sum())
    c4.metric("Total Faults", len(df))
    c5.metric("Risk Score", compute_fleet_risk_score(df))

    st.subheader("Severity Mix")
    severity_chart(df["severity"].str.capitalize().value_counts())

    st.subheader("Component Distribution")
    component_chart(df["component"].fillna("Unknown").value_counts())

    st.subheader("Vehicle Status Table")
    st.dataframe(vehicles, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd

from utils.layout import set_base_page_config, sidebar_section
from api_client import client, normalize_faults, build_vehicle_table

set_base_page_config()

@st.cache_data(ttl=20)
def load_df(limit: int):
    return normalize_faults(client.get_faults(limit))

def main():
    limit = sidebar_section("Vehicle Detail")
    st.title("Vehicle Detail")

    df = load_df(limit)
    vehicles = build_vehicle_table(df)

    if vehicles.empty:
        st.info("No vehicle data.")
        return

    vin = st.selectbox("Select VIN", vehicles["vin"].tolist())
    v_df = df[df["vin"] == vin]

    if v_df.empty:
        st.warning("No data for this VIN")
        return

    latest = v_df.iloc[0]

    st.metric("Active Component", latest["component"])
    st.metric("Severity", latest["severity"].capitalize())
    st.metric("Remaining KM", latest["remaining_km"])

    st.markdown("### Telemetry Snapshot")
    tele_cols = ["coolant_temp_c", "coolant_pressure_bar", "engine_rpm", "vibration_level", "battery_voltage"]
    st.json({c: latest.get(c) for c in tele_cols})

    st.markdown("### Fault History")
    st.dataframe(v_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd

def severity_chart(series: pd.Series):
    if series.empty:
        st.write("No data.")
        return
    st.bar_chart(series)

def component_chart(series: pd.Series):
    if series.empty:
        st.write("No data.")
        return
    st.bar_chart(series)

def remaining_life_chart(df: pd.DataFrame):
    if df.empty:
        st.write("No data.")
        return
    st.bar_chart(df.set_index("vin")["remaining_km"])

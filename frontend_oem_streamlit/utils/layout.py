import streamlit as st
from PIL import Image
import os

APP_TITLE = "AutoSentinels OEM Console"

def set_base_page_config():
    st.set_page_config(page_title=APP_TITLE, layout="wide")

def _load_logo():
    path = os.path.join("assets", "logo.png")
    return Image.open(path) if os.path.exists(path) else None

def render_home_header(title: str):
    cols = st.columns([1, 3])
    logo = _load_logo()

    with cols[0]:
        if logo:
            st.image(logo, use_container_width=True)

    with cols[1]:
        st.title(title)

def sidebar_section(name: str):
    st.sidebar.title("OEM Console")
    st.sidebar.subheader(name)
    return st.sidebar.slider("Fault records", 50, 1000, 300, 50)

import streamlit as st
from utils.layout import set_base_page_config, render_home_header

set_base_page_config()

def main():
    render_home_header("AutoSentinels OEM Console")

    st.write(
        """
Welcome to the **AutoSentinels OEM Console**.

Use the left sidebar to navigate:

- **Fleet Overview**  
- **Vehicle Detail**  
- **Analytics Dashboard**  
- **Agent Brain (OEM AI Assistant)**  

Ensure your backend is running and reachable via  
`AUTOSENTINELS_BACKEND_URL` (default: `http://localhost:8000`).
"""
    )

if __name__ == "__main__":
    main()

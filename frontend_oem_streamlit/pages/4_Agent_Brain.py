import streamlit as st
import pandas as pd

from utils.layout import set_base_page_config, sidebar_section
from api_client import client

set_base_page_config()

def main():
    # We still render the sidebar slider for consistency, but we do not use the limit here.
    sidebar_section("Agent Brain")
    st.title("Agent Brain – OEM AI Assistant")

    st.write(
        """
Ask any question about your fleet.  
The Agent Brain will query the backend `/oem_chat` endpoint
(which uses the LLM + fleet snapshot) and return:

- A natural-language answer
- A tabular view of the underlying fleet data (if provided)
        """
    )

    query = st.text_area(
        "Your question",
        placeholder="Example: Which VINs have repeated coolant issues and need attention this week?",
    )

    if st.button("Ask Agent Brain") and query.strip():
        with st.spinner("Querying OEM Agent Brain via /oem_chat..."):
            resp = client.post_oem_chat(query.strip())

        st.markdown("### Answer")
        st.write(resp.get("answer") or "No answer returned by backend.")

        table = resp.get("table")
        if isinstance(table, list) and table:
            st.markdown("### Fleet snapshot used for this answer")
            st.dataframe(pd.DataFrame(table), use_container_width=True)
        else:
            st.caption("No tabular fleet snapshot was returned for this query.")

if __name__ == "__main__":
    main()
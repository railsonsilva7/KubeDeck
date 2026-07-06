import streamlit as st
import os
from utils import get_asset_path

logo_path = get_asset_path("logo-KubeDeck.svg")
logo_exists = os.path.exists(logo_path)
st.set_page_config(page_title="KubeDeck", page_icon=logo_path if logo_exists else "🚢", layout="wide")
import pandas as pd

from i18n import get_text

lang = st.session_state.get("lang", "pt")

if "is_connected" not in st.session_state or not st.session_state.is_connected:
    st.warning(get_text(lang, "pls_connect"))
    st.stop()

st.title(get_text(lang, "net_title"))
ns = st.session_state.selected_namespace
client = st.session_state.k8s_client
st.markdown(f"{get_text(lang, 'showing_ns')} **{ns}**")

tab1, tab2 = st.tabs([get_text(lang, "services"), get_text(lang, "ingresses")])

with tab1:
    st.subheader(get_text(lang, "services"))
    try:
        svcs = client.get_services(ns)
        if svcs:
            st.dataframe(pd.DataFrame(svcs), width="stretch", hide_index=True)
        else:
            st.info(get_text(lang, "no_services"))
    except Exception as e:
        st.error(str(e))

with tab2:
    st.subheader(get_text(lang, "ingresses"))
    try:
        ings = client.get_ingresses(ns)
        if ings:
            st.dataframe(pd.DataFrame(ings), width="stretch", hide_index=True)
        else:
            st.info(get_text(lang, "no_ingresses"))
    except Exception as e:
        st.error(str(e))

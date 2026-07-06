import streamlit as st
import pandas as pd
from k8s_client import K8sClient
from i18n import get_text
from utils import get_asset_path
import os

logo_path = get_asset_path("logo-KubeDeck.svg")
logo_exists = os.path.exists(logo_path)

st.set_page_config(
    page_title="KubeDeck",
    page_icon=logo_path if logo_exists else "🚢",
    layout="wide"
)



# Initialize Session State
if "k8s_client" not in st.session_state:
    st.session_state.k8s_client = K8sClient()
if "is_connected" not in st.session_state:
    st.session_state.is_connected = False
if "selected_namespace" not in st.session_state:
    st.session_state.selected_namespace = "default"
if "active_tunnels" not in st.session_state:
    st.session_state.active_tunnels = {}
if "lang" not in st.session_state:
    st.session_state.lang = "pt"

lang = st.session_state.lang

# --- Sidebar Authentication ---
with st.sidebar:
    # Language Selector
    c_pt, c_en, c_es, c_zh = st.columns(4)
    with c_pt:
        if st.button("🇧🇷", key="lang_pt"):
            st.session_state.lang = "pt"
            st.rerun()
    with c_en:
        if st.button("🇺🇸", key="lang_en"):
            st.session_state.lang = "en"
            st.rerun()
    with c_es:
        if st.button("🇪🇸", key="lang_es"):
            st.session_state.lang = "es"
            st.rerun()
    with c_zh:
        if st.button("🇨🇳", key="lang_zh"):
            st.session_state.lang = "zh"
            st.rerun()
            
    st.divider()
    
    st.header(get_text(lang, "auth_header"))
    
    if not st.session_state.is_connected:
        uploaded_file = st.file_uploader(get_text(lang, "upload_kubeconfig"), type=["yaml", "yml"])
        if uploaded_file is not None:
            if st.button(get_text(lang, "btn_connect"), type="primary"):
                bytes_data = uploaded_file.getvalue()
                success, msg = st.session_state.k8s_client.load_config_from_bytes(bytes_data)
                if success:
                    st.session_state.is_connected = True
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.success(get_text(lang, "connected_success"))
        # Global Namespace Selector
        namespaces = [get_text(lang, "all_namespaces")] + st.session_state.k8s_client.get_namespaces()
        idx = namespaces.index(st.session_state.selected_namespace) if st.session_state.selected_namespace in namespaces else 0
        selected_ns = st.selectbox(get_text(lang, "namespace"), namespaces, index=idx)
        st.session_state.selected_namespace = selected_ns
        
        st.divider()
        if st.button(get_text(lang, "btn_disconnect"), type="secondary"):
            for data in st.session_state.active_tunnels.values():
                st.session_state.k8s_client.stop_tunnel(data["process"])
            st.session_state.active_tunnels = {}
            st.session_state.k8s_client.cleanup()
            st.session_state.is_connected = False
            st.rerun()

# --- Main Page Content ---
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if logo_exists:
        st.image(logo_path, width="stretch")

st.markdown(f"<h1 style='text-align: center;'>{get_text(lang, 'overview_title')}</h1>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)
if st.session_state.is_connected:
    client = st.session_state.k8s_client
    info = client.get_cluster_info()
    
    if info:
        st.subheader(get_text(lang, "cluster_info"))
        col1, col2 = st.columns(2)
        col1.metric(get_text(lang, "current_context"), info.get("current_context", "N/A"))
        col2.metric(get_text(lang, "total_clusters"), len(info.get("clusters", [])))

    st.divider()
    
    st.subheader(get_text(lang, "nodes"))
    with st.spinner("Buscando nós..."):
        try:
            nodes = client.get_nodes()
            if nodes:
                st.dataframe(pd.DataFrame(nodes), width="stretch", hide_index=True)
            else:
                st.info(get_text(lang, "no_nodes"))
        except Exception as e:
            st.error(f"{get_text(lang, 'error_prefix')} {str(e)}")
            
    st.markdown(get_text(lang, "nav_hint"))
else:
    st.info(get_text(lang, "upload_hint"))

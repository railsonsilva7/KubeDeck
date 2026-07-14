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

st.title(get_text(lang, "config_title"))
ns = st.session_state.selected_namespace
client = st.session_state.k8s_client
st.markdown(f"{get_text(lang, 'showing_ns')} **{ns}**")

tab1, tab2 = st.tabs([get_text(lang, "configmaps"), get_text(lang, "secrets")])

with tab1:
    st.subheader(get_text(lang, "configmaps"))
    try:
        cms = client.get_configmaps(ns)
        if cms:
            st.dataframe(pd.DataFrame(cms), width="stretch", hide_index=True)
            
            st.markdown(get_text(lang, "view_content"))
            all_ns_label = get_text(lang, "all_namespaces")
            options = [f"{c['Namespace']}/{c['Name']}" if ns == all_ns_label or ns == "All Namespaces" else c['Name'] for c in cms]
            selected_cm = st.selectbox(get_text(lang, "select_cm"), options, key="cm_sel", index=None, placeholder=get_text(lang, "choose_cm"))
            
            if selected_cm:
                if ns == all_ns_label or ns == "All Namespaces":
                    target_ns, target_name = selected_cm.split("/", 1)
                else:
                    target_ns, target_name = ns, selected_cm
                    
                details = client.get_configmap_details(target_name, target_ns)
                if details and not "error" in details:
                    for k, v in details.items():
                        with st.expander(f"{k}"):
                            st.code(v)
                elif "error" in details:
                    st.error(details["error"])
                else:
                    st.info(get_text(lang, "empty_cm"))
        else:
            st.info(get_text(lang, "no_cm"))
    except Exception as e:
        st.error(str(e))

with tab2:
    st.subheader(get_text(lang, "secrets"))
    st.info(get_text(lang, "secrets_warning"))
    try:
        secrets = client.get_secrets(ns)
        if secrets:
            st.dataframe(pd.DataFrame(secrets), width="stretch", hide_index=True)
            
            st.markdown(get_text(lang, "reveal_creds"))
            all_ns_label = get_text(lang, "all_namespaces")
            options = [f"{s['Namespace']}/{s['Name']}" if ns == all_ns_label or ns == "All Namespaces" else s['Name'] for s in secrets]
            selected_secret = st.selectbox(get_text(lang, "select_sec"), options, key="sec_sel", index=None, placeholder=get_text(lang, "choose_sec"))
            
            if selected_secret:
                if ns == all_ns_label or ns == "All Namespaces":
                    target_ns, target_name = selected_secret.split("/", 1)
                else:
                    target_ns, target_name = ns, selected_secret
                    
                details = client.get_secret_details(target_name, target_ns)
                if details and not "error" in details:
                    env_str = "\n".join([f'{k}="{v}"' for k, v in details.items()])
                    st.download_button(get_text(lang, "download_env"), data=env_str, file_name=f"{target_name}.env")
                    for k, v in details.items():
                        with st.expander(f"{k}"):
                            st.code(v)
                elif "error" in details:
                    st.error(details["error"])
                else:
                    st.info(get_text(lang, "empty_sec"))
        else:
            st.info(get_text(lang, "no_sec"))
    except Exception as e:
        st.error(str(e))

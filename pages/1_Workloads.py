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

st.title(get_text(lang, "workloads_title"))
ns = st.session_state.selected_namespace
client = st.session_state.k8s_client
st.markdown(f"{get_text(lang, 'showing_ns')} **{ns}**")

tab1, tab2, tab3, tab4 = st.tabs([get_text(lang, "deployments"), get_text(lang, "statefulsets"), get_text(lang, "daemonsets"), get_text(lang, "pods")])

with tab1:
    st.subheader(get_text(lang, "deployments"))
    try:
        deps = client.get_deployments(ns)
        if deps:
            st.dataframe(pd.DataFrame(deps), width="stretch", hide_index=True)
        else:
            st.info(get_text(lang, "no_deployments"))
    except Exception as e:
        st.error(str(e))

with tab2:
    st.subheader(get_text(lang, "statefulsets"))
    try:
        sts = client.get_statefulsets(ns)
        if sts:
            st.dataframe(pd.DataFrame(sts), width="stretch", hide_index=True)
        else:
            st.info(get_text(lang, "no_sts"))
    except Exception as e:
        st.error(str(e))

with tab3:
    st.subheader(get_text(lang, "daemonsets"))
    try:
        dss = client.get_daemonsets(ns)
        if dss:
            st.dataframe(pd.DataFrame(dss), width="stretch", hide_index=True)
        else:
            st.info(get_text(lang, "no_ds"))
    except Exception as e:
        st.error(str(e))

with tab4:
    st.subheader(get_text(lang, "pods"))
    try:
        pods = client.get_pods(ns)
        if pods:
            st.dataframe(pd.DataFrame(pods), width="stretch", hide_index=True)
            
            st.divider()
            st.subheader(get_text(lang, "log_viewer"))
            
            # Since pod names are unique in a namespace, we can just use the name for the selectbox
            pod_names = [p["Name"] for p in pods if ns != get_text(lang, "all_namespaces") or "Namespace" in p]
            # If all namespaces is selected, it's harder to get logs without knowing the namespace. 
            # We will handle it by combining namespace and name in the selectbox if all namespaces is selected.
            if ns == get_text(lang, "all_namespaces") or ns == "All Namespaces":
                log_options = [f"{p['Namespace']}/{p['Name']}" for p in pods]
            else:
                log_options = pod_names

            if log_options:
                selected_pod = st.selectbox(get_text(lang, "select_pod_logs"), log_options)
                lines = st.slider(get_text(lang, "lines"), 10, 500, 100)
                
                if st.button(get_text(lang, "fetch_logs"), type="primary"):
                    with st.spinner("Buscando logs..."):
                        if ns == "All Namespaces":
                            p_ns, p_name = selected_pod.split("/", 1)
                            logs = client.get_pod_logs(name=p_name, namespace=p_ns, lines=lines)
                        else:
                            logs = client.get_pod_logs(name=selected_pod, namespace=ns, lines=lines)
                        
                        st.code(logs, language="bash")
        else:
            st.info(get_text(lang, "no_pods"))
    except Exception as e:
        st.error(str(e))

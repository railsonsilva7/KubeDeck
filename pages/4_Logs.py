import streamlit as st
import os
from utils import get_asset_path

logo_path = get_asset_path("logo-KubeDeck.svg")
logo_exists = os.path.exists(logo_path)
st.set_page_config(page_title="KubeDeck", page_icon=logo_path if logo_exists else "🚢", layout="wide")
import time

from i18n import get_text

lang = st.session_state.get("lang", "pt")

if "is_connected" not in st.session_state or not st.session_state.is_connected:
    st.warning(get_text(lang, "pls_connect"))
    st.stop()

st.title(get_text(lang, "logs_title"))
st.markdown(get_text(lang, "logs_subtitle"))

ns = st.session_state.selected_namespace
client = st.session_state.k8s_client

st.markdown(f"{get_text(lang, 'selected_ns')} {ns}")

try:
    pods = client.get_pods(ns)
    if pods:
        all_ns_label = get_text(lang, "all_namespaces")
        if ns == all_ns_label or ns == "All Namespaces":
            log_options = [f"{p['Namespace']}/{p['Name']}" for p in pods]
        else:
            log_options = [p['Name'] for p in pods]
            
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            selected_pod = st.selectbox(get_text(lang, "select_pod_stream"), log_options)
        with col2:
            lines = st.number_input(get_text(lang, "tail_lines"), min_value=10, max_value=5000, value=100, step=50)
            
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            # We use a checkbox as a state holder for the streaming toggle
            is_streaming = st.checkbox(get_text(lang, "start_stream"))

        if is_streaming:
            st.success(get_text(lang, "streaming_now").format(selected_pod))
            
            # Placeholder for the terminal
            log_container = st.empty()
            
            logs_list = []
            MAX_LINES = 1000 # Prevent memory explosion in browser
            
            if ns == all_ns_label or ns == "All Namespaces":
                p_ns, p_name = selected_pod.split("/", 1)
            else:
                p_ns, p_name = ns, selected_pod
                
            try:
                # Iterate over the live stream generator
                for line in client.stream_pod_logs(name=p_name, namespace=p_ns, lines=lines):
                    logs_list.append(line.strip())
                    
                    if len(logs_list) > MAX_LINES:
                        logs_list.pop(0)
                        
                    # Update the UI dynamically
                    log_container.code("\n".join(logs_list), language="bash")
            except Exception as stream_err:
                st.error(f"Conexão do stream encerrada: {str(stream_err)}")
        else:
            st.info(get_text(lang, "stream_check_hint"))

    else:
        st.info(get_text(lang, "no_pods_logs").format(ns))
except Exception as e:
    st.error(f"Erro ao carregar os pods: {str(e)}")

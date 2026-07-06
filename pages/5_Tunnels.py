import streamlit as st
import os
from utils import get_asset_path

logo_path = get_asset_path("logo-KubeDeck.svg")
logo_exists = os.path.exists(logo_path)
st.set_page_config(page_title="KubeDeck", page_icon=logo_path if logo_exists else "🚢", layout="wide")
import pandas as pd
import socket

def get_free_port(starting_port):
    for port in range(starting_port, 65535):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return starting_port

from i18n import get_text

lang = st.session_state.get("lang", "pt")

if "is_connected" not in st.session_state or not st.session_state.is_connected:
    st.warning(get_text(lang, "pls_connect"))
    st.stop()

st.title(get_text(lang, "tunnel_title"))
st.markdown(get_text(lang, "tunnel_subtitle"))

ns = st.session_state.selected_namespace
client = st.session_state.k8s_client

st.subheader(get_text(lang, "create_tunnel"))

col1, col2 = st.columns(2)
with col1:
    res_type = st.selectbox(get_text(lang, "res_type"), ["service", "pod"])
    
    options = []
    if res_type == "service":
        svcs = client.get_services(ns)
        options = [s["Name"] for s in svcs if s.get("HasSelector", False)]
        if not options:
            st.warning(get_text(lang, "no_svc_pods"))
    else:
        pods = client.get_pods(ns)
        all_ns_label = get_text(lang, "all_namespaces")
        options = [p["Name"] for p in pods if ns != all_ns_label and ns != "All Namespaces" or "Namespace" in p]
        
    res_name = st.selectbox(get_text(lang, "res_name"), options)

with col2:
    if res_name:
        available_ports = client.get_resource_ports(res_type, res_name, ns)
        if len(available_ports) == 1:
            target_port = available_ports[0]
            st.info(get_text(lang, "detected_port").format(target_port))
        else:
            target_port = st.selectbox(get_text(lang, "select_target_port"), available_ports)
            
        # Smart port mapping (evita portas privilegiadas no SO local)
        base_port = target_port
        if target_port == 80: base_port = 8080
        elif target_port == 443: base_port = 8443
        elif target_port < 1024: base_port = target_port + 8000
        
        local_port = get_free_port(base_port)
        
        st.markdown(get_text(lang, "local_port_hint").format(local_port))
    else:
        target_port = 80
        local_port = 8080

if st.button(get_text(lang, "btn_connect_tunnel"), type="primary", disabled=not res_name):
    target_resource = f"{res_type}/{res_name}"
    
    # Valida se já existe um túnel aberto para este MESMO recurso no MESMO namespace
    is_duplicate = any(
        data["resource"] == target_resource and data["namespace"] == ns 
        for data in st.session_state.active_tunnels.values()
    )
    
    if is_duplicate:
        st.warning(get_text(lang, "tunnel_already_active"))
    else:
        tunnel_id = f"{target_resource}:{local_port}->{target_port}"
        with st.spinner("Iniciando túnel..."):
            success, result = client.start_tunnel(res_type, res_name, ns, local_port, target_port)
            if success:
                st.session_state.active_tunnels[tunnel_id] = {
                    "process": result,
                    "local_port": local_port,
                    "target_port": target_port,
                    "resource": f"{res_type}/{res_name}",
                    "namespace": ns
                }
                st.success(get_text(lang, "tunnel_success").format(local_port))
                st.rerun()
            else:
                st.error(result)

st.divider()

st.subheader(get_text(lang, "active_tunnels"))

if st.session_state.active_tunnels:
    for t_id, data in list(st.session_state.active_tunnels.items()):
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.markdown(f"**{data['resource']}** (Namespace: {data['namespace']})")
        c2.code(f"localhost:{data['local_port']} -> {data['target_port']}")
        
        if c3.button(get_text(lang, "btn_disconnect_tunnel"), key=f"stop_{t_id}", type="secondary"):
            client.stop_tunnel(data["process"])
            del st.session_state.active_tunnels[t_id]
            st.rerun()
else:
    st.info(get_text(lang, "no_active_tunnels"))

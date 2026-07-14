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

def render_actions(res_type, items, ns, client, lang):
    if not items: return
    all_ns_label = get_text(lang, "all_namespaces")
    options = [f"{p['Namespace']}/{p['Name']}" if (ns == all_ns_label or ns == "All Namespaces") and "Namespace" in p else p['Name'] for p in items]
    
    st.divider()
    st.markdown(f"### {get_text(lang, 'actions')}")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        selected_res = st.selectbox(get_text(lang, "res_name"), options, key=f"sel_{res_type}", index=None)
    with col2:
        if selected_res:
            action_options = [get_text(lang, "btn_describe"), get_text(lang, "btn_delete")]
            if res_type in ["deployment", "statefulset"]:
                action_options.append(get_text(lang, "btn_scale"))
            if res_type == "pod":
                action_options.append(get_text(lang, "btn_exec"))
            selected_action = st.selectbox(get_text(lang, "actions"), action_options, key=f"act_{res_type}", index=None)
            
    if selected_res and selected_action:
        target_ns = ns
        target_name = selected_res
        if ns == all_ns_label or ns == "All Namespaces":
            if "/" in selected_res:
                target_ns, target_name = selected_res.split("/", 1)
            
        if selected_action == get_text(lang, "btn_describe"):
            st.subheader(get_text(lang, "describe_title").format(res_type, target_name))
            out = client.describe_resource(res_type, target_name, target_ns)
            st.code(out, language="yaml")
            
        elif selected_action == get_text(lang, "btn_delete"):
            st.warning(get_text(lang, "delete_confirm").format(res_type, target_name))
            if st.button("Confirm", type="primary", key=f"del_{res_type}"):
                success, msg = client.delete_resource(res_type, target_name, target_ns)
                if success:
                    st.success(get_text(lang, "delete_success").format(target_name))
                else:
                    st.error(msg)
                    
        elif selected_action == get_text(lang, "btn_scale"):
            st.subheader(get_text(lang, "scale_title").format(res_type, target_name))
            replicas = st.number_input(get_text(lang, "replicas"), min_value=0, value=1, key=f"rep_{res_type}")
            if st.button(get_text(lang, "btn_apply_scale"), key=f"apply_{res_type}"):
                success, msg = client.scale_resource(res_type, target_name, replicas, target_ns)
                if success:
                    st.success(get_text(lang, "scale_success").format(target_name, replicas))
                else:
                    st.error(msg)
                    
        elif selected_action == get_text(lang, "btn_exec"):
            st.subheader(get_text(lang, "exec_title").format(res_type, target_name))
            cmd = st.text_input(get_text(lang, "command"), value="ls -la", key=f"cmd_{res_type}")
            if st.button(get_text(lang, "btn_run"), key=f"run_{res_type}"):
                with st.spinner("..."):
                    success, msg = client.exec_command(target_name, cmd, target_ns)
                    if success:
                        st.success(get_text(lang, "exec_output"))
                        st.code(msg, language="bash")
                    else:
                        st.error(msg)


with tab1:
    st.subheader(get_text(lang, "deployments"))
    try:
        deps = client.get_deployments(ns)
        if deps:
            st.dataframe(pd.DataFrame(deps), width="stretch", hide_index=True)
            render_actions("deployment", deps, ns, client, lang)
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
            render_actions("statefulset", sts, ns, client, lang)
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
            render_actions("daemonset", dss, ns, client, lang)
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
            render_actions("pod", pods, ns, client, lang)
            
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
                        if ns == "All Namespaces" or ns == get_text(lang, "all_namespaces"):
                            p_ns, p_name = selected_pod.split("/", 1)
                            logs = client.get_pod_logs(name=p_name, namespace=p_ns, lines=lines)
                        else:
                            logs = client.get_pod_logs(name=selected_pod, namespace=ns, lines=lines)
                        
                        st.code(logs, language="bash")
        else:
            st.info(get_text(lang, "no_pods"))
    except Exception as e:
        st.error(str(e))

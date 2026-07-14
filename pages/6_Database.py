import streamlit as st
import os
import subprocess
import tempfile
from utils import get_asset_path
from i18n import get_text

logo_path = get_asset_path("logo-KubeDeck.svg")
logo_exists = os.path.exists(logo_path)
st.set_page_config(page_title="KubeDeck - Database", page_icon=logo_path if logo_exists else "🚢", layout="wide")

lang = st.session_state.get("lang", "pt")

if "is_connected" not in st.session_state or not st.session_state.is_connected:
    st.warning(get_text(lang, "pls_connect"))
    st.stop()

st.title(get_text(lang, "db_title"))
st.markdown(get_text(lang, "db_subtitle"))

ns = st.session_state.selected_namespace
client = st.session_state.k8s_client
st.markdown(f"{get_text(lang, 'showing_ns')} **{ns}**")

# Get list of pods to select from
try:
    pods = client.get_pods(ns)
    all_ns_label = get_text(lang, "all_namespaces")
    pod_options = [f"{p['Namespace']}/{p['Name']}" if ns == all_ns_label or ns == "All Namespaces" else p['Name'] for p in pods]
except Exception as e:
    st.error(str(e))
    st.stop()

selected_pod = st.selectbox(get_text(lang, "select_db_pod"), pod_options, index=None)

col1, col2, col3 = st.columns(3)
with col1:
    db_host = st.text_input("DB Host", value="127.0.0.1")
with col2:
    db_port = st.text_input("DB Port", value="5432")
with col3:
    db_user = st.text_input(get_text(lang, "db_user"), value="postgres")

col4, col5 = st.columns(2)
with col4:
    db_name = st.text_input(get_text(lang, "db_name"), value="postgres")
with col5:
    db_pass = st.text_input(get_text(lang, "db_password"), type="password")

if selected_pod:
    target_ns = ns
    target_pod = selected_pod
    if "/" in selected_pod:
        target_ns, target_pod = selected_pod.split("/", 1)
        
    tab_dump, tab_restore = st.tabs(["Dump", "Restore"])
    
    with tab_dump:
        if st.button(get_text(lang, "btn_dump"), type="primary"):
            if not client.config_path:
                st.error("Kubeconfig not loaded")
            else:
                with st.spinner("Realizando dump... Isso pode demorar."):
                    env_prefix = f"PGPASSWORD={db_pass} " if db_pass else ""
                    # We run this in a shell inside the pod to easily pipe
                    cmd = ["kubectl", "exec", "--kubeconfig", client.config_path, "-n", target_ns, target_pod, "--", "sh", "-c", f"{env_prefix}pg_dump -h {db_host} -p {db_port} -U {db_user} {db_name}"]
                    
                    try:
                        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        out, err = process.communicate()
                        
                        if process.returncode == 0:
                            st.success(get_text(lang, "dump_success"))
                            st.download_button(
                                label=get_text(lang, "download_dump"),
                                data=out,
                                file_name=f"{db_name}_dump.sql",
                                mime="application/sql"
                            )
                        else:
                            st.error(err.decode('utf-8', errors='replace'))
                    except Exception as e:
                        st.error(str(e))
                        
    with tab_restore:
        st.warning(get_text(lang, "restore_warning"))
        uploaded_file = st.file_uploader(get_text(lang, "upload_sql"), type=["sql"])
        
        if uploaded_file and st.button(get_text(lang, "btn_restore"), type="primary"):
            if not client.config_path:
                st.error("Kubeconfig not loaded")
            else:
                with st.spinner("Restaurando banco..."):
                    # Save uploaded file to temp
                    fd, temp_path = tempfile.mkstemp(suffix=".sql")
                    with os.fdopen(fd, 'wb') as f:
                        f.write(uploaded_file.getvalue())
                    
                    env_prefix = f"PGPASSWORD={db_pass} " if db_pass else ""
                    # Use subprocess shell to pipe the file into kubectl exec
                    exec_cmd = f"kubectl exec -i --kubeconfig {client.config_path} -n {target_ns} {target_pod} -- sh -c '{env_prefix}psql -h {db_host} -p {db_port} -U {db_user} {db_name}' < {temp_path}"
                    
                    try:
                        process = subprocess.Popen(exec_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        out, err = process.communicate()
                        
                        os.remove(temp_path)
                        
                        if process.returncode == 0:
                            st.success(get_text(lang, "restore_success"))
                            with st.expander("Ver Saída (Output)"):
                                st.code(out.decode('utf-8', errors='replace'), language="bash")
                        else:
                            st.error(err.decode('utf-8', errors='replace'))
                    except Exception as e:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        st.error(str(e))

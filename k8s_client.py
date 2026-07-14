from kubernetes import client, config
import yaml
import tempfile
import os
import base64
import re
import subprocess
from datetime import datetime

class K8sClient:
    def __init__(self):
        self.config_path = None
        self.core_api = None
        self.apps_api = None
        self.net_api = None
        self.custom_api = None

    def load_config_from_bytes(self, file_bytes):
        fd, temp_path = tempfile.mkstemp(suffix=".yaml")
        with os.fdopen(fd, 'wb') as f:
            f.write(file_bytes)
        
        self.config_path = temp_path
        
        try:
            config.load_kube_config(config_file=self.config_path)
            self.core_api = client.CoreV1Api()
            self.apps_api = client.AppsV1Api()
            self.net_api = client.NetworkingV1Api()
            self.custom_api = client.CustomObjectsApi()
            return True, "Configuração carregada com sucesso."
        except Exception as e:
            return False, f"Erro ao carregar configuração: {str(e)}"

    def get_cluster_info(self):
        if not self.config_path: return None
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            clusters = [c['name'] for c in data.get('clusters', [])]
            contexts = [c['name'] for c in data.get('contexts', [])]
            return {
                "clusters": clusters,
                "contexts": contexts,
                "current_context": data.get('current-context', 'N/A')
            }
        except Exception: return None

    def get_namespaces(self):
        if not self.core_api: return []
        namespaces = self.core_api.list_namespace()
        return [ns.metadata.name for ns in namespaces.items]

    def _parse_cpu(self, cpu_str):
        if not isinstance(cpu_str, str): return 0
        if cpu_str.endswith("n"): return int(cpu_str[:-1]) / 1_000_000
        if cpu_str.endswith("m"): return int(cpu_str[:-1])
        try: return int(cpu_str) * 1000
        except: return 0

    def _parse_mem(self, mem_str):
        if not isinstance(mem_str, str): return 0
        if mem_str.endswith("Ki"): return int(mem_str[:-2]) / 1024
        if mem_str.endswith("Mi"): return int(mem_str[:-2])
        if mem_str.endswith("Gi"): return int(mem_str[:-2]) * 1024
        try: return int(mem_str) / (1024 * 1024)
        except: return 0

    def get_node_metrics(self):
        if not self.custom_api: return {}
        try:
            metrics = self.custom_api.list_cluster_custom_object("metrics.k8s.io", "v1beta1", "nodes")
            res = {}
            for item in metrics.get("items", []):
                cpu = self._parse_cpu(item.get("usage", {}).get("cpu", "0"))
                mem = self._parse_mem(item.get("usage", {}).get("memory", "0"))
                res[item["metadata"]["name"]] = {"cpu": f"{int(cpu)}m", "memory": f"{int(mem)}Mi"}
            return res
        except: return {}

    def get_nodes(self):
        if not self.core_api: return []
        nodes = self.core_api.list_node()
        metrics = self.get_node_metrics()
        return [{
            "Name": node.metadata.name,
            "Status": "Ready" if any(cond.type == "Ready" and cond.status == "True" for cond in node.status.conditions) else "NotReady",
            "CPU Usage": metrics.get(node.metadata.name, {}).get("cpu", "N/A"),
            "Memory Usage": metrics.get(node.metadata.name, {}).get("memory", "N/A"),
            "Version": node.status.node_info.kubelet_version,
            "OS": node.status.node_info.os_image
        } for node in nodes.items]

    # --- Workloads ---
    def get_pod_metrics(self, namespace="default"):
        if not self.custom_api: return {}
        try:
            if namespace == "All Namespaces":
                metrics = self.custom_api.list_cluster_custom_object("metrics.k8s.io", "v1beta1", "pods")
            else:
                metrics = self.custom_api.list_namespaced_custom_object("metrics.k8s.io", "v1beta1", namespace, "pods")
            
            res = {}
            for item in metrics.get("items", []):
                total_cpu = 0
                total_mem = 0
                for c in item.get("containers", []):
                    total_cpu += self._parse_cpu(c.get("usage", {}).get("cpu", "0"))
                    total_mem += self._parse_mem(c.get("usage", {}).get("memory", "0"))
                res[item["metadata"]["name"]] = {"cpu": f"{int(total_cpu)}m", "memory": f"{int(total_mem)}Mi"}
            return res
        except: return {}

    def get_pods(self, namespace="default"):
        if not self.core_api: return []
        if namespace == "All Namespaces":
            pods = self.core_api.list_pod_for_all_namespaces()
        else:
            pods = self.core_api.list_namespaced_pod(namespace)
        
        metrics = self.get_pod_metrics(namespace)
        
        return [{
            "Namespace": pod.metadata.namespace,
            "Name": pod.metadata.name,
            "Status": pod.status.phase,
            "CPU": metrics.get(pod.metadata.name, {}).get("cpu", "N/A"),
            "Memory": metrics.get(pod.metadata.name, {}).get("memory", "N/A"),
            "IP": pod.status.pod_ip or "N/A",
            "Node": pod.spec.node_name or "N/A"
        } for pod in pods.items]

    def get_deployments(self, namespace="default"):
        if not self.apps_api: return []
        if namespace == "All Namespaces":
            deps = self.apps_api.list_deployment_for_all_namespaces()
        else:
            deps = self.apps_api.list_namespaced_deployment(namespace)
        
        return [{
            "Namespace": dep.metadata.namespace,
            "Name": dep.metadata.name,
            "Ready": f"{dep.status.ready_replicas or 0}/{dep.spec.replicas or 0}",
            "Up-to-date": dep.status.updated_replicas or 0,
            "Available": dep.status.available_replicas or 0
        } for dep in deps.items]

    def get_statefulsets(self, namespace="default"):
        if not self.apps_api: return []
        if namespace == "All Namespaces":
            sts = self.apps_api.list_stateful_set_for_all_namespaces()
        else:
            sts = self.apps_api.list_namespaced_stateful_set(namespace)
        return [{
            "Namespace": st.metadata.namespace,
            "Name": st.metadata.name,
            "Ready": f"{st.status.ready_replicas or 0}/{st.spec.replicas or 0}",
            "Up-to-date": st.status.updated_replicas or 0
        } for st in sts.items]

    def get_daemonsets(self, namespace="default"):
        if not self.apps_api: return []
        if namespace == "All Namespaces":
            dss = self.apps_api.list_daemon_set_for_all_namespaces()
        else:
            dss = self.apps_api.list_namespaced_daemon_set(namespace)
        return [{
            "Namespace": ds.metadata.namespace,
            "Name": ds.metadata.name,
            "Desired": ds.status.desired_number_scheduled or 0,
            "Current": ds.status.current_number_scheduled or 0,
            "Ready": ds.status.number_ready or 0
        } for ds in dss.items]

    def _format_log_line(self, line):
        match = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)\s+(.*)$', line)
        if not match: return line
        ts_str, rest = match.groups()
        try:
            if "." in ts_str:
                base, frac_z = ts_str.split(".")
                clean_ts = f"{base}.{frac_z[:-1][:6]}+00:00"
            else:
                clean_ts = ts_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_ts)
            local_dt = dt.astimezone()
            return f"[{local_dt.strftime('%d/%m/%Y %H:%M:%S')}] {rest}"
        except: return line

    def get_pod_logs(self, name, namespace="default", lines=100):
        if not self.core_api: return "API Not connected."
        try:
            logs = self.core_api.read_namespaced_pod_log(name=name, namespace=namespace, tail_lines=lines, timestamps=True)
            formatted_logs = [self._format_log_line(line) for line in logs.splitlines()]
            return "\n".join(formatted_logs)
        except Exception as e:
            return f"Error fetching logs: {str(e)}"

    def stream_pod_logs(self, name, namespace="default", lines=100):
        if not self.core_api: return
        try:
            response = self.core_api.read_namespaced_pod_log(
                name=name, 
                namespace=namespace, 
                tail_lines=lines, 
                follow=True, 
                timestamps=True,
                _preload_content=False
            )
            for line in response.stream(amt=None):
                if line:
                    decoded_line = line.decode('utf-8', errors='replace').strip()
                    yield self._format_log_line(decoded_line)
        except Exception as e:
            yield f"Error streaming logs: {str(e)}"

    # --- Network ---
    def get_services(self, namespace="default"):
        if not self.core_api: return []
        if namespace == "All Namespaces":
            svcs = self.core_api.list_service_for_all_namespaces()
        else:
            svcs = self.core_api.list_namespaced_service(namespace)
            
        return [{
            "Namespace": svc.metadata.namespace,
            "Name": svc.metadata.name,
            "Type": svc.spec.type,
            "ClusterIP": svc.spec.cluster_ip,
            "Ports": ", ".join([f"{p.port}:{p.node_port if p.node_port else '-'}/{p.protocol}" for p in svc.spec.ports]) if svc.spec.ports else "N/A",
            "HasSelector": bool(svc.spec.selector)
        } for svc in svcs.items]

    def get_ingresses(self, namespace="default"):
        if not self.net_api: return []
        if namespace == "All Namespaces":
            ings = self.net_api.list_ingress_for_all_namespaces()
        else:
            ings = self.net_api.list_namespaced_ingress(namespace)
            
        res = []
        for ing in ings.items:
            hosts = []
            if ing.spec.rules:
                hosts = [r.host for r in ing.spec.rules if r.host]
            res.append({
                "Namespace": ing.metadata.namespace,
                "Name": ing.metadata.name,
                "Hosts": ", ".join(hosts) if hosts else "*",
                "Class": ing.spec.ingress_class_name or "N/A"
            })
        return res

    # --- Config ---
    def get_configmaps(self, namespace="default"):
        if not self.core_api: return []
        if namespace == "All Namespaces":
            cms = self.core_api.list_config_map_for_all_namespaces()
        else:
            cms = self.core_api.list_namespaced_config_map(namespace)
            
        return [{
            "Namespace": cm.metadata.namespace,
            "Name": cm.metadata.name,
            "Data Keys": ", ".join(cm.data.keys()) if cm.data else "None"
        } for cm in cms.items]

    def get_secrets(self, namespace="default"):
        if not self.core_api: return []
        if namespace == "All Namespaces":
            secrets = self.core_api.list_secret_for_all_namespaces()
        else:
            secrets = self.core_api.list_namespaced_secret(namespace)
            
        return [{
            "Namespace": sec.metadata.namespace,
            "Name": sec.metadata.name,
            "Type": sec.type,
            "Data Keys": ", ".join(sec.data.keys()) if sec.data else "None"
        } for sec in secrets.items]

    def get_configmap_details(self, name, namespace="default"):
        if not self.core_api: return {}
        try:
            cm = self.core_api.read_namespaced_config_map(name, namespace)
            if not cm.data: return {}
            return cm.data
        except Exception as e:
            return {"error": str(e)}

    def get_secret_details(self, name, namespace="default"):
        if not self.core_api: return {}
        try:
            sec = self.core_api.read_namespaced_secret(name, namespace)
            if not sec.data: return {}
            # Decode base64 values for secrets
            return {k: base64.b64decode(v).decode('utf-8', errors='replace') for k, v in sec.data.items()}
        except Exception as e:
            return {"error": str(e)}


    def cleanup(self):
        if self.config_path and os.path.exists(self.config_path):
            os.remove(self.config_path)
            self.config_path = None
            self.core_api = None
            self.apps_api = None
            self.net_api = None
            self.custom_api = None

    # --- K9s Core Features ---
    def describe_resource(self, res_type, name, namespace="default"):
        if not self.config_path: return "Kubeconfig not loaded"
        cmd = ["kubectl", "describe", "--kubeconfig", self.config_path, "-n", namespace, res_type, name]
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            out, err = process.communicate(timeout=10)
            return out if process.returncode == 0 else err
        except Exception as e:
            return str(e)

    def delete_resource(self, res_type, name, namespace="default"):
        if not self.config_path: return False, "Kubeconfig not loaded"
        cmd = ["kubectl", "delete", "--kubeconfig", self.config_path, "-n", namespace, res_type, name]
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            out, err = process.communicate(timeout=10)
            if process.returncode != 0:
                return False, err
            return True, out
        except Exception as e:
            return False, str(e)
            
    def scale_resource(self, res_type, name, replicas, namespace="default"):
        if not self.apps_api: return False, "API Not connected."
        try:
            body = {"spec": {"replicas": replicas}}
            if res_type.lower() == "deployment":
                self.apps_api.patch_namespaced_deployment_scale(name, namespace, body)
            elif res_type.lower() == "statefulset":
                self.apps_api.patch_namespaced_stateful_set_scale(name, namespace, body)
            else:
                return False, "Unsupported resource type for scaling."
            return True, f"Scaled {name} to {replicas}"
        except Exception as e:
            return False, str(e)
            
    def exec_command(self, pod_name, command, namespace="default"):
        if not self.config_path: return False, "Kubeconfig not loaded"
        import shlex
        args = shlex.split(command)
        cmd = ["kubectl", "exec", "--kubeconfig", self.config_path, "-n", namespace, pod_name, "--"] + args
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            out, err = process.communicate(timeout=30)
            if process.returncode != 0:
                return False, err or out
            return True, out
        except Exception as e:
            return False, str(e)

    # --- Tunnels ---
    def get_resource_ports(self, res_type, name, namespace="default"):
        if not self.core_api: return [8080]
        ports = []
        try:
            if res_type == "service":
                svc = self.core_api.read_namespaced_service(name, namespace)
                if svc.spec.ports:
                    for p in svc.spec.ports:
                        ports.append(p.port)
            elif res_type == "pod":
                pod = self.core_api.read_namespaced_pod(name, namespace)
                for container in pod.spec.containers:
                    if container.ports:
                        for p in container.ports:
                            ports.append(p.container_port)
        except Exception:
            pass
            
        if not ports:
            ports = [80]
            
        return list(set(ports))

    def start_tunnel(self, resource_type, name, namespace, local_port, target_port):
        if not self.config_path:
            return False, "Kubeconfig not loaded"
        
        cmd = [
            "kubectl", "port-forward",
            "--kubeconfig", self.config_path,
            "-n", namespace,
            f"{resource_type}/{name}",
            f"{local_port}:{target_port}"
        ]
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            try:
                out, err = process.communicate(timeout=0.5)
                if process.returncode is not None and process.returncode != 0:
                    return False, f"Erro ao iniciar túnel: {err or out}"
            except subprocess.TimeoutExpired:
                pass
            return True, process
        except Exception as e:
            return False, f"Erro: {str(e)} - Verifique se o kubectl está instalado."

    def stop_tunnel(self, process):
        if process:
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                process.kill()

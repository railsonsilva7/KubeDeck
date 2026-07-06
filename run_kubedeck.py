import os
import sys
import webbrowser
from threading import Timer
import streamlit.web.cli as stcli

# Ensure PyInstaller includes k8s_client
import k8s_client

def open_browser():
    """Abre o navegador padrao no endereco do Streamlit."""
    webbrowser.open_new("http://localhost:8501")

def main():
    # Resolve o caminho do script app.py dependendo se esta congelado (PyInstaller) ou rodando cru
    if getattr(sys, 'frozen', False):
        # Quando compilado, os arquivos estao em sys._MEIPASS
        application_path = sys._MEIPASS
    else:
        # Quando rodando cru, pega a pasta do script
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    app_path = os.path.join(application_path, "app.py")
    
    # Inicia um timer para abrir o browser em 2.5 segundos (tempo para o Streamlit iniciar)
    Timer(2.5, open_browser).start()
    
    # Sobrescreve os argumentos do sistema para enganar o Streamlit
    sys.argv = [
        "streamlit", 
        "run", app_path, 
        "--server.headless", "true",
        "--global.developmentMode", "false"
    ]
    
    # Invoca a inicializacao core do Streamlit
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script wrapper para evitar conflito de importação com streamlit
"""
import sys
import os
import subprocess

# Executa o viewer_app.py com streamlit
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    viewer_app_path = os.path.join(script_dir, "viewer_app.py")
    
    # Se foi chamado diretamente, executa com streamlit run
    cmd = [sys.executable, "-m", "streamlit", "run", viewer_app_path] + sys.argv[1:]
    subprocess.run(cmd)
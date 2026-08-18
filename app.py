import os
import json
import glob
import streamlit as st
from google.cloud import texttospeech

# Configuración flexible de credenciales (Local vs Streamlit Cloud)
if "gcp_service_account" in st.secrets:
    # Si estamos en Streamlit Cloud, usa las credenciales guardadas en Secrets
    creds_dict = dict(st.secrets["gcp_service_account"])
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json.dumps(creds_dict)
else:
    # Si estamos en tu computadora local, busca el archivo .json
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_files = glob.glob(os.path.join(base_dir, "*.json"))
    if json_files:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_files[0]
    else:
        st.error("⚠️ No se encontró la clave de credenciales de Google Cloud.")
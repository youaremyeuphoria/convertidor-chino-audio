import json
import os
import glob
import re
import streamlit as st
from google.cloud import texttospeech
from google.oauth2 import service_account

# ---------------------------------------------------------
# Configuración de la página
# ---------------------------------------------------------
st.set_page_config(
    page_title="Convertidor de Chino a Audio",
    page_icon="🔊",
    layout="centered"
)

st.title("🔊 Texto a Audio en Chino Mandarín")
st.write("Ingresa un texto en caracteres chinos (Hanzi) o Pinyin para generar su audio natural.")

def clean_private_key(key_str: str) -> str:
    """Limpia la clave privada de caracteres extraños y soluciona saltos de línea."""
    if not key_str:
        return key_str
    
    # 1. Reemplazar saltos de línea escapados '\\n' por '\n'
    key_str = key_str.replace("\\n", "\n")
    
    # 2. Reemplazar comillas inteligentes por comillas estándar si las hubiese
    key_str = key_str.replace("“", '"').replace("”", '"').replace("’", "'")
    
    # 3. Asegurar que las cabeceras PEM tengan saltos de línea limpios
    key_str = re.sub(r'-----BEGIN PRIVATE KEY-----\s*', '-----BEGIN PRIVATE KEY-----\n', key_str)
    key_str = re.sub(r'\s*-----END PRIVATE KEY-----', '\n-----END PRIVATE KEY-----\n', key_str)
    
    return key_str.strip()

# ---------------------------------------------------------
# Carga de credenciales
# ---------------------------------------------------------
client = None

# Opción A: Intentar desde GCP_JSON en Secrets
if "GCP_JSON" in st.secrets:
    try:
        raw_data = st.secrets["GCP_JSON"]
        if isinstance(raw_data, str):
            info = json.loads(raw_data)
        else:
            info = dict(raw_data)

        if "private_key" in info:
            info["private_key"] = clean_private_key(info["private_key"])

        creds = service_account.Credentials.from_service_account_info(info)
        client = texttospeech.TextToSpeechClient(credentials=creds)
    except Exception as e:
        st.error(f"Error al procesar GCP_JSON desde Secrets: {e}")

# Opción B: Si no está GCP_JSON, intentar la estructura gcp_service_account estándar
elif "gcp_service_account" in st.secrets and not client:
    try:
        info = dict(st.secrets["gcp_service_account"])
        if "private_key" in info:
            info["private_key"] = clean_private_key(info["private_key"])

        creds = service_account.Credentials.from_service_account_info(info)
        client = texttospeech.TextToSpeechClient(credentials=creds)
    except Exception as e:
        st.error(f"Error al leer gcp_service_account desde Secrets: {e}")

# Opción C: Buscar archivo .json local
if not client:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_files = glob.glob(os.path.join(base_dir, "*.json"))
    if json_files:
        try:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_files[0]
            client = texttospeech.TextToSpeechClient()
        except Exception as e:
            st.error(f"Error al cargar archivo JSON local: {e}")

if not client:
    st.warning("⚠️ No se encontró la clave de credenciales de Google Cloud.")

# ---------------------------------------------------------
# Interfaz de usuario
# ---------------------------------------------------------
texto_input = st.text_area(
    "Texto en chino:",
    placeholder="Escribe o pega aquí, ej: 店员笑着跟客人说话",
    height=120
)

col1, col2 = st.columns(2)

with col1:
    opciones_voces = {
        "cmn-CN-Wavenet-A (Femenina)": "cmn-CN-Wavenet-A",
        "cmn-CN-Wavenet-B (Masculina)": "cmn-CN-Wavenet-B",
        "cmn-CN-Wavenet-C (Masculina)": "cmn-CN-Wavenet-C",
        "cmn-CN-Wavenet-D (Femenina)": "cmn-CN-Wavenet-D",
        "cmn-CN-Standard-A (Femenina)": "cmn-CN-Standard-A",
        "cmn-CN-Standard-B (Masculina)": "cmn-CN-Standard-B"
    }
    voz_seleccionada_label = st.selectbox("Voz", list(opciones_voces.keys()))
    voz_code = opciones_voces[voz_seleccionada_label]

with col2:
    velocidad = st.slider("Velocidad de lectura", min_value=0.5, max_value=1.5, value=0.95, step=0.05)

# ---------------------------------------------------------
# Generación de Audio
# ---------------------------------------------------------
if st.button("✨ Generar Audio", type="primary"):
    if not texto_input.strip():
        st.error("Por favor, ingresa un texto antes de generar el audio.")
    elif not client:
        st.error("No hay credenciales válidas configuradas para conectarse a Google Cloud.")
    else:
        with st.spinner("Generando audio..."):
            try:
                synthesis_input = texttospeech.SynthesisInput(text=texto_input)

                voice = texttospeech.VoiceSelectionParams(
                    language_code="cmn-CN",
                    name=voz_code
                )

                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=velocidad
                )

                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )

                st.success("¡Audio generado con éxito!")
                st.audio(response.audio_content, format="audio/mp3")

                st.download_button(
                    label="📥 Descargar MP3",
                    data=response.audio_content,
                    file_name="audio_chino.mp3",
                    mime="audio/mp3"
                )

            except Exception as e:
                st.error(f"Error al generar el audio: {e}")

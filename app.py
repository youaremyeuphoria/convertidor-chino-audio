import json
import os
import glob
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

# ---------------------------------------------------------
# Carga de credenciales
# ---------------------------------------------------------
client = None

# Opción 1: Intentar cargar desde Secrets de Streamlit Cloud
if "gcp_service_account" in st.secrets:
    try:
        # Convertimos los Secrets a un diccionario de Python
        info = dict(st.secrets["gcp_service_account"])
        
        # Si la clave privada viene como string con \n escapados, los corregimos
        if "private_key" in info and isinstance(info["private_key"], str):
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            
        creds = service_account.Credentials.from_service_account_info(info)
        client = texttospeech.TextToSpeechClient(credentials=creds)
    except Exception as e:
        st.error(f"Error al leer las credenciales desde Secrets: {e}")

# Opción 2: Si no está en Secrets, buscar el archivo .json local (para pruebas locales)
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
    # Voces en Chino Mandarín
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
                # Configurar el texto de entrada
                synthesis_input = texttospeech.SynthesisInput(text=texto_input)

                # Configurar los parámetros de voz
                voice = texttospeech.VoiceSelectionParams(
                    language_code="cmn-CN",
                    name=voz_code
                )

                # Configurar el formato del archivo y velocidad
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=velocidad
                )

                # Llamar a la API de Google Cloud Text-to-Speech
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )

                # Mostrar reproductor de audio
                st.success("¡Audio generado con éxito!")
                st.audio(response.audio_content, format="audio/mp3")

                # Botón para descargar el MP3
                st.download_button(
                    label="📥 Descargar MP3",
                    data=response.audio_content,
                    file_name="audio_chino.mp3",
                    mime="audio/mp3"
                )

            except Exception as e:
                st.error(f"Error al generar el audio: {e}")

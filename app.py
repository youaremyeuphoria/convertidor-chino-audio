import os
import glob
import streamlit as st
from google.cloud import texttospeech
from google.oauth2 import service_account

# Configuración de la página
st.set_page_config(page_title="Convertidor de Chino a Audio", page_icon="🔊")
st.title("🔊 Texto a Audio en Chino Mandarín")
st.write("Ingresa un texto en caracteres chinos (Hanzi) o Pinyin para generar su audio natural.")

# Carga de credenciales
client = None

# Opción A: Intentar cargar desde Secrets de Streamlit Cloud
if "gcp_service_account" in st.secrets:
    try:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        client = texttospeech.TextToSpeechClient(credentials=creds)
    except Exception as e:
        st.error(f"Error al leer las credenciales desde Secrets: {e}")

# Opción B: Si no está en Secrets, buscar el archivo .json local
if not client:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_files = glob.glob(os.path.join(base_dir, "*.json"))
    if json_files:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_files[0]
        client = texttospeech.TextToSpeechClient()
    else:
        st.error("⚠️ No se encontró la clave de credenciales de Google Cloud.")

# Área de texto e interfaz
texto = st.text_area("Texto en chino:", placeholder="Escribe o pega aquí, ej: 店员笑着跟客人说话", height=120)

col1, col2 = st.columns(2)
with col1:
    voz_opcion = st.selectbox("Voz", ["cmn-CN-Wavenet-A (Femenina)", "cmn-CN-Wavenet-B (Masculina)", "cmn-CN-Wavenet-C (Femenina 2)"])
with col2:
    velocidad = st.slider("Velocidad de lectura", min_value=0.5, max_value=1.2, value=0.95, step=0.05)

nombre_voz = voz_opcion.split(" ")[0]

if st.button("✨ Generar Audio", type="primary"):
    if not texto.strip():
        st.warning("Por favor escribe un texto primero.")
    elif not client:
        st.error("No se pudo iniciar el servicio de Google Cloud. Revisa las credenciales.")
    else:
        with st.spinner("Generando audio con Google Cloud..."):
            try:
                synthesis_input = texttospeech.SynthesisInput(text=texto.strip())

                voice = texttospeech.VoiceSelectionParams(
                    language_code="cmn-CN",
                    name=nombre_voz
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
                    label="⬇️ Descargar MP3",
                    data=response.audio_content,
                    file_name="audio_chino.mp3",
                    mime="audio/mp3"
                )

            except Exception as e:
                st.error(f"Error al generar el audio: {e}")

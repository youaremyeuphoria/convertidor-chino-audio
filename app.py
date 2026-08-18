import streamlit as st
from google.cloud import texttospeech
from google.oauth2 import service_account

# Configuración de la página
st.set_page_config(
    page_title="Texto a Audio en Chino Mandarín",
    page_icon="🔊",
    layout="centered"
)

# Título e instrucciones
st.title("🔊 Texto a Audio en Chino Mandarín")
st.write("Ingresa un texto en caracteres chinos (Hanzi) o Pinyin para generar su audio natural.")

# Función para obtener y autenticar el cliente de Google Cloud TTS
@st.cache_resource
def get_tts_client():
    if "gcp_service_account" in st.secrets:
        # Convertir la sección de secrets en un diccionario de Python
        info = dict(st.secrets["gcp_service_account"])
        
        # Corregir saltos de línea en la clave privada si vienen escapados
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            
        credentials = service_account.Credentials.from_service_account_info(info)
        return texttospeech.TextToSpeechClient(credentials=credentials)
    else:
        st.error("⚠️ No se encontró la sección [gcp_service_account] en los Secrets de Streamlit.")
        return None

client = get_tts_client()

# Área de texto de entrada
texto_chino = st.text_area(
    "Texto en chino:",
    placeholder="Escribe o pega aquí, ej: 店员笑着跟客人说话",
    height=120
)

# Opciones de voz y velocidad
col1, col2 = st.columns(2)

with col1:
    opciones_voz = {
        "cmn-CN-Wavenet-A (Femenina)": "cmn-CN-Wavenet-A",
        "cmn-CN-Wavenet-B (Masculina)": "cmn-CN-Wavenet-B",
        "cmn-CN-Wavenet-C (Masculina)": "cmn-CN-Wavenet-C",
        "cmn-CN-Wavenet-D (Femenina)": "cmn-CN-Wavenet-D",
        "cmn-CN-Standard-A (Femenina)": "cmn-CN-Standard-A",
        "cmn-CN-Standard-B (Masculina)": "cmn-CN-Standard-B"
    }
    voz_seleccionada = st.selectbox("Voz", list(opciones_voz.keys()))

with col2:
    velocidad = st.slider("Velocidad de lectura", min_value=0.5, max_value=1.5, value=0.95, step=0.05)

# Botón para generar audio
if st.button("✨ Generar Audio", type="primary"):
    if not texto_chino.strip():
        st.warning("Por favor, ingresa algún texto antes de generar el audio.")
    elif client is None:
        st.error("No se pudo conectar con el servicio de Google Cloud. Revisa la configuración de credenciales.")
    else:
        try:
            with st.spinner("Generando audio..."):
                # Configurar la entrada de texto
                synthesis_input = texttospeech.SynthesisInput(text=texto_chino)

                # Configurar la voz
                voice_code = opciones_voz[voz_seleccionada]
                voice = texttospeech.VoiceSelectionParams(
                    language_code="cmn-CN",
                    name=voice_code
                )

                # Configurar el formato del audio de salida y velocidad
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=velocidad
                )

                # Realizar la petición a la API
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )

                # Reproducir el audio resultante
                st.audio(response.audio_content, format="audio/mp3")
                st.success("¡Audio generado con éxito!")

        except Exception as e:
            st.error(f"Error al solicitar el audio a Google Cloud TTS: {e}")

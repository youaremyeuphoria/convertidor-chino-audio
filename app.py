import streamlit as st
from google.api_core.exceptions import GoogleAPIError
from google.auth.exceptions import GoogleAuthError
from google.cloud import texttospeech
from google.oauth2 import service_account


st.set_page_config(
    page_title="Texto a Audio en Chino Mandarín",
    page_icon="🔊",
    layout="centered",
)

st.title("🔊 Texto a Audio en Chino Mandarín")
st.write(
    "Ingresa un texto en caracteres chinos (Hanzi) o Pinyin "
    "para generar su audio natural."
)


@st.cache_resource
def get_tts_client():
    """Crea y conserva el cliente de Google Cloud Text-to-Speech."""

    if "gcp_service_account" not in st.secrets:
        raise RuntimeError(
            "No se encontró [gcp_service_account] en Streamlit Secrets."
        )

    info = dict(st.secrets["gcp_service_account"])

    campos_requeridos = {
        "type",
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "client_id",
        "auth_uri",
        "token_uri",
        "auth_provider_x509_cert_url",
        "client_x509_cert_url",
    }

    campos_faltantes = campos_requeridos.difference(info)

    if campos_faltantes:
        raise RuntimeError(
            "Faltan campos en Streamlit Secrets: "
            + ", ".join(sorted(campos_faltantes))
        )

    # Convierte secuencias literales "\n" a saltos de línea reales.
    private_key = str(info["private_key"]).replace("\\n", "\n").strip()

    if not private_key.startswith("-----BEGIN PRIVATE KEY-----"):
        raise ValueError(
            "private_key no comienza con "
            "'-----BEGIN PRIVATE KEY-----'."
        )

    if not private_key.endswith("-----END PRIVATE KEY-----"):
        raise ValueError(
            "private_key no termina con "
            "'-----END PRIVATE KEY-----'."
        )

    info["private_key"] = private_key + "\n"

    credentials = service_account.Credentials.from_service_account_info(
        info
    )

    return texttospeech.TextToSpeechClient(
        credentials=credentials
    )


# Intentar crear el cliente sin detener toda la aplicación.
try:
    client = get_tts_client()
    error_credenciales = None
except (RuntimeError, ValueError, GoogleAuthError, Exception) as error:
    client = None
    error_credenciales = str(error)


if error_credenciales:
    st.error(
        "No se pudieron cargar las credenciales de Google Cloud.\n\n"
        f"Detalle: {error_credenciales}"
    )

    st.info(
        "Revisa la sección [gcp_service_account] en los Secrets "
        "de Streamlit y confirma que copiaste los valores directamente "
        "desde una clave JSON nueva."
    )


texto_chino = st.text_area(
    "Texto en chino:",
    placeholder="Escribe o pega aquí, por ejemplo: 店员笑着跟客人说话",
    height=120,
)


opciones_voz = {
    "Wavenet A — Femenina": "cmn-CN-Wavenet-A",
    "Wavenet B — Masculina": "cmn-CN-Wavenet-B",
    "Wavenet C — Masculina": "cmn-CN-Wavenet-C",
    "Wavenet D — Femenina": "cmn-CN-Wavenet-D",
    "Standard A — Femenina": "cmn-CN-Standard-A",
    "Standard B — Masculina": "cmn-CN-Standard-B",
}


columna_voz, columna_velocidad = st.columns(2)

with columna_voz:
    voz_seleccionada = st.selectbox(
        "Voz",
        options=list(opciones_voz),
    )

with columna_velocidad:
    velocidad = st.slider(
        "Velocidad de lectura",
        min_value=0.5,
        max_value=1.5,
        value=0.95,
        step=0.05,
    )


generar_audio = st.button(
    "✨ Generar audio",
    type="primary",
    disabled=client is None,
)


if generar_audio:
    texto_limpio = texto_chino.strip()

    if not texto_limpio:
        st.warning(
            "Por favor, ingresa algún texto antes de generar el audio."
        )
    else:
        try:
            with st.spinner("Generando audio..."):
                synthesis_input = texttospeech.SynthesisInput(
                    text=texto_limpio
                )

                voice = texttospeech.VoiceSelectionParams(
                    language_code="cmn-CN",
                    name=opciones_voz[voz_seleccionada],
                )

                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=velocidad,
                )

                response = client.synthesize_speech(
                    request={
                        "input": synthesis_input,
                        "voice": voice,
                        "audio_config": audio_config,
                    }
                )

            st.audio(
                response.audio_content,
                format="audio/mp3",
            )

            st.download_button(
                label="⬇️ Descargar MP3",
                data=response.audio_content,
                file_name="audio_chino.mp3",
                mime="audio/mpeg",
            )

            st.success("¡Audio generado correctamente!")

        except GoogleAPIError as error:
            st.error(
                "Google Cloud rechazó la solicitud. Comprueba que la API "
                "Text-to-Speech esté habilitada, que la cuenta de servicio "
                "tenga permisos y que el proyecto tenga facturación activa.\n\n"
                f"Detalle: {error}"
            )
        except Exception as error:
            st.error(
                "Ocurrió un error inesperado al generar el audio.\n\n"
                f"Detalle: {error}"
            )

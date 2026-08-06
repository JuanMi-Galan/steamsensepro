"""
Asistente conversacional enfocado en videojuegos (RPG / Steam) para SteamSense.

En vez de usar tool-calling, el contexto del jugador que ya se calculó en la
sesión (perfil, recomendaciones, riesgo de abandono, cluster) se serializa e
inyecta directamente en el system prompt en cada turno, así el asistente
siempre responde con los datos reales y actuales del jugador cargado.
"""
import json
import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT_BASE = """Eres SteamSense AI, un asistente conversacional experto en videojuegos, \
con especialidad en juegos de rol (RPG) y en el ecosistema de Steam.

Tu tono es cercano, entusiasta y directo, como el de un amigo gamer con mucho criterio.
Puedes conversar sobre cualquier tema de videojuegos (mecánicas, historia, comparaciones, \
recomendaciones generales, curiosidades de la industria), pero tu valor diferencial es que \
tienes acceso al perfil real del jugador que está usando la aplicación: sus estadísticas de \
biblioteca, las recomendaciones de compra generadas por el Modelo 1 (precompra), el riesgo de \
abandono de sus juegos actuales generado por el Modelo 2 (postcompra), y su segmento de \
clustering (estilo de juego).

Reglas importantes:
- Si el usuario pregunta algo sobre SU perfil, SUS juegos, SUS recomendaciones o SU riesgo de \
abandono, usa el bloque "CONTEXTO_JUGADOR" de más abajo (si está disponible) como fuente de verdad.
- Si no hay CONTEXTO_JUGADOR cargado todavía, indícale amablemente que puede ingresar su Steam ID \
en la barra lateral y presionar "Cargar mi perfil" para obtener recomendaciones personalizadas.
- No inventes datos numéricos sobre el jugador que no estén en el contexto.
- Responde en español, de forma breve y clara salvo que el usuario pida más detalle.
"""


def build_system_prompt(context: dict | None) -> str:
    if not context:
        return SYSTEM_PROMPT_BASE

    contexto_json = json.dumps(context, ensure_ascii=False, indent=2, default=str)
    return f"{SYSTEM_PROMPT_BASE}\n\nCONTEXTO_JUGADOR (datos reales, actualizados en esta sesión):\n{contexto_json}"


@st.cache_resource(show_spinner=False)
def get_client() -> OpenAI:
    return OpenAI(api_key=OPENAI_API_KEY)


def stream_assistant_answer(conversation: list[dict]) -> str:
    """Llama al modelo con stream=True y pinta la respuesta progresivamente en Streamlit."""
    client = get_client()
    full_response = ""
    placeholder = st.empty()

    stream = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=conversation,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            full_response += delta.content
            placeholder.markdown(full_response)

    return full_response

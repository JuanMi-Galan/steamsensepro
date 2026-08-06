"""
SteamSense — panel al estilo Steam que usa los modelos entrenados en
05_eda_e_ingenieria_variables.ipynb para, a partir de un Steam ID:

1. Modelo 1 (precompra, modelos_1/mejor_modelo1_global.pkl): recomendar juegos
   RPG que el jugador aún no tiene, priorizando los de menor riesgo de abandono.
2. Modelo 2 (postcompra, modelos_2/mejor_modelo2_global.pkl): estimar el riesgo
   de abandono de los juegos RPG que el jugador ya posee.
3. Clustering (modelos_clustering/gmm_v2.pkl + preprocessing_pipeline.pkl):
   identificar el estilo/segmento de jugador.
4. Un asistente conversacional enfocado en videojuegos que conoce el contexto
   del jugador cargado.

Ejecutar con: streamlit run main.py
"""
import numpy as np
import pandas as pd
import streamlit as st

import model_utils
from assistant import build_system_prompt, stream_assistant_answer
from feature_engineering import (
    build_features_cluster,
    build_features_modelo1,
    build_features_modelo2,
    build_games_catalog,
    compute_player_stats,
)
from steam_client import (
    SteamAPIError,
    get_owned_games,
    get_player_summary,
    resolve_steam_id,
    steam_capsule_image,
    steam_header_image,
)

st.set_page_config(
    page_title="SteamSense",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Estilo visual al estilo Steam (tema oscuro, azules y verde "compra")
# ============================================================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #1b2838 0%, #0e141b 100%);
        color: #c7d5e0;
    }
    section[data-testid="stSidebar"] {
        background-color: #171a21;
        border-right: 1px solid #2a3f5a;
    }
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-family: "Motiva Sans", Arial, sans-serif;
    }
    .steamsense-hero {
        background: linear-gradient(90deg, #1b2838 0%, #2a475e 100%);
        border-radius: 6px;
        padding: 18px 24px;
        margin-bottom: 18px;
        border: 1px solid #2a3f5a;
    }
    .steamsense-card {
        background-color: #16202d;
        border: 1px solid #2a3f5a;
        border-radius: 4px;
        padding: 10px;
        margin-bottom: 14px;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .steamsense-card:hover {
        transform: translateY(-2px);
        border-color: #66c0f4;
    }
    .steamsense-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 3px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-top: 4px;
    }
    .badge-green { background-color: #4c6b22; color: #a4d007; }
    .badge-yellow { background-color: #6b5a22; color: #e1c04c; }
    .badge-red { background-color: #6b2222; color: #e1704c; }
    .steamsense-price {
        color: #a4d007;
        font-weight: 700;
    }
    div[data-testid="stMetricValue"] {
        color: #66c0f4;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Datos y modelos en caché (una sola vez por proceso)
# ============================================================
@st.cache_data(show_spinner="Cargando catálogo de juegos RPG...")
def cached_catalog():
    return build_games_catalog("data/u_rpg_juegos_duraciones.csv")


juegos_limpios, catalogo_rpg_full = cached_catalog()


def risk_badge(proba: float) -> tuple[str, str]:
    if proba < 0.34:
        return "Bajo riesgo", "badge-green"
    if proba < 0.67:
        return "Riesgo medio", "badge-yellow"
    return "Alto riesgo", "badge-red"


# ============================================================
# Estado de sesión
# ============================================================
DEFAULTS = {
    "player_loaded": False,
    "load_error": None,
    "steam_id": "",
    "player_summary": None,
    "player_stats": None,
    "owned_games_count": 0,
    "recomendaciones_df": pd.DataFrame(),
    "riesgo_df": pd.DataFrame(),
    "cluster_label": None,
    "cluster_proba": None,
    "assistant_context": None,
    "messages": [
        {"role": "assistant", "content": "¡Hola! Soy SteamSense AI 🎮 ¿En qué te ayudo con tus RPG hoy?"}
    ],
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def cargar_perfil(steam_id_input: str):
    st.session_state.load_error = None
    try:
        steam_id = resolve_steam_id(steam_id_input)
        summary = get_player_summary(steam_id)
        if summary is not None and summary.get("communityvisibilitystate") != 3:
            st.session_state.load_error = (
                "Este perfil de Steam es privado. Pídele al usuario que haga público "
                "'Game details' en steamcommunity.com/my/edit/settings e intenta de nuevo."
            )
            return

        games, meta = get_owned_games(steam_id)
        if meta["private"]:
            st.session_state.load_error = (
                "No se pudo leer la biblioteca de juegos (perfil privado o restringido). "
                "Activa 'Game details' público en la configuración de privacidad de Steam."
            )
            return
        if not games:
            st.session_state.load_error = "Este perfil no tiene juegos registrados en Steam."
            return

        stats, df_rpg_owned = compute_player_stats(games, juegos_limpios, catalogo_rpg_full)

        owned_appids = {str(g["appid"]) for g in games}
        candidatos = juegos_limpios.loc[~juegos_limpios.index.isin(owned_appids)]

        features1 = build_features_modelo1(candidatos, stats)
        proba1 = model_utils.predict_abandono_precompra(features1)
        recomendaciones_df = candidatos.copy()
        recomendaciones_df["proba_abandono"] = proba1
        recomendaciones_df["compatibilidad"] = 1 - proba1
        recomendaciones_df = recomendaciones_df.sort_values("compatibilidad", ascending=False)

        riesgo_df = pd.DataFrame()
        if not df_rpg_owned.empty:
            features2 = build_features_modelo2(df_rpg_owned, stats)
            proba2 = model_utils.predict_abandono_postcompra(features2)
            riesgo_df = df_rpg_owned.reset_index(drop=True).copy()
            riesgo_df["proba_abandono"] = proba2
            riesgo_df = riesgo_df.sort_values("proba_abandono", ascending=False)

        features_cluster = build_features_cluster(stats)
        cluster_label, cluster_proba = model_utils.predict_cluster(features_cluster)

        st.session_state.steam_id = steam_id
        st.session_state.player_summary = summary
        st.session_state.player_stats = stats
        st.session_state.owned_games_count = len(games)
        st.session_state.recomendaciones_df = recomendaciones_df
        st.session_state.riesgo_df = riesgo_df
        st.session_state.cluster_label = cluster_label
        st.session_state.cluster_proba = cluster_proba
        st.session_state.player_loaded = True
        st.session_state.reco_page = 1

        perfil = model_utils.cluster_profile(cluster_label)
        top_recs = recomendaciones_df.head(5)[["nombre", "main_story", "compatibilidad"]]
        top_riesgo = riesgo_df.head(5)[["nombre", "horas_totales", "main_story", "proba_abandono"]] if not riesgo_df.empty else pd.DataFrame()

        st.session_state.assistant_context = {
            "steam_id": steam_id,
            "nombre_perfil": summary.get("personaname") if summary else None,
            "biblioteca": {
                "num_juegos_totales": stats["num_juegos_totales"],
                "horas_totales_todos_juegos": round(stats["horas_totales_todos_juegos"], 1),
                "num_juegos_activos_2_semanas": stats["num_juegos_activos"],
                "num_rpg_jugados": stats["num_rpg_jugados"],
                "pct_juegos_activos": round(stats["pct_juegos_activos"] * 100, 1),
                "promedio_pct_completado_historia_global": round(stats["promedio_pct_completado_historia_global"] * 100, 1),
            },
            "estilo_de_juego": {
                "cluster": perfil["nombre"],
                "descripcion": perfil["descripcion"],
            },
            "top_recomendaciones_compra": [
                {"nombre": r["nombre"], "duracion_historia_h": round(r["main_story"], 1), "compatibilidad_pct": round(r["compatibilidad"] * 100, 1)}
                for _, r in top_recs.iterrows()
            ],
            "top_riesgo_abandono_juegos_actuales": [
                {"nombre": r["nombre"], "horas_jugadas": r["horas_totales"], "duracion_historia_h": round(r["main_story"], 1), "riesgo_abandono_pct": round(r["proba_abandono"] * 100, 1)}
                for _, r in top_riesgo.iterrows()
            ] if not top_riesgo.empty else [],
        }

    except SteamAPIError as exc:
        st.session_state.load_error = str(exc)
    except Exception as exc:  # noqa: BLE001
        st.session_state.load_error = f"Error inesperado al cargar el perfil: {exc}"


TERMINOS_Y_CONDICIONES = """
**SteamSense** es un proyecto educativo/personal, sin fines de lucro, **no afiliado ni
respaldado por Valve Corporation ni por Steam**.

Al usar esta aplicación aceptas que:

- **Autorización** — solo consultarás Steam IDs propios o de personas que te hayan
  autorizado a consultar su información.
- **Alcance de los datos** — la app consulta la Steam Web API pública y solo puede leer lo
  que el perfil consultado tenga configurado como **público** (biblioteca de juegos, horas
  jugadas, resumen de perfil).
- **Uso de los datos** — se usan únicamente dentro de tu sesión actual para generar las
  recomendaciones, el riesgo de abandono y el estilo de juego que ves en pantalla; no se
  almacenan de forma permanente ni se comparten con terceros.
- **Naturaleza de las predicciones** — las recomendaciones y probabilidades de abandono las
  genera un modelo estadístico con fines demostrativos/educativos, puede contener errores y
  **no constituye garantía ni asesoría de compra**.
- **Responsabilidad** — el uso de esta herramienta es bajo tu propia responsabilidad; no nos
  hacemos responsables por el uso indebido de la información consultada ni por decisiones
  tomadas a partir de las predicciones mostradas.

Puedes revisar la [política de privacidad oficial de Steam](https://store.steampowered.com/privacy_agreement/).
"""


@st.dialog("📜 Términos y Condiciones y Política de Privacidad", width="medium")
def dialogo_terminos():
    st.markdown(TERMINOS_Y_CONDICIONES)
    st.divider()
    if st.button("Acepto, continuar", type="primary", use_container_width=True):
        st.session_state.acepta_terminos = True
        st.rerun()


# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.markdown("## 🎮 SteamSense")
    st.caption("Recomendaciones y riesgo de abandono para tu biblioteca RPG")

    if "acepta_terminos" not in st.session_state:
        st.session_state.acepta_terminos = False

    if not st.session_state.acepta_terminos:
        st.info(
            "Antes de ingresar un Steam ID, revisa y acepta nuestros "
            "**Términos y Condiciones y Política de Privacidad**."
        )
        if st.button("📜 Leer y aceptar Términos y Condiciones", use_container_width=True):
            dialogo_terminos()
    else:
        st.caption("✅ Términos y Condiciones aceptados")

        def _cargar_desde_sidebar():
            with st.spinner("Consultando Steam y generando recomendaciones..."):
                cargar_perfil(st.session_state.get("steam_id_field", ""))

        # Sin st.form: dentro de un form, el aviso "Press Enter to submit form"
        # se queda pegado sobre el input y bloquea los clics hasta que el
        # usuario hace clic en otro lado. Con on_change, Enter confirma el
        # valor y el aviso se limpia solo, sin bloquear nada.
        st.text_input(
            "Steam ID",
            placeholder="76561198000000000",
            key="steam_id_field",
            on_change=_cargar_desde_sidebar,
        )
        st.button(
            "Cargar mi perfil",
            type="primary",
            use_container_width=True,
            on_click=_cargar_desde_sidebar,
        )

        st.caption(
            "Encuentra tu Steam ID en tu cuenta de Steam: "
            "[store.steampowered.com/account](https://store.steampowered.com/account/) "
            "(aparece junto a tu nombre de cuenta)."
        )
        st.caption(
            "Para que podamos leer tu biblioteca, en "
            "[steamcommunity.com/my/edit/settings](https://steamcommunity.com/my/edit/settings) "
            "configura como **Público**: *My profile*, *My basic details* y *Game details*."
        )

    if st.session_state.load_error:
        st.error(st.session_state.load_error)

    st.divider()
    seccion = st.radio(
        "Secciones",
        ["Mi Perfil", "Recomendaciones para Comprar", "Riesgo en Mis Juegos", "Mi Estilo de Juego", "Asistente Gamer"],
        index=0,
    )

    if st.session_state.player_loaded:
        summary = st.session_state.player_summary
        st.divider()
        if summary and summary.get("avatarmedium"):
            st.image(summary["avatarmedium"], width=80)
        st.markdown(f"**{summary.get('personaname', 'Jugador')}**" if summary else "**Jugador**")
        st.caption(f"{st.session_state.owned_games_count} juegos en biblioteca")


# ============================================================
# Encabezado
# ============================================================
st.markdown(
    """
    <div class="steamsense-hero">
        <h1>🎮 SteamSense</h1>
        <p>Predicciones de abandono y estilo de juego para tu biblioteca de RPG en Steam.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

necesita_perfil = seccion in ("Mi Perfil", "Recomendaciones para Comprar", "Riesgo en Mis Juegos", "Mi Estilo de Juego")
if necesita_perfil and not st.session_state.player_loaded:
    st.info("👈 Ingresa tu Steam ID en la barra lateral y presiona **Cargar mi perfil** para comenzar.")

# ============================================================
# Sección: Mi Perfil
# ============================================================
if seccion == "Mi Perfil" and st.session_state.player_loaded:
    stats = st.session_state.player_stats
    summary = st.session_state.player_summary

    col_avatar, col_info = st.columns([1, 4])
    with col_avatar:
        if summary and summary.get("avatarfull"):
            st.image(summary["avatarfull"], width=120)
    with col_info:
        st.subheader(summary.get("personaname", "Jugador") if summary else "Jugador")
        if summary and summary.get("profileurl"):
            st.caption(summary["profileurl"])

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Juegos en biblioteca", stats["num_juegos_totales"])
    c2.metric("Horas totales jugadas", f"{stats['horas_totales_todos_juegos']:.0f} h")
    c3.metric("RPG en tu catálogo", stats["num_rpg_jugados"])
    c4.metric("Activos (últimas 2 sem.)", stats["num_juegos_activos"])

    c5, c6 = st.columns(2)
    c5.metric("% juegos activos", f"{stats['pct_juegos_activos'] * 100:.1f}%")
    c6.metric("Avance promedio en historias RPG", f"{stats['promedio_pct_completado_historia_global'] * 100:.0f}%")

    perfil = model_utils.cluster_profile(st.session_state.cluster_label)
    st.divider()
    st.markdown(f"### {perfil['emoji']} Tu estilo de juego: {perfil['nombre']}")
    st.write(perfil["descripcion"])
    st.caption("Ve a la sección **Mi Estilo de Juego** para el detalle completo.")

# ============================================================
# Sección: Recomendaciones para Comprar (Modelo 1 - precompra)
# ============================================================
elif seccion == "Recomendaciones para Comprar" and st.session_state.player_loaded:
    st.subheader("🛒 Recomendaciones para tu próxima compra")
    st.caption(
        "Para cada RPG que aún no tienes, estimamos la probabilidad de que lo abandones si "
        "lo compras — combinando el perfil de tu biblioteca con las características del "
        "juego (duración, popularidad)."
    )

    RECOS_POR_PAGINA = 12

    df = st.session_state.recomendaciones_df
    busqueda = st.text_input("Buscar en el catálogo", placeholder="Nombre del juego...", key="reco_busqueda")
    if busqueda:
        df = df[df["nombre"].str.contains(busqueda, case=False, na=False)]

    # Reiniciar a la página 1 cada vez que cambia la búsqueda
    if st.session_state.get("_reco_busqueda_previa") != busqueda:
        st.session_state.reco_page = 1
        st.session_state._reco_busqueda_previa = busqueda

    total_juegos = len(df)
    total_paginas = max(1, -(-total_juegos // RECOS_POR_PAGINA))  # ceil
    st.session_state.setdefault("reco_page", 1)
    st.session_state.reco_page = min(max(st.session_state.reco_page, 1), total_paginas)

    inicio = (st.session_state.reco_page - 1) * RECOS_POR_PAGINA
    df_top = df.iloc[inicio: inicio + RECOS_POR_PAGINA]

    if df_top.empty:
        st.info("No se encontraron juegos con ese criterio.")
    else:
        cols = st.columns(3)
        for i, (_, row) in enumerate(df_top.iterrows()):
            badge_text, badge_class = risk_badge(row["proba_abandono"])
            with cols[i % 3]:
                st.markdown(
                    f"""
                    <div class="steamsense-card">
                        <img src="{steam_header_image(row['appid'])}" style="width:100%; border-radius:3px;" />
                        <h4>{row['nombre']}</h4>
                        <span class="steamsense-badge {badge_class}">Compatibilidad {row['compatibilidad']*100:.0f}%</span>
                        <p style="margin-top:8px; font-size:0.85rem;">
                        Historia principal: ~{row['main_story']:.0f} h<br/>
                        Riesgo de abandono estimado: {row['proba_abandono']*100:.0f}%
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.divider()
        col_prev, col_mid, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("◀ Anterior", disabled=st.session_state.reco_page <= 1, use_container_width=True):
                st.session_state.reco_page -= 1
                st.rerun()
        with col_mid:
            st.markdown(
                f"<p style='text-align:center; margin-top:8px;'>"
                f"Página {st.session_state.reco_page} de {total_paginas} · {total_juegos} juegos</p>",
                unsafe_allow_html=True,
            )
        with col_next:
            if st.button("Siguiente ▶", disabled=st.session_state.reco_page >= total_paginas, use_container_width=True):
                st.session_state.reco_page += 1
                st.rerun()

# ============================================================
# Sección: Riesgo en Mis Juegos (Modelo 2 - postcompra)
# ============================================================
elif seccion == "Riesgo en Mis Juegos" and st.session_state.player_loaded:
    st.subheader("⚠️ Riesgo de abandono en tus RPG actuales")
    st.caption(
        "Usando tus horas jugadas reales en cada RPG que ya tienes, estimamos qué tan "
        "probable es que lo dejes sin terminar."
    )

    riesgo_df = st.session_state.riesgo_df
    if riesgo_df.empty:
        st.info("Aún no identificamos juegos RPG de nuestro catálogo en tu biblioteca.")
    else:
        for _, row in riesgo_df.iterrows():
            badge_text, badge_class = risk_badge(row["proba_abandono"])
            col_img, col_body = st.columns([1, 4])
            with col_img:
                st.image(steam_capsule_image(row["appid"]))
            with col_body:
                st.markdown(f"**{row['nombre']}**  <span class='steamsense-badge {badge_class}'>{badge_text}</span>", unsafe_allow_html=True)
                avance = min(row["horas_totales"] / row["main_story"], 1.0) if row["main_story"] else 0
                st.progress(avance, text=f"{row['horas_totales']:.0f} h jugadas de ~{row['main_story']:.0f} h de historia principal")
                st.caption(f"Probabilidad de abandono: {row['proba_abandono']*100:.0f}%")
            st.divider()

# ============================================================
# Sección: Mi Estilo de Juego (Clustering)
# ============================================================
elif seccion == "Mi Estilo de Juego" and st.session_state.player_loaded:
    st.subheader("🧭 Tu estilo de juego")

    etiqueta = st.session_state.cluster_label
    proba = st.session_state.cluster_proba
    perfil = model_utils.cluster_profile(etiqueta)

    st.markdown(f"## {perfil['emoji']} {perfil['nombre']}")
    st.write(perfil["descripcion"])

    st.divider()
    st.markdown("#### Afinidad con cada perfil de jugador")
    for cluster_id, probabilidad in enumerate(proba):
        info = model_utils.cluster_profile(cluster_id)
        st.write(f"{info['emoji']} **{info['nombre']}**")
        st.progress(float(probabilidad), text=f"{probabilidad*100:.1f}%")

# ============================================================
# Sección: Asistente Gamer
# ============================================================
elif seccion == "Asistente Gamer":
    st.subheader("💬 Asistente Gamer")
    st.caption("Pregúntale sobre RPG, Steam o tu perfil cargado.")

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Escribe tu mensaje..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        conversation = [{"role": "system", "content": build_system_prompt(st.session_state.assistant_context)}]
        conversation.extend({"role": m["role"], "content": m["content"]} for m in st.session_state.messages)

        with st.chat_message("assistant"):
            try:
                response = stream_assistant_answer(conversation)
            except Exception as exc:  # noqa: BLE001
                response = f"No pude conectar con el asistente: {exc}"
                st.error(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

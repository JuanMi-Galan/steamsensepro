"""
Ingeniería de variables para producción.

Este módulo replica -sin modificarlo- el tratamiento de datos hecho en
`05_eda_e_ingenieria_variables.ipynb` para poder generar, en vivo y para un
único steam_id, las mismas columnas que se usaron para entrenar:

- mejor_modelo1_global.pkl (precompra)
- mejor_modelo2_global.pkl (postcompra)
- gmm_v2.pkl + preprocessing_pipeline.pkl (clustering)

Resumen de las reglas replicadas del notebook:
1. Catálogo de juegos RPG (celdas 13-44): limpieza de `u_rpg_juegos_duraciones.csv`,
   emparejando nombre de Steam vs. nombre de HowLongToBeat, corrigiendo
   main_extra < main_story, marcando completionist no confiable, calculando
   `umbral_completado`, `owners_punto_medio`, `log_owners` y `ratio_extra_vs_historia`.
2. Estadísticas de jugador (celdas 67-72): agregados sobre TODA la biblioteca
   del jugador (no solo RPG) -> num_juegos_totales, horas_totales_todos_juegos,
   num_juegos_activos, num_rpg_jugados, pct_juegos_activos, dispersion_de_atencion,
   y promedio_pct_completado_historia_global (este último NUNCA se ajusta por
   leave-one-out, ver celdas 81-83 donde ese ajuste está comentado/deshabilitado).
3. Leave-one-out (celdas 75-80): al construir la fila de un juego puntual para
   Modelo 2 (postcompra), se resta la contribución de ESE juego de los agregados
   del jugador, porque en entrenamiento cada fila representaba un juego
   específico y no debía "verse a sí misma" en sus propias estadísticas.
   Para Modelo 1 (precompra) no aplica: el candidato no está en la biblioteca.
"""
import re
import unicodedata

import numpy as np
import pandas as pd

RANGOS_OWNERS = {
    '0 .. 20,000': 10000,
    '20,000 .. 50,000': 35000,
    '50,000 .. 100,000': 75000,
    '100,000 .. 200,000': 150000,
    '200,000 .. 500,000': 350000,
    '500,000 .. 1,000,000': 750000,
    '1,000,000 .. 2,000,000': 1500000,
    '2,000,000 .. 5,000,000': 3500000,
    '5,000,000 .. 10,000,000': 7500000,
    '10,000,000 .. 20,000,000': 15000000,
    '20,000,000 .. 50,000,000': 35000000,
    '50,000,000 .. 100,000,000': 75000000,
}

FEATURES_MODELO1 = [
    'main_story', 'main_extra', 'ratio_extra_vs_historia', 'log_owners',
    'num_juegos_totales', 'horas_totales_todos_juegos',
    'num_juegos_activos', 'num_rpg_jugados', 'pct_juegos_activos',
    'dispersion_de_atencion', 'promedio_pct_completado_historia_global',
]

FEATURES_MODELO2 = FEATURES_MODELO1 + ['horas_hasta_corte', 'pct_avance_hasta_corte']

FEATURES_CLUSTER = [
    'num_juegos_totales', 'horas_totales_todos_juegos', 'pct_juegos_activos',
    'num_rpg_jugados', 'dispersion_de_atencion', 'promedio_pct_completado_historia_global',
]

# El género "RPG" de SteamSpy incluye bastante shovelware/asset-flips y juegos
# para adultos con main_story casi 0 (imposibles de "abandonar" para el modelo,
# por lo que salían recomendados con compatibilidad ~100%). Se filtran del
# catálogo mostrado en la app -no de catalogo_rpg_full, que se usa tal cual
# para num_rpg_jugados y debe coincidir con la definición usada en entrenamiento.
MIN_MAIN_STORY_HOURS = 2.0

NSFW_KEYWORDS = [
    "hentai", "xxx", "porn", "nsfw", "erotic", "succubus", "ecchi", "lewd",
    "r18", "18+", "adult only", "brothel", "harem simulator", "sex ",
]
NSFW_PATTERN = re.compile("|".join(re.escape(k) for k in NSFW_KEYWORDS), re.IGNORECASE)


def estandarizar_nombre(value):
    if pd.isna(value):
        return ''
    value = str(value).strip()
    value = unicodedata.normalize('NFKD', value)
    value = ''.join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = re.sub(r'["\'""`´''""«»]', '', value)
    value = re.sub(r'\s+', ' ', value)
    return value.strip()


def build_games_catalog(csv_path: str = "data/u_rpg_juegos_duraciones.csv"):
    """
    Reproduce juegos_limpios (celdas 13-44 del notebook), pero conservando la
    columna 'nombre' (el notebook la descarta en la celda 44; aquí se necesita
    para mostrarla en la interfaz).

    Retorna:
    - juegos_limpios: DataFrame indexado por appid (str) con las columnas de
      catálogo necesarias para los modelos.
    - catalogo_rpg_full: set de appids (str) de TODO el género RPG en SteamSpy,
      usado para calcular num_rpg_jugados (celda 68, antes de la limpieza).
    """
    juegos = pd.read_csv(csv_path)
    juegos['appid'] = juegos['appid'].astype(str)

    catalogo_rpg_full = set(juegos['appid'].unique())

    juegos['nombre_estandarizado'] = juegos['nombre'].apply(estandarizar_nombre)
    juegos['hltb_name_estandarizado'] = juegos['hltb_name'].apply(estandarizar_nombre)

    mask = (
        (juegos['nombre_estandarizado'] != '') &
        (juegos['hltb_name_estandarizado'] != '') &
        (juegos['nombre_estandarizado'] == juegos['hltb_name_estandarizado'])
    )
    juegos_limpios = juegos.loc[mask].copy().reset_index(drop=True)
    juegos_limpios = juegos_limpios.drop(columns=['nombre_estandarizado', 'hltb_name_estandarizado'])

    juegos_limpios = juegos_limpios[
        juegos_limpios['main_story'].notna() & (juegos_limpios['main_story'] > 0)
    ].copy().reset_index(drop=True)

    # Filtro de calidad/contenido para lo que se muestra en la app (ver nota arriba)
    juegos_limpios = juegos_limpios[
        (juegos_limpios['main_story'] >= MIN_MAIN_STORY_HOURS) &
        ~juegos_limpios['nombre'].fillna('').str.contains(NSFW_PATTERN)
    ].copy().reset_index(drop=True)

    # Corregir main_extra < main_story
    juegos_limpios['main_extra'] = juegos_limpios[['main_story', 'main_extra']].max(axis=1)

    # Marcar completionist no confiable como NaN
    juegos_limpios.loc[
        (juegos_limpios['completionist'] == 0) | (juegos_limpios['completionist'] < juegos_limpios['main_extra']),
        'completionist'
    ] = np.nan

    juegos_limpios['umbral_completado'] = (
        juegos_limpios['completionist']
        .fillna(juegos_limpios['main_extra'])
        .fillna(juegos_limpios['main_story'])
    )

    juegos_limpios['owners_punto_medio'] = juegos_limpios['owners_estimado'].map(RANGOS_OWNERS).astype(int)
    juegos_limpios['log_owners'] = np.log1p(juegos_limpios['owners_punto_medio'])
    juegos_limpios['ratio_extra_vs_historia'] = juegos_limpios['main_extra'] / juegos_limpios['main_story']

    juegos_limpios = juegos_limpios.drop_duplicates(subset='appid').set_index('appid', drop=False)

    return juegos_limpios, catalogo_rpg_full


def compute_player_stats(owned_games: list[dict], juegos_limpios: pd.DataFrame, catalogo_rpg_full: set):
    """
    Reproduce jugador_stats (celdas 67-72) para UN solo jugador, a partir de
    su biblioteca completa (todos los juegos, no solo RPG).

    Retorna:
    - stats: dict con los agregados "completos" (sin leave-one-out) del jugador
    - df_rpg_owned: DataFrame de los juegos RPG del catálogo que el jugador
      posee, ya unido con las columnas de catálogo (main_story, log_owners, etc.)
      y con 'pct_completado_historia' calculado -> insumo para Modelo 2.
    """
    df = pd.DataFrame(owned_games)
    if df.empty:
        stats = {
            'num_juegos_totales': 0,
            'horas_totales_todos_juegos': 0.0,
            'num_juegos_activos': 0,
            'num_rpg_jugados': 0,
            'pct_juegos_activos': 0.0,
            'dispersion_de_atencion': 0,
            'promedio_pct_completado_historia_global': 0.0,
        }
        return stats, df.assign(appid=pd.Series(dtype=str))

    df['appid'] = df['appid'].astype(str)

    num_juegos_totales = len(df)
    horas_totales_todos_juegos = float(df['horas_totales'].sum())
    num_juegos_activos = int((df['horas_2_semanas'] > 0).sum())
    num_rpg_jugados = int(df['appid'].isin(catalogo_rpg_full).sum())
    pct_juegos_activos = (num_juegos_activos / num_juegos_totales) if num_juegos_totales > 0 else 0.0
    dispersion_de_atencion = num_juegos_activos

    # 'nombre' se descarta del lado del catálogo: ya viene en `df` (el nombre
    # reportado por la propia API de Steam para la biblioteca del jugador), y
    # dejar 'nombre' duplicado hace que el merge lo renombre a nombre_x/nombre_y.
    df_rpg_owned = df.merge(
        juegos_limpios.drop(columns=['appid', 'nombre']), left_on='appid', right_index=True, how='inner'
    )
    df_rpg_owned = df_rpg_owned[df_rpg_owned['main_story'] > 0].copy()
    df_rpg_owned['pct_completado_historia'] = df_rpg_owned['horas_totales'] / df_rpg_owned['main_story']

    promedio_pct = float(df_rpg_owned['pct_completado_historia'].mean()) if len(df_rpg_owned) else 0.0

    stats = {
        'num_juegos_totales': num_juegos_totales,
        'horas_totales_todos_juegos': horas_totales_todos_juegos,
        'num_juegos_activos': num_juegos_activos,
        'num_rpg_jugados': num_rpg_jugados,
        'pct_juegos_activos': pct_juegos_activos,
        'dispersion_de_atencion': dispersion_de_atencion,
        'promedio_pct_completado_historia_global': promedio_pct,
    }
    return stats, df_rpg_owned


def build_features_modelo1(candidatos: pd.DataFrame, stats: dict) -> pd.DataFrame:
    """
    Features para juegos que el jugador AÚN NO posee (precompra).
    `candidatos` es un subconjunto de juegos_limpios (una fila por juego candidato).
    Los agregados del jugador se usan tal cual (el candidato no está en su biblioteca).
    """
    out = candidatos.copy()
    for col, val in stats.items():
        if col == 'num_juegos_totales':
            out[col] = val
        else:
            out[col] = val
    return out[FEATURES_MODELO1]


def build_features_modelo2(df_rpg_owned: pd.DataFrame, stats: dict) -> pd.DataFrame:
    """
    Features para juegos RPG que el jugador YA posee (postcompra), aplicando
    leave-one-out fila por fila tal como en las celdas 75-80 del notebook:
    se resta la contribución del propio juego de los agregados del jugador
    antes de usarlos como feature, para no filtrar información de la propia
    fila objetivo. `promedio_pct_completado_historia_global` NO se ajusta
    (ese ajuste está deshabilitado en el notebook original).
    """
    if df_rpg_owned.empty:
        return df_rpg_owned.reindex(columns=FEATURES_MODELO2)

    out = df_rpg_owned.copy()

    out['num_juegos_totales'] = stats['num_juegos_totales'] - 1
    out['horas_totales_todos_juegos'] = stats['horas_totales_todos_juegos'] - out['horas_totales']
    activo_este_juego = (out['horas_2_semanas'] > 0).astype(int)
    out['num_juegos_activos'] = stats['num_juegos_activos'] - activo_este_juego
    out['num_rpg_jugados'] = stats['num_rpg_jugados'] - 1
    out['pct_juegos_activos'] = np.where(
        out['num_juegos_totales'] > 0,
        out['num_juegos_activos'] / out['num_juegos_totales'],
        0.0,
    )
    out['dispersion_de_atencion'] = out['num_juegos_activos']
    out['promedio_pct_completado_historia_global'] = stats['promedio_pct_completado_historia_global']

    out['horas_hasta_corte'] = out['horas_totales'] - out['horas_2_semanas']
    out['pct_avance_hasta_corte'] = out['horas_hasta_corte'] / out['main_story']

    return out[FEATURES_MODELO2]


def build_features_cluster(stats: dict) -> pd.DataFrame:
    """
    Features de perfil de jugador para el pipeline de clustering (celda 130):
    se aplica log1p a horas_totales_todos_juegos ANTES del PowerTransformer/PCA
    guardado en preprocessing_pipeline.pkl (ese log1p no forma parte del pickle).
    """
    row = dict(stats)
    row['horas_totales_todos_juegos'] = np.log1p(row['horas_totales_todos_juegos'])
    return pd.DataFrame([row])[FEATURES_CLUSTER]

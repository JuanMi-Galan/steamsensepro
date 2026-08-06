"""
Carga de modelos entrenados en 05_eda_e_ingenieria_variables.ipynb y wrappers
de predicción. Los modelos son Pipelines de sklearn (ColumnTransformer ->
VarianceThreshold -> SelectKBest -> LGBMClassifier/etc.), por lo que basta con
pasarles un DataFrame con las columnas de entrenamiento en cualquier orden.

Los modelos se descargan automáticamente desde Google Drive si no existen localmente.
"""
from pathlib import Path
import pickle

import numpy as np
import pandas as pd
import streamlit as st

from feature_engineering import FEATURES_MODELO1, FEATURES_MODELO2, FEATURES_CLUSTER
from download_models import ensure_models_downloaded

# Asegurar que los modelos estén disponibles antes de cualquier operación
ensure_models_downloaded()

BASE_DIR = Path(__file__).resolve().parent

MODEL1_PATH = BASE_DIR / "modelos_1" / "mejor_modelo1_global.pkl"
MODEL2_PATH = BASE_DIR / "modelos_2" / "mejor_modelo2_global.pkl"
CLUSTER_PIPE_PATH = BASE_DIR / "modelos_clustering" / "preprocessing_pipeline.pkl"
CLUSTER_MODEL_PATH = BASE_DIR / "modelos_clustering" / "gmm_v2.pkl"

# Perfiles descriptivos calculados a partir de las medias reales de cada
# cluster obtenidas en el notebook (celda "df_cluster.groupby('Grupos GMM v2').mean()")
CLUSTER_PROFILES = {
    0: {
        "nombre": "Jugador Dedicado",
        "emoji": "🎯",
        "descripcion": (
            "Biblioteca moderada, pero con altísimo nivel de compromiso: juega "
            "en profundidad sus RPG, superando varias veces la duración de la "
            "historia principal, y mantiene algo de actividad reciente."
        ),
    },
    1: {
        "nombre": "Coleccionista Dormido",
        "emoji": "💤",
        "descripcion": (
            "Biblioteca grande construida con el tiempo, pero sin actividad "
            "reciente: prácticamente no tiene juegos activos en las últimas "
            "2 semanas."
        ),
    },
    2: {
        "nombre": "Coleccionista Masivo",
        "emoji": "📚",
        "descripcion": (
            "Biblioteca enorme. Acumula muchas horas en total, pero "
            "repartidas entre tantos juegos que la actividad por título "
            "individual es baja."
        ),
    },
}


@st.cache_resource(show_spinner=False)
def load_pickle(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)


def get_model1():
    return load_pickle(str(MODEL1_PATH))


def get_model2():
    return load_pickle(str(MODEL2_PATH))


def get_cluster_pipeline():
    return load_pickle(str(CLUSTER_PIPE_PATH))


def get_cluster_model():
    return load_pickle(str(CLUSTER_MODEL_PATH))


def predict_abandono_precompra(features_df: pd.DataFrame) -> np.ndarray:
    """Probabilidad de abandono (clase 1) si el jugador compra cada juego candidato."""
    if features_df.empty:
        return np.array([])
    model = get_model1()
    return model.predict_proba(features_df[FEATURES_MODELO1])[:, 1]


def predict_abandono_postcompra(features_df: pd.DataFrame) -> np.ndarray:
    """Probabilidad de abandono (clase 1) para juegos ya comprados por el jugador."""
    if features_df.empty:
        return np.array([])
    model = get_model2()
    return model.predict_proba(features_df[FEATURES_MODELO2])[:, 1]


def predict_cluster(features_df: pd.DataFrame):
    """Retorna (etiqueta_cluster:int, probabilidades:np.ndarray) para el perfil del jugador."""
    pipe = get_cluster_pipeline()
    gmm = get_cluster_model()

    transformado = pipe.transform(features_df[FEATURES_CLUSTER])
    n_components = gmm.means_.shape[0]
    pca_cols = [f"pca{i}" for i in range(n_components)]
    componentes = pd.DataFrame(transformado[:, :n_components], columns=pca_cols)

    etiqueta = int(gmm.predict(componentes)[0])
    probabilidades = gmm.predict_proba(componentes)[0]
    return etiqueta, probabilidades


def cluster_profile(etiqueta: int) -> dict:
    return CLUSTER_PROFILES.get(etiqueta, {
        "nombre": f"Cluster {etiqueta}",
        "emoji": "🎮",
        "descripcion": "Perfil de jugador sin descripción disponible.",
    })

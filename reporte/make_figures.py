import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import re

plt.rcParams.update({
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})

PALETTE = {
    "primary": "#1b6ca8",
    "secondary": "#e2711d",
    "grey": "#8a8f98",
    "accent": "#2f9e44",
    "muted": "#c9c9c9",
}

OUT = "."

# -----------------------------------------------------------------
# Figura 1: distribucion de horas de historia principal (main_story)
# -----------------------------------------------------------------
df = pd.read_csv("../data/u_rpg_juegos_duraciones.csv")
serie = df["main_story"].dropna()
serie = serie[serie > 0]

fig, ax = plt.subplots(figsize=(6, 3.6))
ax.hist(serie, bins=60, range=(0, 100), color=PALETTE["primary"], alpha=0.85, edgecolor="white", linewidth=0.3)
ax.axvline(serie.median(), color=PALETTE["secondary"], linestyle="--", linewidth=1.4,
           label=f"Mediana = {serie.median():.1f} h")
ax.set_xlabel("Horas de historia principal (main_story)")
ax.set_ylabel("Número de juegos")
ax.set_title("Distribución de duración de historia principal en catálogo RPG\n(n={:,} juegos con main_story > 0 en HowLongToBeat)".format(len(serie)), fontsize=10)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(f"{OUT}/fig_main_story_dist.png")
plt.close(fig)

# -----------------------------------------------------------------
# Figura 2: comparacion de average precision (CV) por tipo de modelo
# -----------------------------------------------------------------
def best_by_model(path):
    d = pd.read_csv(path)
    d = d[["scaler", "model", "best_score"]].copy()
    return d.groupby("model")["best_score"].max().sort_values(ascending=False)

m1 = best_by_model("../data/gridsearch_results_modelo_1.csv")
m2 = best_by_model("../data/gridsearch_results_modelo_2.csv")

order = ["LGBMClassifier", "XGBClassifier", "KNeighborsClassifier", "LogisticRegression", "LDA"]
m1 = m1.reindex(order)
m2 = m2.reindex(order)

labels = ["LightGBM", "XGBoost", "KNN", "Reg. Log.", "LDA"]
x = np.arange(len(labels))
width = 0.36

fig, ax = plt.subplots(figsize=(6.4, 3.8))
b1 = ax.bar(x - width/2, m1.values, width, label="Modelo 1 (precompra)", color=PALETTE["primary"])
b2 = ax.bar(x + width/2, m2.values, width, label="Modelo 2 (postcompra)", color=PALETTE["secondary"])
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel("Average Precision (CV, k=4)")
ax.set_ylim(0.85, 1.005)
ax.set_title("Mejor Average Precision por familia de modelo (GridSearchCV)")
ax.legend(frameon=False, loc="lower right")
for bars in (b1, b2):
    for rect in bars:
        h = rect.get_height()
        if not np.isnan(h):
            ax.annotate(f"{h:.3f}", (rect.get_x() + rect.get_width()/2, h),
                        xytext=(0, 3), textcoords="offset points", ha="center", fontsize=7.5)
fig.tight_layout()
fig.savefig(f"{OUT}/fig_gridsearch_comparacion.png")
plt.close(fig)

# -----------------------------------------------------------------
# Figura 3: perfiles de cluster (medias por variable, normalizadas 0-1
# para permitir comparacion visual en una misma escala)
# -----------------------------------------------------------------
data = {
    "num_juegos_totales":          [184.27, 314.86, 754.55],
    "horas_totales (log1p)":       [8.27, 4.83, 8.78],
    "pct_juegos_activos":          [0.06, 0.00, 0.01],
    "num_rpg_jugados":             [33.52, 58.54, 145.42],
    "dispersion_de_atencion":      [6.04, 0.00, 3.16],
    "pct_completado_promedio":     [5.01, 2.10, 1.84],
}
clusters = ["Dedicado", "Coleccionista\nDormido", "Coleccionista\nMasivo"]
colors = [PALETTE["accent"], PALETTE["grey"], PALETTE["secondary"]]

variables = list(data.keys())
mat = np.array([data[v] for v in variables])  # shape (vars, clusters)
mat_norm = mat / mat.max(axis=1, keepdims=True)

fig, ax = plt.subplots(figsize=(7, 4))
y = np.arange(len(variables))
h = 0.25
for i, (c, col) in enumerate(zip(clusters, colors)):
    ax.barh(y + (i-1)*h, mat_norm[:, i], height=h, color=col, label=c)
ax.set_yticks(y)
ax.set_yticklabels(variables)
ax.set_xlabel("Valor relativo al máximo entre clusters (0–1)")
ax.set_title("Perfiles de jugador identificados por el modelo GMM\n(medias por variable, escala normalizada)")
ax.legend(frameon=False, loc="lower right", fontsize=8)
ax.invert_yaxis()
fig.tight_layout()
fig.savefig(f"{OUT}/fig_cluster_perfiles.png")
plt.close(fig)

print("OK: figuras generadas")

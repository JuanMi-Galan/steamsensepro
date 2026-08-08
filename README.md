# SteamSense Pro 🎮

Panel interactivo al estilo Steam que utiliza Machine Learning para recomendar juegos RPG, predecir riesgo de abandono y clasificar perfiles de jugadores.

## 🚀 Características

- **Recomendaciones de Juegos**: Modelo de precompra que sugiere RPGs con menor riesgo de abandono
- **Análisis de Riesgo**: Modelo de postcompra que evalúa tus juegos actuales
- **Perfil de Jugador**: Clustering que identifica tu estilo de juego
- **Asistente IA**: Chatbot conversacional que conoce tu contexto de Steam

## 📋 Requisitos

- Python 3.9+
- Steam API Key ([obtén una aquí](https://steamcommunity.com/dev/apikey))
- OpenAI API Key (para el asistente conversacional)
- Cuenta de Google Drive (para almacenar modelos)
- Data para no ejecutar API: [descarga data](https://drive.google.com/drive/folders/1aGecoOPu6_xZ3pWk1_MeJ7YduDjcNnan?usp=sharing)

## 🛠️ Instalación Local

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/JuanMi-Galan/steamsensepro.git
   cd steamsensepro
   ```

2. **Instalar dependencias con uv** (recomendado)
   ```bash
   uv sync
   ```
   
   O con pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar modelos en Google Drive**
   
   Los modelos son demasiado grandes para GitHub, así que debes subirlos a Google Drive:
   
   ```bash
   python setup_gdrive.py
   ```
   
   Este script te guiará paso a paso. Alternativamente, consulta [GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md) para instrucciones detalladas.

4. **Configurar variables de entorno**
   
   Copia el archivo de ejemplo y edítalo:
   ```bash
   cp .env.example .env
   ```
   
   Edita `.env` con tus claves:
   ```env
   STEAM_API_KEY=tu_clave_aqui
   OPENAI_API_KEY=tu_clave_aqui
   GDRIVE_MODEL1_ID = "1yS6ZMXBx0yxcjCJDWfHIsit9NPPLFP4_"
   GDRIVE_MODEL2_ID = "1Y4-fzFUfJzoXE-NFsznV7HwSLFK4mOzj"
   GDRIVE_PIPELINE_ID = "1l2k3kC6Qcj77jKizXcIDTbdIqQuewq06"
   GDRIVE_GMM_ID = "1mcsLM1udGvw8nIG67qHEk4P1OMhCz0vH"
   ```

5. **Ejecutar la aplicación**
   
   Con uv (recomendado):
   ```bash
   uv run streamlit run main.py
   ```
   
   O si prefieres activar el entorno virtual:
   ```bash
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   streamlit run main.py
   ```

## ☁️ Despliegue en Streamlit Cloud

Para desplegar en Streamlit Cloud, sigue la guía detallada: [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md)

**Resumen rápido:**

1. Sube modelos a Google Drive ([guía aquí](GOOGLE_DRIVE_SETUP.md))
2. Ve a [share.streamlit.io](https://share.streamlit.io) y conecta tu repositorio
3. Configura los Secrets con tus API keys y los IDs de Google Drive
4. ¡Deploy! 🚀

Consulta [`.streamlit.secrets.example.toml`](.streamlit.secrets.example.toml) para ver el formato exacto de los Secrets.

## 📁 Estructura del Proyecto

```
steamsensepro/
├── main.py                     # Aplicación principal de Streamlit
├── model_utils.py              # Carga y predicción de modelos
├── feature_engineering.py      # Ingeniería de características
├── steam_client.py             # Cliente API de Steam
├── assistant.py                # Asistente conversacional
├── download_models.py          # Descarga automática de modelos
├── setup_gdrive.py             # Script de configuración
├── requirements.txt            # Dependencias
├── pyproject.toml              # Configuración del proyecto
├── .env                       # Variables de entorno
├── GOOGLE_DRIVE_SETUP.md       # Guía de configuración de Drive
├── data/                       # Datos (no en git, Drive: 
└── modelos_*/                  # Modelos entrenados (no en git, Drive: 
```

Link de los modelos y la carpeta data, donde se tiene la información para entrenar los modelos: [modelos_data](https://drive.google.com/drive/folders/1lMs_bK5Yhe6FzYRvg_6yFYBdS7QGnOpj?usp=sharing)



## 🧪 Testing

Para verificar que los modelos se descargan correctamente:

```bash
uv run python download_models.py
```

Deberías ver:
```
📥 Descargando 4 archivo(s) desde Google Drive...
✓ mejor_modelo1_global.pkl descargado
✓ mejor_modelo2_global.pkl descargado
✓ preprocessing_pipeline.pkl descargado
✓ gmm_v2.pkl descargado
✓ Todos los modelos descargados exitosamente
```

## 📊 Modelos

- **Modelo 1 (Precompra)**: Predice probabilidad de abandono antes de comprar
- **Modelo 2 (Postcompra)**: Predice probabilidad de abandono en juegos poseídos
- **Clustering GMM**: Clasifica jugadores en 3 perfiles (Dedicado, Coleccionista Dormido, Coleccionista Masivo)

Los modelos fueron entrenados en los notebooks:
- `01_obtencion_informacion_apis.ipynb` - Obtención de datos de Steam
- `02_eda_e_ingenieria_variables.ipynb` - EDA y entrenamiento de modelos

## 🔧 Desarrollo

Para contribuir o modificar:

1. Instala dependencias de desarrollo:
   ```bash
   uv sync --dev
   ```

2. Entrena tus propios modelos ejecutando los notebooks

3. Los modelos entrenados se guardan en `modelos_*/`

## 📝 Notas

- Los archivos de datos y modelos están en `.gitignore` por su tamaño
- Los modelos se descargan automáticamente al iniciar la app
- La primera ejecución puede tardar unos minutos en descargar los modelos
- En Streamlit Cloud, los modelos se descargan en cada reinicio

## 📄 Licencia

Ver archivo [LICENSE](LICENSE)

## 👤 Autor

Juan Miguel Galan Olivares - [GitHub](https://github.com/JuanMi-Galan)

## 🙏 Agradecimientos

- Steam API para los datos de juegos
- OpenAI para el asistente conversacional
- Scikit-learn, LightGBM, XGBoost para los modelos ML

# Configuración de Google Drive para Modelos

Esta guía explica cómo subir tus modelos a Google Drive y configurar el proyecto para descargarlos automáticamente.

## Paso 1: Subir archivos a Google Drive

1. Ve a [Google Drive](https://drive.google.com)
2. Crea una carpeta llamada `steamsensepro_models` (o el nombre que prefieras)
3. Sube los siguientes archivos:
   - `modelos_1/mejor_modelo1_global.pkl`
   - `modelos_2/mejor_modelo2_global.pkl`
   - `modelos_clustering/preprocessing_pipeline.pkl`
   - `modelos_clustering/gmm_v2.pkl`

## Paso 2: Obtener los IDs de los archivos

Para cada archivo subido:

1. **Haz clic derecho** en el archivo → **Compartir**
2. En la ventana de compartir, haz clic en **"Cambiar a cualquier persona con el enlace"**
3. Asegúrate de que el acceso sea **"Cualquier persona con el enlace puede ver"**
4. Copia el enlace que te da (será algo como):
   ```
   https://drive.google.com/file/d/1A2B3C4D5E6F7G8H9I0J/view?usp=sharing
   ```
5. El **ID del archivo** es la parte entre `/d/` y `/view`:
   ```
   1A2B3C4D5E6F7G8H9I0J  ← Este es tu ID
   ```

## Paso 3: Configurar las variables de entorno

1. Copia el archivo `.env.example` y renómbralo a `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edita el archivo `.env` y reemplaza los IDs:
   ```env
   GDRIVE_MODEL1_ID=1A2B3C4D5E6F7G8H9I0J
   GDRIVE_MODEL2_ID=2B3C4D5E6F7G8H9I0J1K
   GDRIVE_PIPELINE_ID=3C4D5E6F7G8H9I0J1K2L
   GDRIVE_GMM_ID=4D5E6F7G8H9I0J1K2L3M
   ```

## Paso 4: Configurar en Streamlit Cloud

Cuando despliegues en Streamlit Cloud:

1. Ve a **Settings** de tu app
2. En la sección **Secrets**, agrega cada variable:
   ```toml
   GDRIVE_MODEL1_ID = "1A2B3C4D5E6F7G8H9I0J"
   GDRIVE_MODEL2_ID = "2B3C4D5E6F7G8H9I0J1K"
   GDRIVE_PIPELINE_ID = "3C4D5E6F7G8H9I0J1K2L"
   GDRIVE_GMM_ID = "4D5E6F7G8H9I0J1K2L3M"
   STEAM_API_KEY = "tu_steam_api_key"
   OPENAI_API_KEY = "tu_openai_api_key"
   ```

## Verificación

Para probar que la descarga funciona:

```bash
python download_models.py
```

Deberías ver mensajes como:
```
📥 Descargando 4 archivo(s) desde Google Drive...

Descargando mejor_modelo1_global.pkl...
✓ mejor_modelo1_global.pkl descargado
...
✓ Todos los modelos descargados exitosamente
```

## Notas importantes

- Los archivos se descargan **solo la primera vez** que se ejecuta la app
- En Streamlit Cloud, los archivos se descargarán cada vez que la app se reinicie
- Asegúrate de que los archivos en Google Drive tengan **permisos de lectura pública**
- Si cambias los modelos, actualiza los archivos en Google Drive (mantén los mismos IDs)

## Alternativas

Si prefieres usar otro servicio de almacenamiento:

- **Hugging Face Hub**: Ideal para modelos ML, tiene integración directa
- **AWS S3**: Más profesional pero requiere cuenta AWS
- **Dropbox**: Similar a Google Drive
- **GitHub Releases**: Para archivos hasta 2GB con Git LFS

Para cambiar el servicio, modifica el archivo `download_models.py` con la lógica de descarga correspondiente.

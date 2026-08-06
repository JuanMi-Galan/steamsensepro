# 🚀 Guía de Despliegue en Streamlit Cloud

Esta guía te ayudará a desplegar SteamSense Pro en Streamlit Cloud paso a paso.

## 📋 Pre-requisitos

Antes de comenzar, asegúrate de tener:

1. ✅ Cuenta de GitHub con el repositorio `steamsensepro` 
2. ✅ Modelos subidos a Google Drive (ver [GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md))
3. ✅ Los 4 IDs de Google Drive de tus modelos
4. ✅ Steam API Key ([obtener aquí](https://steamcommunity.com/dev/apikey))
5. ✅ OpenAI API Key ([obtener aquí](https://platform.openai.com/api-keys))

## 🌐 Paso 1: Crear cuenta en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Haz clic en **"Sign up"** o **"Get started"**
3. Conecta tu cuenta de GitHub

## 📦 Paso 2: Desplegar la aplicación

1. En Streamlit Cloud, haz clic en **"New app"**

2. Configura el despliegue:
   - **Repository**: `tu-usuario/steamsensepro`
   - **Branch**: `main`
   - **Main file path**: `main.py`
   - **App URL** (opcional): Personaliza la URL de tu app

3. **NO hagas clic en Deploy todavía** - primero configura los Secrets

## 🔐 Paso 3: Configurar Secrets

1. En la página de configuración de tu app, ve a **"Advanced settings"**

2. Haz clic en la pestaña **"Secrets"**

3. Copia y pega el siguiente contenido, **reemplazando con tus valores reales**:

```toml
# Steam API
STEAM_API_KEY = "TU_STEAM_API_KEY_AQUI"

# OpenAI API  
OPENAI_API_KEY = "TU_OPENAI_API_KEY_AQUI"

# Google Drive IDs para descargar modelos
GDRIVE_MODEL1_ID = "1yS6ZMXBx0yxcjCJDWfHIsit9NPPLFP4_"
GDRIVE_MODEL2_ID = "1Y4-fzFUfJzoXE-NFsznV7HwSLFK4mOzj"
GDRIVE_PIPELINE_ID = "1l2k3kC6Qcj77jKizXcIDTbdIqQuewq06"
GDRIVE_GMM_ID = "1mcsLM1udGvw8nIG67qHEk4P1OMhCz0vH"
```

**IMPORTANTE**: 
- Usa las comillas dobles `"` para todos los valores
- NO incluyas espacios después del `=`
- Reemplaza los IDs de ejemplo con los tuyos de Google Drive

4. Haz clic en **"Save"**

## 🚀 Paso 4: Desplegar

1. Haz clic en **"Deploy!"**

2. La app comenzará a construirse. Esto puede tomar 2-5 minutos.

3. Durante el primer inicio, verás en los logs:
   ```
   📥 Intentando descargar 4 archivo(s) desde Google Drive...
   ✓ mejor_modelo1_global.pkl descargado
   ✓ mejor_modelo2_global.pkl descargado
   ...
   ```

4. Una vez completado, tu app estará disponible en la URL asignada

## 🔄 Paso 5: Verificar el despliegue

1. Abre la URL de tu app

2. Verifica que:
   - ✅ La interfaz carga correctamente
   - ✅ Puedes ingresar un Steam ID
   - ✅ Los modelos cargan sin errores

3. Si hay errores, revisa los logs haciendo clic en **"Manage app"** → **"Logs"**

## 🐛 Solución de problemas comunes

### Error: "ID de Google Drive no configurado"

**Causa**: Los secrets no están configurados correctamente.

**Solución**:
1. Ve a **Manage app** → **Settings** → **Secrets**
2. Verifica que todas las variables `GDRIVE_*_ID` estén presentes
3. Asegúrate de usar el formato correcto (sin espacios extra)

### Error: "Access denied" al descargar de Google Drive

**Causa**: Los archivos en Google Drive no tienen permisos públicos.

**Solución**:
1. Para cada archivo en Google Drive:
   - Clic derecho → Compartir
   - Cambiar a "Cualquier persona con el enlace puede ver"
2. Reinicia la app en Streamlit Cloud

### Error: "Module not found"

**Causa**: Alguna dependencia no se instaló correctamente.

**Solución**:
1. Verifica que `requirements.txt` esté actualizado en GitHub
2. Reinicia la app: **Manage app** → **Reboot app**

### La app está lenta o se cae

**Causa**: La descarga de modelos grandes puede agotar los recursos.

**Solución**:
- Los modelos se cachean después de la primera descarga
- La app puede tardar 1-2 minutos en el primer inicio
- Las siguientes cargas serán más rápidas

## 🔄 Actualizar la aplicación

Cuando hagas cambios en tu código:

1. Haz commit y push a GitHub:
   ```bash
   git add .
   git commit -m "Descripción de cambios"
   git push origin main
   ```

2. Streamlit Cloud detectará los cambios automáticamente

3. Si necesitas forzar un redeploy:
   - **Manage app** → **Reboot app**

## 📊 Monitoreo

Puedes ver el estado de tu app en tiempo real:

1. **Logs**: Ver errores y mensajes de debug
2. **Metrics**: Uso de CPU, memoria y ancho de banda
3. **Settings**: Cambiar configuración y secrets

## 💡 Consejos

- **Secrets**: Nunca subas el archivo `.env` a GitHub
- **Caché**: Streamlit cachea los modelos descargados entre sesiones
- **Límites**: Streamlit Cloud tiene límites de recursos en el plan gratuito
- **Backups**: Mantén copias de tus modelos en Google Drive

## 🆘 ¿Necesitas ayuda?

- [Documentación de Streamlit](https://docs.streamlit.io)
- [Foro de Streamlit](https://discuss.streamlit.io)
- [Documentación de esta app](README.md)

---

¡Feliz despliegue! 🎮✨

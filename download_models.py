"""
Descarga automática de modelos y datos desde Google Drive.
Los modelos se descargan solo si no existen localmente.
"""
import os
from pathlib import Path

# Intentar importar gdown solo si es necesario
try:
    import gdown
    GDOWN_AVAILABLE = True
except ImportError:
    GDOWN_AVAILABLE = False
    print("⚠️  gdown no está disponible. La descarga automática está deshabilitada.")


# IDs de archivos en Google Drive (reemplazar con tus propios IDs)
GOOGLE_DRIVE_FILES = {
    "modelos_1/mejor_modelo1_global.pkl": os.getenv("GDRIVE_MODEL1_ID", ""),
    "modelos_2/mejor_modelo2_global.pkl": os.getenv("GDRIVE_MODEL2_ID", ""),
    "modelos_clustering/preprocessing_pipeline.pkl": os.getenv("GDRIVE_PIPELINE_ID", ""),
    "modelos_clustering/gmm_v2.pkl": os.getenv("GDRIVE_GMM_ID", ""),
}

BASE_DIR = Path(__file__).resolve().parent


def download_file_from_gdrive(file_id: str, destination: Path, quiet: bool = False):
    """Descarga un archivo de Google Drive usando su ID."""
    if not file_id:
        raise ValueError(
            f"ID de Google Drive no configurado para {destination}.\n"
            f"Por favor configura la variable de entorno correspondiente en Streamlit Secrets "
            f"o en tu archivo .env local."
        )
    
    if not GDOWN_AVAILABLE:
        raise ImportError(
            "gdown no está instalado. Ejecuta: uv pip install gdown"
        )
    
    url = f"https://drive.google.com/uc?id={file_id}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"📥 Descargando {destination.name}...")
    gdown.download(url, str(destination), quiet=quiet)
    print(f"✓ {destination.name} descargado")


def ensure_models_downloaded(raise_on_missing: bool = True):
    """
    Verifica que todos los modelos existan localmente.
    Si no existen, intenta descargarlos desde Google Drive.
    
    Args:
        raise_on_missing: Si True, lanza excepción si faltan modelos y no se pueden descargar.
                         Si False, solo imprime advertencia.
    """
    missing_files = []
    
    for relative_path, gdrive_id in GOOGLE_DRIVE_FILES.items():
        file_path = BASE_DIR / relative_path
        
        if not file_path.exists():
            missing_files.append((relative_path, gdrive_id, file_path))
    
    if not missing_files:
        print("✓ Todos los modelos están disponibles localmente")
        return True
    
    print(f"\n⚠️  {len(missing_files)} archivo(s) faltante(s)")
    
    # Si no hay IDs configurados, mostrar instrucciones
    if not any(gdrive_id for _, gdrive_id, _ in missing_files):
        error_msg = (
            "\n❌ No se encontraron los modelos localmente y no hay IDs de Google Drive configurados.\n\n"
            "Para usar la aplicación, necesitas:\n"
            "1. Configurar las variables GDRIVE_*_ID en Streamlit Secrets, o\n"
            "2. Tener los archivos de modelos disponibles localmente\n\n"
            "Consulta GOOGLE_DRIVE_SETUP.md para más detalles."
        )
        print(error_msg)
        if raise_on_missing:
            raise ValueError(error_msg)
        return False
    
    # Intentar descargar
    print(f"\n📥 Intentando descargar {len(missing_files)} archivo(s) desde Google Drive...\n")
    
    failed_downloads = []
    for relative_path, gdrive_id, file_path in missing_files:
        try:
            if not gdrive_id:
                print(f"⚠️  Sin ID para {relative_path}, omitiendo...")
                failed_downloads.append(relative_path)
                continue
            download_file_from_gdrive(gdrive_id, file_path, quiet=False)
        except Exception as e:
            print(f"❌ Error descargando {relative_path}: {e}")
            failed_downloads.append(relative_path)
    
    if failed_downloads:
        error_msg = f"\n❌ No se pudieron descargar algunos archivos: {', '.join(failed_downloads)}"
        print(error_msg)
        if raise_on_missing:
            raise RuntimeError(error_msg)
        return False
    
    print("\n✓ Todos los modelos descargados exitosamente\n")
    return True


if __name__ == "__main__":
    # Para probar la descarga manualmente
    ensure_models_downloaded()

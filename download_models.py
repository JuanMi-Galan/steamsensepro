"""
Descarga automática de modelos y datos desde Google Drive.
Los modelos se descargan solo si no existen localmente.
"""
import os
from pathlib import Path
import gdown


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
        raise ValueError(f"ID de Google Drive no configurado para {destination}")
    
    url = f"https://drive.google.com/uc?id={file_id}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Descargando {destination.name}...")
    gdown.download(url, str(destination), quiet=quiet)
    print(f"✓ {destination.name} descargado")


def ensure_models_downloaded():
    """
    Verifica que todos los modelos existan localmente.
    Si no existen, los descarga desde Google Drive.
    """
    missing_files = []
    
    for relative_path, gdrive_id in GOOGLE_DRIVE_FILES.items():
        file_path = BASE_DIR / relative_path
        
        if not file_path.exists():
            missing_files.append((relative_path, gdrive_id, file_path))
    
    if not missing_files:
        print("✓ Todos los modelos ya están disponibles localmente")
        return
    
    print(f"\n📥 Descargando {len(missing_files)} archivo(s) desde Google Drive...\n")
    
    for relative_path, gdrive_id, file_path in missing_files:
        try:
            download_file_from_gdrive(gdrive_id, file_path, quiet=False)
        except Exception as e:
            print(f"❌ Error descargando {relative_path}: {e}")
            raise
    
    print("\n✓ Todos los modelos descargados exitosamente\n")


if __name__ == "__main__":
    # Para probar la descarga manualmente
    ensure_models_downloaded()

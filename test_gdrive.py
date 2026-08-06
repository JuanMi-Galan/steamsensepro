#!/usr/bin/env python3
"""
Script para probar la descarga desde Google Drive.
Verifica que los IDs de Google Drive sean correctos y accesibles.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Importar después de cargar .env
import gdown

# IDs de archivos en Google Drive
GDRIVE_IDS = {
    "GDRIVE_MODEL1_ID": os.getenv("GDRIVE_MODEL1_ID", ""),
    "GDRIVE_MODEL2_ID": os.getenv("GDRIVE_MODEL2_ID", ""),
    "GDRIVE_PIPELINE_ID": os.getenv("GDRIVE_PIPELINE_ID", ""),
    "GDRIVE_GMM_ID": os.getenv("GDRIVE_GMM_ID", ""),
}


def test_gdrive_id(name: str, file_id: str):
    """Prueba si un ID de Google Drive es accesible."""
    if not file_id:
        print(f"❌ {name}: ID vacío")
        return False
    
    print(f"\n🔍 Probando {name}: {file_id}")
    
    try:
        # Crear URL
        url = f"https://drive.google.com/uc?id={file_id}"
        print(f"   URL: {url}")
        
        # Intentar obtener información del archivo
        output_path = Path(f"/tmp/test_{name}.pkl")
        
        # Descargar solo los primeros bytes para verificar acceso
        print(f"   Intentando acceder al archivo...")
        gdown.download(url, str(output_path), quiet=False)
        
        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"   ✓ Archivo accesible! Tamaño: {size_mb:.2f} MB")
            output_path.unlink()  # Eliminar archivo de prueba
            return True
        else:
            print(f"   ❌ No se pudo descargar")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    print("=" * 70)
    print("🧪 PRUEBA DE ACCESO A GOOGLE DRIVE")
    print("=" * 70)
    
    results = {}
    
    for name, file_id in GDRIVE_IDS.items():
        results[name] = test_gdrive_id(name, file_id)
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN")
    print("=" * 70)
    
    success_count = sum(results.values())
    total_count = len(results)
    
    for name, success in results.items():
        status = "✓" if success else "❌"
        print(f"  {status} {name}: {'OK' if success else 'FALLO'}")
    
    print()
    print(f"Éxito: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n✅ Todos los archivos son accesibles desde Google Drive!")
        print("   Puedes desplegar en Streamlit Cloud con confianza.")
    else:
        print("\n⚠️  Algunos archivos no son accesibles.")
        print("\nVerifica que:")
        print("1. Los archivos en Google Drive tengan permisos públicos")
        print("   (Cualquier persona con el enlace puede ver)")
        print("2. Los IDs en el archivo .env sean correctos")
        print("3. Los archivos no hayan sido eliminados")
    
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Prueba cancelada")
    except Exception as e:
        print(f"\n❌ Error general: {e}")

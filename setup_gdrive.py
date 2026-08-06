#!/usr/bin/env python3
"""
Script de ayuda para configurar los modelos en Google Drive.
Te guía paso a paso para obtener los IDs de Google Drive.
"""

import os
from pathlib import Path


def main():
    print("=" * 70)
    print("🚀 CONFIGURACIÓN DE MODELOS EN GOOGLE DRIVE")
    print("=" * 70)
    print("\nEste script te ayudará a configurar los IDs de Google Drive.\n")
    
    base_dir = Path(__file__).parent
    
    # Archivos que necesitan subirse
    files_to_upload = [
        ("modelos_1/mejor_modelo1_global.pkl", "GDRIVE_MODEL1_ID"),
        ("modelos_2/mejor_modelo2_global.pkl", "GDRIVE_MODEL2_ID"),
        ("modelos_clustering/preprocessing_pipeline.pkl", "GDRIVE_PIPELINE_ID"),
        ("modelos_clustering/gmm_v2.pkl", "GDRIVE_GMM_ID"),
    ]
    
    print("📋 ARCHIVOS A SUBIR:")
    print("-" * 70)
    for path, _ in files_to_upload:
        file_path = base_dir / path
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"  ✓ {path} ({size_mb:.2f} MB)")
        else:
            print(f"  ✗ {path} (NO ENCONTRADO)")
    print()
    
    print("📝 PASOS A SEGUIR:")
    print("-" * 70)
    print("1. Ve a https://drive.google.com")
    print("2. Crea una carpeta (ej: 'steamsensepro_models')")
    print("3. Sube los archivos listados arriba")
    print("4. Para cada archivo:")
    print("   - Clic derecho → Compartir")
    print("   - Cambia a 'Cualquier persona con el enlace puede ver'")
    print("   - Copia el enlace")
    print("   - El ID está entre '/d/' y '/view'")
    print("   - Ejemplo: https://drive.google.com/file/d/ABC123XYZ/view")
    print("            El ID es: ABC123XYZ")
    print()
    
    env_file = base_dir / ".env"
    env_example = base_dir / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print("📄 No se encontró .env, ¿quieres crear uno desde .env.example?")
        response = input("(s/n): ").lower().strip()
        if response == 's':
            with open(env_example) as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
            print(f"✓ Archivo .env creado\n")
    
    print("🔧 CONFIGURACIÓN DE IDs:")
    print("-" * 70)
    print("Ahora vamos a configurar los IDs de Google Drive.\n")
    
    config_lines = []
    
    for path, env_var in files_to_upload:
        print(f"\n📁 {path}")
        file_id = input(f"   Ingresa el ID de Google Drive para {env_var}: ").strip()
        config_lines.append(f'{env_var}="{file_id}"')
    
    print("\n" + "=" * 70)
    print("📋 CONFIGURACIÓN GENERADA:")
    print("=" * 70)
    print()
    for line in config_lines:
        print(line)
    print()
    
    if env_file.exists():
        print(f"💾 ¿Quieres actualizar el archivo .env?")
        response = input("(s/n): ").lower().strip()
        if response == 's':
            # Leer .env actual
            with open(env_file) as f:
                lines = f.readlines()
            
            # Actualizar las líneas de GDRIVE
            updated_lines = []
            gdrive_vars = {var for _, var in files_to_upload}
            
            for line in lines:
                var_name = line.split('=')[0].strip()
                if var_name in gdrive_vars:
                    # Reemplazar con el nuevo valor
                    for config_line in config_lines:
                        if config_line.startswith(var_name):
                            updated_lines.append(config_line + '\n')
                            break
                else:
                    updated_lines.append(line)
            
            # Escribir de vuelta
            with open(env_file, 'w') as f:
                f.writelines(updated_lines)
            
            print(f"✓ Archivo .env actualizado\n")
    else:
        print("⚠️  Crea un archivo .env y agrega la configuración de arriba\n")
    
    print("=" * 70)
    print("✅ CONFIGURACIÓN COMPLETA")
    print("=" * 70)
    print("\n🧪 Para probar la descarga, ejecuta:")
    print("   python download_models.py")
    print("\n🚀 Para iniciar la app:")
    print("   streamlit run main.py")
    print("\n📖 Para más detalles, consulta GOOGLE_DRIVE_SETUP.md")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Configuración cancelada")
    except Exception as e:
        print(f"\n❌ Error: {e}")

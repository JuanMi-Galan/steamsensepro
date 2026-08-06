#!/bin/bash
# Script para ejecutar la aplicación SteamSense Pro

echo "🎮 Iniciando SteamSense Pro..."
echo ""

# Verificar que existe el archivo .env
if [ ! -f .env ]; then
    echo "⚠️  No se encontró el archivo .env"
    echo "   Por favor, copia .env.example a .env y configura tus claves:"
    echo "   cp .env.example .env"
    echo ""
    exit 1
fi

# Ejecutar con uv
echo "📦 Ejecutando con uv..."
uv run streamlit run main.py

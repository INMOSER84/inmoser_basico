#!/bin/bash

# Script para eliminar todas las cachés del módulo

echo "Limpiando cachés del módulo inmoser_service_order..."

# Eliminar directorios __pycache__ en todo el módulo
find . -type d -name "__pycache__" -exec rm -rf {} +

# Eliminar archivos .pyc en todo el módulo
find . -name "*.pyc" -delete

# Eliminar archivos .pyo (archivos de bytecode optimizados)
find . -name "*.pyo" -delete

# Eliminar directorios .pytest_cache si existen
find . -type d -name ".pytest_cache" -exec rm -rf {} +

# Eliminar directorios .cache si existen
find . -type d -name ".cache" -exec rm -rf {} +

# Eliminar archivos .coverage si existen
find . -name ".coverage" -delete

# Eliminar directorios __pycache__ en el directorio raíz si existe
if [ -d "__pycache__" ]; then
    rm -rf __pycache__
fi

# Eliminar archivos de caché de Odoo si existen
find . -name "*.cache" -delete

echo "Limpieza de cachés completada."
echo "Archivos restantes en el módulo:"
ls -la

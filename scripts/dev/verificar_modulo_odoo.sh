#!/bin/bash

MODULO_PATH="$1"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOGFILE="verificacion_modulo_${TIMESTAMP}.log"

echo "🔍 Verificando módulo: $MODULO_PATH" | tee "$LOGFILE"

# 1. Verificar manifest
if [ ! -f "$MODULO_PATH/__manifest__.py" ]; then
  echo "❌ ERROR: No se encontró __manifest__.py" | tee -a "$LOGFILE"
  exit 1
else
  echo "✅ Manifest encontrado" | tee -a "$LOGFILE"
fi

# 2. Validar sintaxis Python
echo "🧪 Validando sintaxis Python..." | tee -a "$LOGFILE"
find "$MODULO_PATH" -type f -name "*.py" | while read -r file; do
  if ! python3 -m py_compile "$file" 2>>"$LOGFILE"; then
    echo "❌ Error de sintaxis en: $file" | tee -a "$LOGFILE"
  else
    echo "✅ $file OK" | tee -a "$LOGFILE"
  fi
done

# 3. Validar XML
echo "🧪 Validando XML..." | tee -a "$LOGFILE"
find "$MODULO_PATH" -type f -name "*.xml" | while read -r file; do
  if ! xmllint --noout "$file" 2>>"$LOGFILE"; then
    echo "❌ Error XML en: $file" | tee -a "$LOGFILE"
  else
    echo "✅ $file OK" | tee -a "$LOGFILE"
  fi
done

# 4. Validar estructura mínima
REQUIRED_DIRS=("models" "views" "security")
for dir in "${REQUIRED_DIRS[@]}"; do
  if [ ! -d "$MODULO_PATH/$dir" ]; then
    echo "⚠️ Advertencia: Falta carpeta '$dir'" | tee -a "$LOGFILE"
  else
    echo "✅ Carpeta '$dir' presente" | tee -a "$LOGFILE"
  fi
done

# 5. Resultado final
echo "🧾 Verificación completa. Revisa el log: $LOGFILE" | tee -a "$LOGFILE"

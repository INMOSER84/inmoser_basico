#!/bin/bash
# Simulación de instalación Odoo – Auditoría técnica mejorada
# Autor: Inmoser DevOps

set -euo pipefail  # Salir en errores y variables no definidas

# Colores para salida
readonly ROJO='\033[0;31m'
readonly VERDE='\033[0;32m'
readonly AMARILLO='\033[1;33m'
readonly AZUL='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuración
readonly MODULO_PATH="${1:-}"
readonly LOGDIR="$HOME/odoo-inmoser_clean/logs"
readonly TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
readonly LOGFILE="$LOGDIR/simulacion_instalacion_${TIMESTAMP}.log"
readonly CHANGELOG="$LOGDIR/changelog.txt"

# Funciones de utilidad
log_info()    { echo -e "${AZUL}[INFO]${NC} $*"    | tee -a "$LOGFILE"; }
log_error()   { echo -e "${ROJO}[ERROR]${NC} $*"   | tee -a "$LOGFILE"; }
log_success() { echo -e "${VERDE}[SUCCESS]${NC} $*"| tee -a "$LOGFILE"; }
log_warning() { echo -e "${AMARILLO}[WARNING]${NC} $*"| tee -a "$LOGFILE"; }

check_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        log_error "Comando requerido no encontrado: $1"
        return 1
    fi
    return 0
}

validate_manifest() {
    local manifest="$1"
    log_info "Validando manifest: $manifest"

    if [[ ! -f "$manifest" ]]; then
        log_error "No se encontró __manifest__.py"
        return 1
    fi

    if ! python3 -c "
import ast, sys
try:
    with open('$manifest', 'r', encoding='utf-8') as f:
        data = f.read()
    manifest = ast.literal_eval(data)
    if not isinstance(manifest, dict):
        raise ValueError('El manifest no es un diccionario')
    print('[SUCCESS] Manifest válido')
    print('Nombre:', manifest.get('name', 'Sin nombre'))
    print('Versión:', manifest.get('version', 'Sin versión'))
    print('Dependencias:', ', '.join(manifest.get('depends', [])))
except Exception as e:
    print(f'[ERROR] {e}')
    sys.exit(1)
" >> "$LOGFILE" 2>&1; then
        log_error "El manifest contiene errores"
        return 1
    fi

    log_success "Manifest válido"
    return 0
}

check_dependencies() {
    local manifest="$1"
    log_info "Verificando dependencias"

    python3 -c "
import ast
with open('$manifest', 'r', encoding='utf-8') as f:
    manifest = ast.literal_eval(f.read())
deps = manifest.get('depends', [])
if deps:
    print('Dependencias encontradas:')
    for dep in deps:
        print(f'  - {dep}')
else:
    print('No se declararon dependencias')
" | tee -a "$LOGFILE"
}

validate_xml_files() {
    log_info "Validando archivos XML"
    local xml_files=()
    local errors=0

    while IFS= read -r -d '' file; do
        xml_files+=("$file")
    done < <(find "$MODULO_PATH" -type f -name "*.xml" -print0)

    if [[ ${#xml_files[@]} -eq 0 ]]; then
        log_warning "No se encontraron archivos XML"
        return 0
    fi

    for file in "${xml_files[@]}"; do
        if xmllint --noout "$file" 2>/dev/null; then
            log_success "XML válido: ${file#$MODULO_PATH/}"
        else
            log_error "Error XML en: ${file#$MODULO_PATH/}"
            xmllint --noout "$file" 2>>"$LOGFILE"
            ((errors++))
        fi
    done

    return $errors
}

validate_python_files() {
    log_info "Validando archivos Python"
    local py_files=()
    local errors=0

    while IFS= read -r -d '' file; do
        py_files+=("$file")
    done < <(find "$MODULO_PATH" -type f -name "*.py" -print0)

    if [[ ${#py_files[@]} -eq 0 ]]; then
        log_warning "No se encontraron archivos Python"
        return 0
    fi

    for file in "${py_files[@]}"; do
        if python3 -m py_compile "$file" 2>/dev/null; then
            log_success "Python válido: ${file#$MODULO_PATH/}"
        else
            log_error "Error de sintaxis en: ${file#$MODULO_PATH/}"
            python3 -m py_compile "$file" 2>>"$LOGFILE"
            ((errors++))
        fi
    done

    return $errors
}

check_directory_structure() {
    log_info "Verificando estructura de directorios"
    local required_dirs=("models" "views" "security")
    local optional_dirs=("data" "demo" "i18n" "static" "report" "wizard")

    for dir in "${required_dirs[@]}"; do
        if [[ -d "$MODULO_PATH/$dir" ]]; then
            log_success "Directorio encontrado: $dir"
        else
            log_warning "Falta directorio requerido: $dir"
        fi
    done

    for dir in "${optional_dirs[@]}"; do
        if [[ -d "$MODULO_PATH/$dir" ]]; then
            log_info "Directorio opcional encontrado: $dir"
        fi
    done
}

check_security_files() {
    log_info "Verificando archivos de seguridad"
    local security_dir="$MODULO_PATH/security"

    if [[ -d "$security_dir" ]]; then
        local csv_files=()
        while IFS= read -r -d '' file; do
            csv_files+=("$file")
        done < <(find "$security_dir" -type f -name "*.csv" -print0)

        if [[ ${#csv_files[@]} -gt 0 ]]; then
            for file in "${csv_files[@]}"; do
                log_info "Archivo CSV de seguridad: ${file#$MODULO_PATH/}"
            done
        else
            log_warning "No se encontraron archivos CSV de seguridad"
        fi

        local xml_files=()
        while IFS= read -r -d '' file; do
            xml_files+=("$file")
        done < <(find "$security_dir" -type f -name "*.xml" -print0)

        if [[ ${#xml_files[@]} -gt 0 ]]; then
            for file in "${xml_files[@]}"; do
                if xmllint --noout "$file" 2>/dev/null; then
                    log_success "XML de seguridad válido: ${file#$MODULO_PATH/}"
                else
                    log_error "Error en XML de seguridad: ${file#$MODULO_PATH/}"
                fi
            done
        fi
    else
        log_warning "No existe directorio security"
    fi
}

generate_summary() {
    log_info "Generando resumen de la simulación"

    local total_errors=$(grep -c "\[ERROR\]" "$LOGFILE" 2>/dev/null || echo 0)
    local total_warnings=$(grep -c "\[WARNING\]" "$LOGFILE" 2>/dev/null || echo 0)
    local total_success=$(grep -c "\[SUCCESS\]" "$LOGFILE" 2>/dev/null || echo 0)

    # Asegurar enteros sin saltos ni espacios
    total_errors=$(echo "$total_errors" | tr -d '[:space:]')
    total_warnings=$(echo "$total_warnings" | tr -d '[:space:]')
    total_success=$(echo "$total_success" | tr -d '[:space:]')

    echo "=====================================================" | tee -a "$LOGFILE"
    echo "📊 RESUMEN DE LA SIMULACIÓN" | tee -a "$LOGFILE"
    echo "=====================================================" | tee -a "$LOGFILE"
    echo "✅ Completados: $total_success" | tee -a "$LOGFILE"
    echo "⚠️  Advertencias: $total_warnings" | tee -a "$LOGFILE"
    echo "❌ Errores: $total_errors" | tee -a "$LOGFILE"
    echo "📋 Log completo: $LOGFILE" | tee -a "$LOGFILE"

    {
        echo "====================================================="
        echo "📌 Simulación de instalación $(basename "$MODULO_PATH") – $(date)"
        echo "Resultados: ✅$total_success ⚠️$total_warnings ❌$total_errors"
        if [[ $total_errors -gt 0 ]]; then
            echo "Errores encontrados:"
            grep "\[ERROR\]" "$LOGFILE" | head -10
        fi
        echo ""
    } >> "$CHANGELOG"
}

main() {
    if [[ -z "$MODULO_PATH" ]]; then
        echo "❌ ERROR: Debes indicar la ruta del módulo."
        echo "Uso: $0 /ruta/al/modulo"
        exit 1
    fi

    if [[ ! -d "$MODULO_PATH" ]]; then
        log_error "El directorio no existe: $MODULO_PATH"
        exit 1
    fi

    mkdir -p "$LOGDIR"

    log_info "🔧 Simulando instalación de: $MODULO_PATH"
    log_info "📁 Módulo: $(basename "$MODULO_PATH")"
    log_info "📍 Ruta: $MODULO_PATH"

    log_info "Verificando dependencias del sistema"
    local deps_faltantes=0
    for cmd in python3 xmllint find grep tee; do
        if ! check_command "$cmd"; then
            ((deps_faltantes++))
        fi
    done

    if [[ $deps_faltantes -gt 0 ]]; then
        log_error "Faltan dependencias del sistema"
        exit 1
    fi

    local manifest_path="$MODULO_PATH/__manifest__.py"
    if validate_manifest "$manifest_path"; then
        check_dependencies "$manifest_path"
    else
        exit 1
    fi

    local xml_errors=0
    local py_errors=0

    validate_xml_files || xml_errors=$?
    validate_python_files || py_errors=$?

    check_directory_structure
    check_security_files

    generate_summary

    if [[ $xml_errors -eq 0 && $py_errors -eq 0 ]]; then
        log_success "🎉 Simulación completada sin errores críticos"
        exit 0
    else
        log_error "❌ Simulación completada con errores"
        exit 1
    fi
}

main "$@"

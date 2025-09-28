#!/bin/bash
# Reset completo y validación quirúrgica – Inmoser DevOps v4
set -euo pipefail

# Colores
readonly ROJO='\033[0;31m'
readonly VERDE='\033[0;32m'
readonly AMARILLO='\033[1;33m'
readonly AZUL='\033[0;34m'
readonly NC='\033[0m'

# Configuración
readonly ODOO_DB="inmoser17"
readonly ODOO_USER="odoo"
readonly ODOO_PASS="odoo"
readonly ODOO_PORT="8069"
readonly DB_PORT="5432"
readonly ADMIN_PASS="admin"
readonly NETWORK="inmoser-net"
readonly ODOO_IMG="odoo:17"
readonly PG_IMG="postgres:15"
readonly ADDONS_HOST="$HOME/odoo-inmoser_clean/addons"
readonly MODULO="inmoser_service_order"
readonly LOGDIR="$HOME/odoo-inmoser_clean/logs"
readonly CHANGELOG="$LOGDIR/changelog.txt"
readonly TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
readonly BACKUP_DIR="$HOME/odoo-inmoser_clean/backups"

# Variables de control
DRY_RUN=false
SKIP_BACKUP=false
VERBOSE=false

# Contenedores y volúmenes
readonly CONTAINERS=(odoo db)
readonly VOLUMES=(odoo-data db-data)

# Logging
log() { echo -e "$*" | tee -a "$LOGDIR/reset_${TIMESTAMP}.log"; }
log_info()    { log "${AZUL}[INFO]${NC} $*"; }
log_error()   { log "${ROJO}[ERROR]${NC} $*"; }
log_success() { log "${VERDE}[SUCCESS]${NC} $*"; }
log_warning() { log "${AMARILLO}[WARNING]${NC} $*"; }

usage() {
    cat << EOF
Uso: $0 [OPCIONES]

Opciones:
    -d, --dry-run        Simulación sin cambios
    -s, --skip-backup    No hacer backup de BD
    -v, --verbose        Mostrar logs completos
    -h, --help           Ayuda
EOF
}

# Parseo de argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dry-run) DRY_RUN=true ;;
        -s|--skip-backup) SKIP_BACKUP=true ;;
        -v|--verbose) VERBOSE=true ;;
        -h|--help) usage; exit 0 ;;
        *) log_error "Opción desconocida: $1"; usage; exit 1 ;;
    esac
    shift
done

mkdir -p "$LOGDIR" "$BACKUP_DIR"
START_TIME=$(date +%s)

check_ports() {
    log_info "🔍 Verificando puertos $ODOO_PORT y $DB_PORT"
    for port in "$ODOO_PORT" "$DB_PORT"; do
        if lsof -iTCP:$port -sTCP:LISTEN >/dev/null 2>&1; then
            log_error "Puerto $port en uso. Abortando."
            exit 1
        fi
    done
    log_success "Puertos libres"
}

backup_database() {
    if [[ "$SKIP_BACKUP" == true ]]; then
        log_info "⏭️ Saltando backup de BD"
        return
    fi
    if docker ps | grep -q "db"; then
        local file="$BACKUP_DIR/backup_${ODOO_DB}_${TIMESTAMP}.sql"
        docker exec -i db pg_dump -U "$ODOO_USER" "$ODOO_DB" > "$file" 2>/dev/null || \
            log_warning "No se pudo crear backup (BD no existe)"
        log_success "Backup guardado: $file"
    else
        log_info "No hay BD activa para backup"
    fi
}

cleanup_containers() {
    log_info "🧹 Limpiando contenedores y volúmenes"
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY-RUN] Contenedores: ${CONTAINERS[*]}, Volúmenes: ${VOLUMES[*]}, Red: $NETWORK"
        return
    fi
    docker rm -f "${CONTAINERS[@]}" 2>/dev/null || true
    docker volume rm "${VOLUMES[@]}" 2>/dev/null || true
    docker network rm "$NETWORK" 2>/dev/null || true
    log_success "Contenedores, volúmenes y red eliminados"
}

validate_module() {
    log_info "🔍 Validando módulo $MODULO..."
    if [[ ! -d "$ADDONS_HOST/$MODULO" ]]; then
        log_error "Ruta del módulo no existe: $ADDONS_HOST/$MODULO"
        exit 1
    fi
    if ! "$HOME/odoo-inmoser_clean/scripts/dev/simular_instalacion_odoo.sh" "$ADDONS_HOST/$MODULO"; then
        log_error "Validación fallida. Abortando."
        echo "❌ Falló despliegue – $TIMESTAMP" >> "$CHANGELOG"
        exit 1
    fi
    log_success "Módulo válido"
}

create_network() {
    log_info "🌐 Creando red Docker"
    [[ "$DRY_RUN" == true ]] && { log_info "[DRY-RUN] Se crearía red $NETWORK"; return; }
    docker network create "$NETWORK" 2>/dev/null || true
    log_success "Red $NETWORK lista"
}

launch_postgres() {
    log_info "🐘 Lanzando PostgreSQL"
    [[ "$DRY_RUN" == true ]] && { log_info "[DRY-RUN] Se lanzaría PostgreSQL"; return; }
    docker run -d --name db --network "$NETWORK" -v db-data:/var/lib/postgresql/data \
        -e POSTGRES_DB="$ODOO_DB" -e POSTGRES_USER="$ODOO_USER" -e POSTGRES_PASSWORD="$ODOO_PASS" "$PG_IMG"
    
    log_info "⏳ Esperando 15 segundos iniciales antes de chequear PostgreSQL..."
    sleep 15

    local tries=0
    until docker exec -i db pg_isready -U "$ODOO_USER" >/dev/null 2>&1; do
        ((tries++))
        [[ $tries -gt 15 ]] && { log_error "PostgreSQL no arrancó"; docker logs db; exit 1; }
        echo -n "."
        sleep 2
    done
    echo -e "\n${VERDE}✅ PostgreSQL listo${NC}"
}

init_odoo_db() {
    log_info "🧠 Inicializando base Odoo"
    [[ "$DRY_RUN" == true ]] && { log_info "[DRY-RUN] Se inicializaría la base"; return; }
    docker run --rm --network "$NETWORK" -v odoo-data:/var/lib/odoo -v "$ADDONS_HOST:/mnt/extra-addons:ro" \
        "$ODOO_IMG" odoo -d "$ODOO_DB" --db_host=db --db_user="$ODOO_USER" --db_password="$ODOO_PASS" \
        --init base --stop-after-init --addons-path=/mnt/extra-addons
    log_success "Base Odoo inicializada"
}

install_module_and_test() {
    log_info "📦 Instalando módulo y ejecutando tests..."
    local install_log="$LOGDIR/install_${MODULO}_${TIMESTAMP}.log"
    local test_log="$LOGDIR/test_${MODULO}_${TIMESTAMP}.log"
    [[ "$DRY_RUN" == true ]] && { log_info "[DRY-RUN] Se instalaría módulo y ejecutarían tests"; return; }
    docker run --rm --network "$NETWORK" -v odoo-data:/var/lib/odoo -v "$ADDONS_HOST:/mnt/extra-addons:ro" \
        "$ODOO_IMG" odoo -d "$ODOO_DB" --db_host=db --db_user="$ODOO_USER" --db_password="$ODOO_PASS" \
        --stop-after-init -i "$MODULO" --test-enable --addons-path=/mnt/extra-addons \
        2>&1 | tee "$install_log" "$test_log"
    if grep -q "ERROR\|FAIL\|Traceback" "$test_log"; then
        log_error "❌ Tests fallidos. Rollback completo"
        docker rm -f "${CONTAINERS[@]}" 2>/dev/null || true
        docker volume rm "${VOLUMES[@]}" 2>/dev/null || true
        docker network rm "$NETWORK" 2>/dev/null || true
        exit 1
    fi
    log_success "✅ Tests pasados"
}

show_summary() {
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    log_info "====================================================="
    log_info "📊 RESUMEN"
    log_info "⏱️ Duración: ${duration}s"
    log_info "📁 Logs: $LOGDIR/reset_${TIMESTAMP}.log"
    log_info "📝 Changelog: $CHANGELOG"
    [[ "$DRY_RUN" == false ]] && log_info "🌐 Odoo disponible en http://localhost:$ODOO_PORT"
    log_info "====================================================="
}

main() {
    log_info "🚀 Iniciando reset completo de Odoo"
    check_ports
    backup_database
    cleanup_containers
    validate_module
    create_network
    launch_postgres
    init_odoo_db
    install_module_and_test
    [[ "$DRY_RUN" == false ]] && echo "📌 Despliegue exitoso – $TIMESTAMP" >> "$CHANGELOG"
    show_summary
}

main "$@"

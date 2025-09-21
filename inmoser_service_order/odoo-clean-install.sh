#!/bin/bash

# Script: odoo-clean-install.sh
# Descripción: Limpieza profunda de contenedores Odoo y PostgreSQL, e instalación desde cero
# Autor: Inmoser
# Versión: 1.0

set -e  # Exit on error

echo "=============================================="
echo "  LIMPIEZA PROFUNDA E INSTALACIÓN DE ODOO 17  "
echo "=============================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que Docker esté instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado. Instálalo primero."
        exit 1
    fi
    print_success "Docker está instalado"
}

# Limpieza profunda de contenedores Docker
clean_docker() {
    print_status "Iniciando limpieza profunda de Docker..."
    
    # Detener todos los contenedores
    if [ "$(docker ps -aq)" ]; then
        print_status "Deteniendo todos los contenedores..."
        docker stop $(docker ps -aq)
    fi
    
    # Eliminar todos los contenedores
    if [ "$(docker ps -aq)" ]; then
        print_status "Eliminando todos los contenedores..."
        docker rm $(docker ps -aq) -f
    fi
    
    # Eliminar todas las imágenes
    if [ "$(docker images -q)" ]; then
        print_status "Eliminando todas las imágenes..."
        docker rmi $(docker images -q) -f
    fi
    
    # Eliminar todos los volúmenes
    if [ "$(docker volume ls -q)" ]; then
        print_status "Eliminando todos los volúmenes..."
        docker volume rm $(docker volume ls -q) -f
    fi
    
    # Eliminar todas las redes (excepto las predefinidas)
    if [ "$(docker network ls -q --filter type=custom)" ]; then
        print_status "Eliminando redes personalizadas..."
        docker network rm $(docker network ls -q --filter type=custom)
    fi
    
    # Limpiar sistema Docker
    print_status "Limpiando sistema Docker..."
    docker system prune -a -f --volumes
    
    # Verificar que no queden rastros
    print_status "Verificando limpieza..."
    echo "Contenedores: $(docker ps -aq)"
    echo "Imágenes: $(docker images -q)"
    echo "Volúmenes: $(docker volume ls -q)"
    
    print_success "Limpieza Docker completada"
}

# Crear estructura de directorios
create_directories() {
    print_status "Creando estructura de directorios..."
    
    # Directorio principal
    mkdir -p /opt/odoo17
    cd /opt/odoo17
    
    # Directorios para Odoo
    mkdir -p addons config data logs custom-addons
    
    # Crear directorio para el módulo personalizado
    mkdir -p custom-addons/inmoser_service_order
    
    print_success "Directorios creados"
}

# Crear archivo de configuración Odoo
create_odoo_config() {
    print_status "Creando archivo de configuración Odoo..."
    
    cat > /opt/odoo17/config/odoo.conf << 'EOL'
[options]
addons_path = /mnt/extra-addons,/mnt/extra-addons/inmoser_service_order
data_dir = /var/lib/odoo
admin_passwd = admin
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo
db_name = odoo17
without_demo = all
list_db = True
proxy_mode = True
http_port = 8069
logfile = /var/log/odoo/odoo.log
log_level = info
EOL

    print_success "Configuración Odoo creada"
}

# Crear docker-compose.yml
create_docker_compose() {
    print_status "Creando docker-compose.yml..."
    
    cat > /opt/odoo17/docker-compose.yml << 'EOL'
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=odoo
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - odoo-db-data:/var/lib/postgresql/data/pgdata
    restart: unless-stopped
    networks:
      - odoo-network

  odoo:
    image: odoo:17.0
    depends_on:
      - db
    ports:
      - "8069:8069"
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./config:/etc/odoo
      - ./logs:/var/log/odoo
      - ./custom-addons:/mnt/extra-addons
    restart: unless-stopped
    networks:
      - odoo-network

volumes:
  odoo-db-data:
  odoo-web-data:

networks:
  odoo-network:
    driver: bridge
EOL

    print_success "Docker Compose creado"
}

# Copiar módulo personalizado
copy_custom_module() {
    print_status "Copiando módulo personalizado..."
    
    # Verificar si el módulo existe en la ubicación original
    if [ -d "/opt/odoo17/custom/addons/inmoser_service_order" ]; then
        cp -r /opt/odoo17/custom/addons/inmoser_service_order /opt/odoo17/custom-addons/
        print_success "Módulo copiado"
    else
        print_warning "Módulo no encontrado en /opt/odoo17/custom/addons/, se creará uno básico"
        
        # Crear estructura básica del módulo
        mkdir -p /opt/odoo17/custom-addons/inmoser_service_order
        cat > /opt/odoo17/custom-addons/inmoser_service_order/__manifest__.py << 'EOL'
{
    "name": "Inmoser Service Order",
    "version": "17.0.1.0.0",
    "category": "Services",
    "author": "Inmoser",
    "website": "https://www.inmoser.com",
    "depends": ["base"],
    "application": True,
    "installable": True,
}
EOL
        
        cat > /opt/odoo17/custom-addons/inmoser_service_order/__init__.py << 'EOL'
# Empty init file
EOL
    fi
}

# Iniciar contenedores
start_containers() {
    print_status "Iniciando contenedores Docker..."
    
    cd /opt/odoo17
    
    # Iniciar servicios
    docker-compose up -d
    
    # Esperar a que los servicios estén listos
    print_status "Esperando a que los servicios estén listos..."
    sleep 30
    
    # Verificar estado de los contenedores
    print_status "Verificando estado de los contenedores..."
    docker-compose ps
    
    print_success "Contenedores iniciados"
}

# Crear base de datos Odoo
create_database() {
    print_status "Creando base de datos Odoo..."
    
    # Esperar a que PostgreSQL esté listo
    print_status "Esperando a que PostgreSQL esté listo..."
    sleep 10
    
    # Crear base de datos usando el contenedor Odoo
    docker-compose exec -T odoo python -c "
import sys
try:
    from odoo.tools.config import config
    from odoo.service.db import _create_empty_database
    config['db_name'] = 'odoo17'
    config['db_user'] = 'odoo'
    config['db_password'] = 'odoo'
    config['db_host'] = 'db'
    config['db_port'] = '5432'
    _create_empty_database('odoo17')
    print('Database created successfully')
except Exception as e:
    print(f'Error creating database: {e}')
    sys.exit(1)
"
    
    print_success "Base de datos creada"
}

# Instalar módulo personalizado
install_custom_module() {
    print_status "Instalando módulo personalizado..."
    
    # Esperar a que Odoo esté completamente iniciado
    print_status "Esperando a que Odoo esté listo..."
    sleep 60
    
    # Instalar módulo usando Odoo shell
    docker-compose exec -T odoo python -c "
import requests
import time

# Configuración
url = 'http://localhost:8069'
db_name = 'odoo17'
admin_password = 'admin'
module_name = 'inmoser_service_order'

# Esperar a que Odoo esté respondiendo
max_retries = 12
retry_delay = 10

for i in range(max_retries):
    try:
        response = requests.get(f'{url}/web/database/selector', timeout=10)
        if response.status_code == 200:
            print('Odoo is ready')
            break
    except requests.exceptions.RequestException:
        print(f'Waiting for Odoo to start... ({i+1}/{max_retries})')
        time.sleep(retry_delay)
else:
    print('Odoo did not start in time')
    exit(1)

# Instalar módulo
try:
    import xmlrpc.client
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db_name, 'admin', admin_password, {})
    
    if uid:
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        # Verificar si el módulo existe
        module_ids = models.execute_kw(db_name, uid, admin_password,
            'ir.module.module', 'search',
            [[['name', '=', module_name]]]
        )
        
        if module_ids:
            # Instalar módulo
            result = models.execute_kw(db_name, uid, admin_password,
                'ir.module.module', 'button_immediate_install',
                [module_ids]
            )
            print(f'Module {module_name} installed successfully')
        else:
            print(f'Module {module_name} not found')
    else:
        print('Authentication failed')
except Exception as e:
    print(f'Error installing module: {e}')
"
    
    print_success "Proceso de instalación iniciado"
}

# Verificar instalación
verify_installation() {
    print_status "Verificando instalación..."
    
    # Esperar a que la instalación se complete
    sleep 30
    
    # Verificar logs de Odoo
    print_status "Últimas líneas del log de Odoo:"
    docker-compose logs odoo --tail=20
    
    # Verificar que el módulo esté instalado
    docker-compose exec -T odoo python -c "
import xmlrpc.client

try:
    url = 'http://localhost:8069'
    db_name = 'odoo17'
    admin_password = 'admin'
    module_name = 'inmoser_service_order'
    
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db_name, 'admin', admin_password, {})
    
    if uid:
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        # Verificar estado del módulo
        module_info = models.execute_kw(db_name, uid, admin_password,
            'ir.module.module', 'search_read',
            [[['name', '=', module_name]]],
            {'fields': ['name', 'state']}
        )
        
        if module_info:
            print(f'Module status: {module_info[0][\"state\"]}')
        else:
            print('Module not found in database')
    else:
        print('Authentication failed')
except Exception as e:
    print(f'Error checking module: {e}')
"
}

# Función principal
main() {
    echo "=============================================="
    echo "  INICIANDO PROCESO COMPLETO DE REINSTALACIÓN "
    echo "=============================================="
    
    # Verificar Docker
    check_docker
    
    # Limpieza profunda
    clean_docker
    
    # Crear estructura
    create_directories
    
    # Crear configuración
    create_odoo_config
    create_docker_compose
    
    # Copiar módulo personalizado
    copy_custom_module
    
    # Iniciar contenedores
    start_containers
    
    # Crear base de datos
    create_database
    
    # Instalar módulo
    install_custom_module
    
    # Verificar instalación
    verify_installation
    
    echo "=============================================="
    echo "            INSTALACIÓN COMPLETADA            "
    echo "=============================================="
    echo ""
    echo "✅ Odoo 17 está ejecutándose en: http://localhost:8069"
    echo "📊 Usuario: admin"
    echo "🔑 Contraseña: admin"
    echo "📦 Base de datos: odoo17"
    echo "⚙️  Módulo personalizado: inmoser_service_order"
    echo ""
    echo "Para ver los logs: cd /opt/odoo17 && docker-compose logs -f"
    echo "Para detener los servicios: cd /opt/odoo17 && docker-compose down"
    echo ""
}

# Ejecutar función principal
main "$@"

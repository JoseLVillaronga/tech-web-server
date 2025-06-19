#!/bin/bash

# Tech Web Server - Instalador de Servicio Systemd
# Instala el servidor web como servicio del sistema

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con colores
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

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ] || [ ! -f ".env" ]; then
    print_error "Este script debe ejecutarse desde el directorio raíz del proyecto tech-web-server"
    print_error "Asegúrate de que existan los archivos main.py y .env"
    exit 1
fi

# Obtener información del sistema
CURRENT_USER=$(whoami)
CURRENT_DIR=$(pwd)
SERVICE_NAME="tech-web-server"
PYTHON_PATH=$(which python3)

print_status "Configuración del servicio:"
echo "  Usuario: $CURRENT_USER"
echo "  Directorio: $CURRENT_DIR"
echo "  Python: $PYTHON_PATH"
echo "  Servicio: $SERVICE_NAME"
echo ""

# Verificar que el usuario puede usar sudo
print_status "Verificando permisos de sudo..."
if ! sudo -n true 2>/dev/null; then
    print_error "Este script requiere permisos de sudo sin contraseña"
    print_error "Configura sudo para tu usuario o ejecuta: sudo visudo"
    exit 1
fi
print_success "Permisos de sudo verificados"

# Verificar que existe el entorno virtual
if [ ! -d "venv" ]; then
    print_error "No se encontró el entorno virtual en ./venv"
    print_error "Ejecuta primero: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi
print_success "Entorno virtual encontrado"

# Verificar que las dependencias están instaladas
print_status "Verificando dependencias..."
source venv/bin/activate
if ! python -c "import aiohttp, motor, pymongo" 2>/dev/null; then
    print_error "Faltan dependencias. Ejecuta: pip install -r requirements.txt"
    exit 1
fi
deactivate
print_success "Dependencias verificadas"

# Crear el archivo de servicio systemd
print_status "Creando archivo de servicio systemd..."

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Tech Web Server - Alternative to Apache2
Documentation=https://github.com/user/tech-web-server
After=network.target
Wants=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin
ExecStart=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/main.py
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=10

# Límites de recursos
LimitNOFILE=65536
LimitNPROC=4096

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=tech-web-server

[Install]
WantedBy=multi-user.target
EOF

print_success "Archivo de servicio creado: $SERVICE_FILE"

# Recargar systemd
print_status "Recargando configuración de systemd..."
sudo systemctl daemon-reload
print_success "Configuración de systemd recargada"

# Habilitar el servicio
print_status "Habilitando servicio para inicio automático..."
sudo systemctl enable "$SERVICE_NAME"
print_success "Servicio habilitado para inicio automático"

# Mostrar información del servicio
print_status "Información del servicio instalado:"
echo ""
echo "📋 Comandos útiles:"
echo "  Iniciar servicio:    sudo systemctl start $SERVICE_NAME"
echo "  Detener servicio:    sudo systemctl stop $SERVICE_NAME"
echo "  Reiniciar servicio:  sudo systemctl restart $SERVICE_NAME"
echo "  Estado del servicio: sudo systemctl status $SERVICE_NAME"
echo "  Ver logs:            sudo journalctl -u $SERVICE_NAME -f"
echo "  Ver logs recientes:  sudo journalctl -u $SERVICE_NAME --since '1 hour ago'"
echo ""

# Preguntar si iniciar el servicio ahora
echo -n "¿Deseas iniciar el servicio ahora? (y/N): "
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    print_status "Iniciando servicio..."
    sudo systemctl start "$SERVICE_NAME"
    
    # Esperar un momento y verificar el estado
    sleep 2
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "¡Servicio iniciado correctamente!"
        
        # Mostrar información de los puertos
        source .env 2>/dev/null || true
        HTTP_PORT=${DEFAULT_HTTP_PORT:-3080}
        HTTPS_PORT=${DEFAULT_HTTPS_PORT:-3453}
        DASHBOARD_PORT=${DASHBOARD_PORT:-8000}
        
        echo ""
        echo "🌐 Servicios disponibles:"
        echo "  HTTP:      http://localhost:$HTTP_PORT"
        echo "  HTTPS:     https://localhost:$HTTPS_PORT"
        echo "  Dashboard: http://localhost:$DASHBOARD_PORT"
        echo ""
        
        # Mostrar estado del servicio
        print_status "Estado actual del servicio:"
        sudo systemctl status "$SERVICE_NAME" --no-pager -l
        
    else
        print_error "Error al iniciar el servicio"
        print_status "Verificando logs de error..."
        sudo journalctl -u "$SERVICE_NAME" --since '1 minute ago' --no-pager
        exit 1
    fi
else
    print_warning "Servicio instalado pero no iniciado"
    print_status "Para iniciarlo manualmente: sudo systemctl start $SERVICE_NAME"
fi

echo ""
print_success "🎉 Instalación completada exitosamente!"
print_status "El servicio $SERVICE_NAME está listo para usar"

# Mostrar información adicional
echo ""
echo "📝 Notas importantes:"
echo "  • El servicio se ejecuta como usuario: $CURRENT_USER"
echo "  • Directorio de trabajo: $CURRENT_DIR"
echo "  • El servicio se reinicia automáticamente si falla"
echo "  • Los logs se guardan en el journal del sistema"
echo "  • Para desinstalar: sudo systemctl stop $SERVICE_NAME && sudo systemctl disable $SERVICE_NAME && sudo rm $SERVICE_FILE"
echo ""

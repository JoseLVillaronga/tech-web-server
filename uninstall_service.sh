#!/bin/bash

# Tech Web Server - Desinstalador de Servicio Systemd
# Desinstala el servicio del sistema

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

SERVICE_NAME="tech-web-server"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

print_status "Desinstalando servicio: $SERVICE_NAME"
echo ""

# Verificar que el usuario puede usar sudo
print_status "Verificando permisos de sudo..."
if ! sudo -n true 2>/dev/null; then
    print_error "Este script requiere permisos de sudo sin contraseña"
    exit 1
fi
print_success "Permisos de sudo verificados"

# Verificar si el servicio existe
if [ ! -f "$SERVICE_FILE" ]; then
    print_warning "El servicio $SERVICE_NAME no está instalado"
    exit 0
fi

# Mostrar estado actual del servicio
print_status "Estado actual del servicio:"
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "  Estado: ACTIVO (ejecutándose)"
    SERVICE_RUNNING=true
else
    echo "  Estado: INACTIVO"
    SERVICE_RUNNING=false
fi

if sudo systemctl is-enabled --quiet "$SERVICE_NAME"; then
    echo "  Inicio automático: HABILITADO"
    SERVICE_ENABLED=true
else
    echo "  Inicio automático: DESHABILITADO"
    SERVICE_ENABLED=false
fi

echo ""

# Confirmar desinstalación
echo -n "¿Estás seguro de que deseas desinstalar el servicio $SERVICE_NAME? (y/N): "
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    print_status "Desinstalación cancelada"
    exit 0
fi

echo ""

# Detener el servicio si está ejecutándose
if [ "$SERVICE_RUNNING" = true ]; then
    print_status "Deteniendo servicio..."
    sudo systemctl stop "$SERVICE_NAME"
    print_success "Servicio detenido"
fi

# Deshabilitar el servicio si está habilitado
if [ "$SERVICE_ENABLED" = true ]; then
    print_status "Deshabilitando inicio automático..."
    sudo systemctl disable "$SERVICE_NAME"
    print_success "Inicio automático deshabilitado"
fi

# Eliminar el archivo de servicio
print_status "Eliminando archivo de servicio..."
sudo rm -f "$SERVICE_FILE"
print_success "Archivo de servicio eliminado: $SERVICE_FILE"

# Recargar systemd
print_status "Recargando configuración de systemd..."
sudo systemctl daemon-reload
print_success "Configuración de systemd recargada"

# Limpiar cache de systemd
sudo systemctl reset-failed "$SERVICE_NAME" 2>/dev/null || true

echo ""
print_success "🎉 Desinstalación completada exitosamente!"
print_status "El servicio $SERVICE_NAME ha sido completamente eliminado del sistema"

echo ""
echo "📝 Notas:"
echo "  • El servicio ya no se iniciará automáticamente"
echo "  • Los archivos del proyecto no han sido eliminados"
echo "  • Para reinstalar, ejecuta: ./install_service.sh"
echo ""

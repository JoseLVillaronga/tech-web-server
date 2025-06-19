#!/bin/bash

# Tech Web Server - Gestor de Servicio
# Script para gestionar fácilmente el servicio systemd

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SERVICE_NAME="tech-web-server"

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

print_header() {
    echo -e "${CYAN}$1${NC}"
}

# Función para mostrar el estado del servicio
show_status() {
    print_header "📊 Estado del Servicio $SERVICE_NAME"
    echo ""
    
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "  Estado: ${GREEN}ACTIVO${NC} (ejecutándose)"
    else
        echo -e "  Estado: ${RED}INACTIVO${NC}"
    fi
    
    if sudo systemctl is-enabled --quiet "$SERVICE_NAME"; then
        echo -e "  Inicio automático: ${GREEN}HABILITADO${NC}"
    else
        echo -e "  Inicio automático: ${YELLOW}DESHABILITADO${NC}"
    fi
    
    echo ""
    sudo systemctl status "$SERVICE_NAME" --no-pager -l || true
}

# Función para mostrar logs
show_logs() {
    local lines=${1:-50}
    print_header "📋 Logs del Servicio (últimas $lines líneas)"
    echo ""
    sudo journalctl -u "$SERVICE_NAME" -n "$lines" --no-pager
}

# Función para seguir logs en tiempo real
follow_logs() {
    print_header "📋 Logs en Tiempo Real (Ctrl+C para salir)"
    echo ""
    sudo journalctl -u "$SERVICE_NAME" -f
}

# Función para mostrar información de puertos
show_ports() {
    print_header "🌐 Información de Puertos"
    echo ""
    
    if [ -f ".env" ]; then
        source .env 2>/dev/null || true
        HTTP_PORT=${DEFAULT_HTTP_PORT:-3080}
        HTTPS_PORT=${DEFAULT_HTTPS_PORT:-3453}
        DASHBOARD_PORT=${DASHBOARD_PORT:-8000}
        
        echo "  HTTP:      http://localhost:$HTTP_PORT"
        echo "  HTTPS:     https://localhost:$HTTPS_PORT"
        echo "  Dashboard: http://localhost:$DASHBOARD_PORT"
    else
        print_warning "Archivo .env no encontrado"
    fi
    echo ""
}

# Función para mostrar ayuda
show_help() {
    print_header "🔧 Tech Web Server - Gestor de Servicio"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo "  start      - Iniciar el servicio"
    echo "  stop       - Detener el servicio"
    echo "  restart    - Reiniciar el servicio"
    echo "  reload     - Recargar configuración del servicio"
    echo "  status     - Mostrar estado del servicio"
    echo "  enable     - Habilitar inicio automático"
    echo "  disable    - Deshabilitar inicio automático"
    echo "  logs [N]   - Mostrar logs (N líneas, por defecto 50)"
    echo "  follow     - Seguir logs en tiempo real"
    echo "  ports      - Mostrar información de puertos"
    echo "  install    - Instalar servicio systemd"
    echo "  uninstall  - Desinstalar servicio systemd"
    echo "  help       - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 start"
    echo "  $0 logs 100"
    echo "  $0 follow"
    echo ""
}

# Verificar permisos de sudo para comandos que lo requieren
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        print_error "Este comando requiere permisos de sudo"
        exit 1
    fi
}

# Procesar comando
case "${1:-help}" in
    "start")
        check_sudo
        print_status "Iniciando servicio $SERVICE_NAME..."
        sudo systemctl start "$SERVICE_NAME"
        if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
            print_success "Servicio iniciado correctamente"
            show_ports
        else
            print_error "Error al iniciar el servicio"
            show_logs 20
            exit 1
        fi
        ;;
        
    "stop")
        check_sudo
        print_status "Deteniendo servicio $SERVICE_NAME..."
        sudo systemctl stop "$SERVICE_NAME"
        print_success "Servicio detenido"
        ;;
        
    "restart")
        check_sudo
        print_status "Reiniciando servicio $SERVICE_NAME..."
        sudo systemctl restart "$SERVICE_NAME"
        if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
            print_success "Servicio reiniciado correctamente"
            show_ports
        else
            print_error "Error al reiniciar el servicio"
            show_logs 20
            exit 1
        fi
        ;;
        
    "reload")
        check_sudo
        print_status "Recargando configuración del servicio $SERVICE_NAME..."
        sudo systemctl reload-or-restart "$SERVICE_NAME"
        print_success "Configuración recargada"
        ;;
        
    "status")
        check_sudo
        show_status
        ;;
        
    "enable")
        check_sudo
        print_status "Habilitando inicio automático para $SERVICE_NAME..."
        sudo systemctl enable "$SERVICE_NAME"
        print_success "Inicio automático habilitado"
        ;;
        
    "disable")
        check_sudo
        print_status "Deshabilitando inicio automático para $SERVICE_NAME..."
        sudo systemctl disable "$SERVICE_NAME"
        print_success "Inicio automático deshabilitado"
        ;;
        
    "logs")
        check_sudo
        lines=${2:-50}
        show_logs "$lines"
        ;;
        
    "follow")
        check_sudo
        follow_logs
        ;;
        
    "ports")
        show_ports
        ;;
        
    "install")
        if [ -f "install_service.sh" ]; then
            ./install_service.sh
        else
            print_error "Script install_service.sh no encontrado"
            exit 1
        fi
        ;;
        
    "uninstall")
        if [ -f "uninstall_service.sh" ]; then
            ./uninstall_service.sh
        else
            print_error "Script uninstall_service.sh no encontrado"
            exit 1
        fi
        ;;
        
    "help"|"-h"|"--help")
        show_help
        ;;
        
    *)
        print_error "Comando desconocido: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

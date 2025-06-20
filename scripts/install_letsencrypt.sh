#!/bin/bash
# Script de instalación para Let's Encrypt Manager
# Instala dependencias, configura cron y prepara el entorno

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Detectar directorio del proyecto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS_DIR="$PROJECT_DIR/scripts"
LOGS_DIR="$PROJECT_DIR/logs"
CRON_DIR="$PROJECT_DIR/cron"

log "🚀 Instalando Let's Encrypt Manager"
log "📁 Directorio del proyecto: $PROJECT_DIR"

# Verificar que estamos en el directorio correcto
if [[ ! -f "$PROJECT_DIR/main.py" ]]; then
    error "No se encontró main.py. ¿Estás en el directorio correcto del proyecto?"
    exit 1
fi

# Crear directorios necesarios
log "📁 Creando directorios..."
mkdir -p "$LOGS_DIR"
mkdir -p "$PROJECT_DIR/ssl/certs"

# Verificar Python y pip
log "🐍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    error "Python3 no está instalado"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    error "pip3 no está instalado"
    exit 1
fi

# Instalar dependencias Python
log "📦 Instalando dependencias Python..."
pip3 install --user cryptography psutil pyyaml

# Instalar certbot
log "🔐 Instalando certbot..."
if ! command -v certbot &> /dev/null; then
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        sudo apt-get update
        sudo apt-get install -y certbot
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum install -y certbot
    elif command -v dnf &> /dev/null; then
        # Fedora
        sudo dnf install -y certbot
    else
        warn "No se pudo instalar certbot automáticamente"
        warn "Instala manualmente: https://certbot.eff.org/instructions"
    fi
else
    log "✅ Certbot ya está instalado"
fi

# Función para instalar plugin DNS
install_dns_plugin() {
    local provider=$1
    local plugin_name=$2
    
    log "🔌 Instalando plugin DNS para $provider..."
    
    if pip3 show "$plugin_name" &> /dev/null; then
        log "✅ Plugin $plugin_name ya está instalado"
    else
        pip3 install --user "$plugin_name"
        log "✅ Plugin $plugin_name instalado"
    fi
}

# Preguntar por proveedor DNS
echo ""
echo "🌐 Selecciona tu proveedor DNS:"
echo "1) Cloudflare"
echo "2) AWS Route53"
echo "3) DigitalOcean"
echo "4) Namecheap"
echo "5) Saltar instalación de plugins DNS"

read -p "Opción (1-5): " dns_choice

case $dns_choice in
    1)
        install_dns_plugin "Cloudflare" "certbot-dns-cloudflare"
        DNS_PROVIDER="cloudflare"
        ;;
    2)
        install_dns_plugin "AWS Route53" "certbot-dns-route53"
        DNS_PROVIDER="route53"
        ;;
    3)
        install_dns_plugin "DigitalOcean" "certbot-dns-digitalocean"
        DNS_PROVIDER="digitalocean"
        ;;
    4)
        install_dns_plugin "Namecheap" "certbot-dns-namecheap"
        DNS_PROVIDER="namecheap"
        ;;
    5)
        log "⏭️  Saltando instalación de plugins DNS"
        DNS_PROVIDER="cloudflare"
        ;;
    *)
        warn "Opción inválida, usando Cloudflare por defecto"
        DNS_PROVIDER="cloudflare"
        ;;
esac

# Hacer scripts ejecutables
log "🔧 Configurando permisos..."
chmod +x "$SCRIPTS_DIR"/*.py
chmod +x "$SCRIPTS_DIR"/*.sh

# Configurar cron
log "⏰ Configurando cron..."

# Actualizar rutas en archivo cron
CRON_FILE="$CRON_DIR/letsencrypt.cron"
TEMP_CRON="/tmp/letsencrypt_temp.cron"

# Reemplazar rutas en archivo cron
sed "s|/home/sloch/tech_web_server|$PROJECT_DIR|g" "$CRON_FILE" > "$TEMP_CRON"
sed -i "s|--dns-provider cloudflare|--dns-provider $DNS_PROVIDER|g" "$TEMP_CRON"

# Instalar cron
if crontab -l &> /dev/null; then
    # Backup del crontab actual
    crontab -l > "$LOGS_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
    log "📋 Backup del crontab actual guardado"
    
    # Agregar nuevas entradas (evitar duplicados)
    (crontab -l 2>/dev/null | grep -v "letsencrypt_manager.py"; cat "$TEMP_CRON") | crontab -
else
    # Instalar crontab nuevo
    crontab "$TEMP_CRON"
fi

rm "$TEMP_CRON"
log "✅ Cron configurado"

# Crear archivo de configuración de credenciales DNS (ejemplo)
if [[ "$DNS_PROVIDER" == "cloudflare" ]]; then
    CREDS_FILE="/etc/letsencrypt/cloudflare.ini"
    if [[ ! -f "$CREDS_FILE" ]]; then
        log "📝 Creando archivo de credenciales de ejemplo..."
        sudo mkdir -p /etc/letsencrypt
        sudo tee "$CREDS_FILE" > /dev/null << EOF
# Credenciales de Cloudflare para Let's Encrypt
# Obtén tu API token en: https://dash.cloudflare.com/profile/api-tokens
# Permisos necesarios: Zone:DNS:Edit, Zone:Zone:Read

dns_cloudflare_api_token = YOUR_CLOUDFLARE_API_TOKEN_HERE
EOF
        sudo chmod 600 "$CREDS_FILE"
        warn "⚠️  Configura tus credenciales en: $CREDS_FILE"
    fi
fi

# Probar configuración
log "🧪 Probando configuración..."
if python3 "$SCRIPTS_DIR/letsencrypt_config.py"; then
    log "✅ Configuración válida"
else
    error "❌ Error en configuración"
    exit 1
fi

# Probar verificador de certificados
log "🔍 Probando verificador de certificados..."
if python3 "$SCRIPTS_DIR/cert_checker.py"; then
    log "✅ Verificador funcionando"
else
    warn "⚠️  Verificador con advertencias (normal si no hay certificados)"
fi

# Crear archivo de estado
STATUS_FILE="$LOGS_DIR/letsencrypt_install.status"
cat > "$STATUS_FILE" << EOF
# Estado de instalación Let's Encrypt Manager
INSTALL_DATE=$(date)
PROJECT_DIR=$PROJECT_DIR
DNS_PROVIDER=$DNS_PROVIDER
CERTBOT_VERSION=$(certbot --version 2>/dev/null || echo "No disponible")
PYTHON_VERSION=$(python3 --version)
EOF

log "📊 Estado guardado en: $STATUS_FILE"

echo ""
log "🎉 ¡Instalación completada!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Configura tus credenciales DNS en /etc/letsencrypt/${DNS_PROVIDER}.ini"
echo "2. Actualiza virtual_hosts.yaml con ssl_enabled: true"
echo "3. Prueba manualmente: $SCRIPTS_DIR/letsencrypt_manager.py --dry-run"
echo "4. El cron ejecutará automáticamente a las 2:00 AM diariamente"
echo ""
echo "📝 Logs en: $LOGS_DIR/"
echo "⚙️  Configuración cron: crontab -l"
echo ""
log "✅ ¡Let's Encrypt Manager listo para usar!"

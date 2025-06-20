#!/bin/bash
# Script para renovación manual de certificados Let's Encrypt
# Ejecutar cuando el script automático indique que se requiere renovación manual

DOMAIN="ogolfen.z-sur.com.ar"
EMAIL="jlvillaronga@z-sur.com.ar"
PROJECT_DIR="/home/jose/tech-web-server"

echo "🔐 Iniciando renovación manual de certificado para $DOMAIN"
echo "📧 Email: $EMAIL"
echo ""

# Verificar si certbot está instalado
if ! command -v certbot &> /dev/null; then
    echo "❌ Error: certbot no está instalado"
    echo "💡 Instalar con: sudo apt install certbot"
    exit 1
fi

echo "🚀 Ejecutando certbot para renovación manual..."
echo "⚠️  IMPORTANTE: Deberás agregar un registro TXT DNS cuando se solicite"
echo ""

# Ejecutar certbot con verificación DNS manual
sudo certbot certonly \
    --manual \
    --preferred-challenges dns \
    -d "$DOMAIN" \
    --agree-tos \
    --email "$EMAIL" \
    --no-eff-email \
    --force-renewal

# Verificar si el comando fue exitoso
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Certificado obtenido exitosamente"
    echo "🔄 Copiando certificados al proyecto..."
    
    # Ejecutar script de copia y reinicio
    cd "$PROJECT_DIR"
    python scripts/renew_manual_certs.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Proceso completado exitosamente"
        echo "🌐 El sitio web ahora tiene el certificado renovado"
    else
        echo "⚠️  Certificado obtenido pero error en la copia"
        echo "💡 Ejecutar manualmente: python scripts/renew_manual_certs.py"
    fi
else
    echo "❌ Error obteniendo el certificado"
    echo "💡 Verificar configuración DNS y volver a intentar"
    exit 1
fi

echo ""
echo "📋 Proceso de renovación manual completado"
echo "🔍 Verificar logs en: $PROJECT_DIR/logs/cert_renewal.log"

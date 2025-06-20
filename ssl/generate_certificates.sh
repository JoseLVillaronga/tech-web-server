#!/bin/bash

# 🔐 Generador de Certificados SSL Auto-firmados para Tech Web Server
# Este script genera certificados SSL para desarrollo y pruebas locales

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar mensajes
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar que estamos en el directorio correcto
if [ ! -d "certs" ] || [ ! -d "private" ]; then
    log_error "Este script debe ejecutarse desde el directorio ssl/"
    exit 1
fi

log_info "Generando certificados SSL auto-firmados para Tech Web Server..."

# Configuración de certificados
DAYS=365
KEY_SIZE=2048
COUNTRY="AR"
STATE="Buenos Aires"
CITY="Buenos Aires"
ORG="Tech-Support"
OU="Development"

# Dominios para los certificados
DEFAULT_DOMAINS=("localhost" "test.local" "intranet.local" "tech-support.local")

# Si se pasan parámetros, usar esos dominios; si no, usar los por defecto
if [ $# -gt 0 ]; then
    DOMAINS=("$@")
    log_info "Generando certificados para dominios específicos: ${DOMAINS[*]}"
else
    DOMAINS=("${DEFAULT_DOMAINS[@]}")
    log_info "Generando certificados para dominios por defecto"
fi

# Generar CA (Certificate Authority) privada
log_info "Generando Certificate Authority (CA) privada..."

# Clave privada de la CA
openssl genrsa -out private/ca-key.pem $KEY_SIZE

# Certificado de la CA
openssl req -new -x509 -days $DAYS -key private/ca-key.pem -out certs/ca-cert.pem \
    -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=Tech-Support CA"

log_success "Certificate Authority generada"

# Generar certificados para cada dominio
for domain in "${DOMAINS[@]}"; do
    log_info "Generando certificado para $domain..."
    
    # Clave privada del dominio
    openssl genrsa -out private/${domain}-key.pem $KEY_SIZE
    
    # Certificate Signing Request (CSR)
    openssl req -new -key private/${domain}-key.pem -out ${domain}.csr \
        -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=$domain"
    
    # Crear archivo de extensiones para SAN (Subject Alternative Names)
    # Diferentes configuraciones para dominios locales vs públicos
    if [[ "$domain" == *.local ]] || [[ "$domain" == "localhost" ]]; then
        # Configuración para dominios locales
        cat > ${domain}.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = $domain
DNS.2 = *.$domain
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
    else
        # Configuración para dominios públicos
        cat > ${domain}.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = $domain
DNS.2 = www.$domain
EOF
    fi

    # Generar certificado firmado por nuestra CA
    openssl x509 -req -in ${domain}.csr -CA certs/ca-cert.pem -CAkey private/ca-key.pem \
        -CAcreateserial -out certs/${domain}-cert.pem -days $DAYS \
        -extfile ${domain}.ext
    
    # Limpiar archivos temporales
    rm ${domain}.csr ${domain}.ext
    
    log_success "Certificado para $domain generado"
done

# Generar certificado wildcard solo si estamos usando dominios por defecto
if [ $# -eq 0 ]; then
    log_info "Generando certificado wildcard para *.local..."

    openssl genrsa -out private/wildcard-local-key.pem $KEY_SIZE

    openssl req -new -key private/wildcard-local-key.pem -out wildcard-local.csr \
        -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=*.local"

    cat > wildcard-local.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = *.local
DNS.2 = local
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

    openssl x509 -req -in wildcard-local.csr -CA certs/ca-cert.pem -CAkey private/ca-key.pem \
        -CAcreateserial -out certs/wildcard-local-cert.pem -days $DAYS \
        -extfile wildcard-local.ext

    rm wildcard-local.csr wildcard-local.ext

    log_success "Certificado wildcard generado"
fi

# Establecer permisos seguros
chmod 600 private/*.pem
chmod 644 certs/*.pem

# Mostrar información de los certificados generados
log_info "Certificados generados:"
echo ""
echo "📁 Estructura de archivos:"
echo "ssl/"
echo "├── certs/"
for cert in certs/*.pem; do
    echo "│   ├── $(basename $cert)"
done
echo "└── private/"
for key in private/*.pem; do
    echo "    ├── $(basename $key)"
done

echo ""
log_info "Información de certificados:"
for domain in "${DOMAINS[@]}"; do
    echo ""
    echo "🔐 $domain:"
    openssl x509 -in certs/${domain}-cert.pem -noout -subject -dates
done

echo ""
echo "🔐 Wildcard *.local:"
openssl x509 -in certs/wildcard-local-cert.pem -noout -subject -dates

echo ""
log_warning "IMPORTANTE: Estos son certificados auto-firmados para DESARROLLO"
log_warning "Los navegadores mostrarán advertencias de seguridad"
log_warning "Para producción, usar certificados de Let's Encrypt"

echo ""
log_success "¡Certificados SSL generados exitosamente!"
log_info "Para confiar en estos certificados, importa ssl/certs/ca-cert.pem en tu navegador"

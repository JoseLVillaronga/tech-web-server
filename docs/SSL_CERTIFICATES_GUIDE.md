# 🔐 Guía Completa de Certificados SSL - Tech Web Server

Esta guía explica cómo configurar, obtener y renovar certificados SSL Let's Encrypt para el Tech Web Server.

## 📋 Índice

1. [Configuración Inicial](#configuración-inicial)
2. [Obtener Certificado Manualmente](#obtener-certificado-manualmente)
3. [Sistema de Renovación Automática](#sistema-de-renovación-automática)
4. [Renovación Manual](#renovación-manual)
5. [Troubleshooting](#troubleshooting)

---

## 🔧 Configuración Inicial

### Prerrequisitos

1. **Certbot instalado:**
```bash
sudo apt update
sudo apt install certbot
```

2. **Dominio configurado:**
   - Dominio apuntando a tu servidor
   - Acceso a configuración DNS
   - Puerto 80/443 accesibles (o puertos personalizados)

3. **Virtual Host configurado:**
```yaml
# config/virtual_hosts.yaml
virtual_hosts:
  - domain: "tu-dominio.com"
    document_root: "public/tu-sitio"
    ssl_enabled: true
    letsencrypt_email: "tu-email@dominio.com"
```

---

## 🛠️ Obtener Certificado Manualmente

### Método 1: Verificación DNS (Recomendado para puertos no estándar)

Este método es ideal cuando usas puertos personalizados (como 3080/3453) en lugar de 80/443.

#### Paso 1: Ejecutar Certbot
```bash
sudo certbot certonly \
    --manual \
    --preferred-challenges dns \
    -d tu-dominio.com \
    --agree-tos \
    --email tu-email@dominio.com \
    --no-eff-email
```

#### Paso 2: Configurar DNS
Certbot te mostrará algo como:
```
Please deploy a DNS TXT record under the name:
_acme-challenge.tu-dominio.com

with the following value:
ABC123XYZ789...

Press Enter to Continue
```

#### Paso 3: Agregar registro TXT
En tu proveedor DNS, agrega:
- **Tipo:** TXT
- **Nombre:** `_acme-challenge.tu-dominio.com`
- **Valor:** `ABC123XYZ789...` (el que te dio certbot)
- **TTL:** 300 (5 minutos)

#### Paso 4: Verificar DNS
```bash
# Verificar que el registro DNS se propagó
dig TXT _acme-challenge.tu-dominio.com

# O usar nslookup
nslookup -type=TXT _acme-challenge.tu-dominio.com
```

#### Paso 5: Continuar con Certbot
Presiona Enter en certbot para continuar la verificación.

### Método 2: Verificación HTTP (Solo para puertos 80/443)

```bash
sudo certbot certonly \
    --standalone \
    -d tu-dominio.com \
    --agree-tos \
    --email tu-email@dominio.com \
    --no-eff-email
```

---

## 🤖 Sistema de Renovación Automática

### Configuración Actual

El sistema incluye verificación automática diaria:

#### Cron Job Configurado
```bash
# Verificar certificados SSL diariamente a las 6:00 AM
0 6 * * * cd /home/jose/tech-web-server && python scripts/renew_manual_certs.py >> logs/cert_renewal.log 2>&1
```

#### Script de Verificación: `scripts/renew_manual_certs.py`

**Funcionalidades:**
- ✅ Verifica expiración de certificados diariamente
- ✅ Solo actúa cuando quedan menos de 30 días
- ✅ Copia automáticamente certificados renovados
- ✅ Reinicia el servidor web automáticamente
- ✅ Genera logs detallados
- ✅ Envía notificaciones cuando se requiere acción manual

**Flujo de trabajo:**
1. **Verificación diaria:** Revisa si el certificado expira en < 30 días
2. **Detección automática:** Busca certificados renovados en `/etc/letsencrypt/live/`
3. **Copia automática:** Si encuentra certificado más nuevo, lo copia al proyecto
4. **Reinicio:** Reinicia el servidor web para aplicar cambios
5. **Notificación:** Informa si se requiere renovación manual

---

## 🔄 Renovación Manual

### Cuándo es Necesaria

- Cuando el script automático indica "ACCIÓN REQUERIDA"
- Certificados obtenidos con `--manual` (verificación DNS)
- Cuando quedan menos de 30 días de validez

### Script de Renovación: `scripts/manual_renewal.sh`

#### Uso Simple
```bash
cd /home/jose/tech-web-server
./scripts/manual_renewal.sh
```

#### Proceso Completo Manual

1. **Ejecutar renovación:**
```bash
sudo certbot certonly \
    --manual \
    --preferred-challenges dns \
    -d ogolfen.z-sur.com.ar \
    --agree-tos \
    --email jlvillaronga@z-sur.com.ar \
    --no-eff-email \
    --force-renewal
```

2. **Configurar DNS** (cuando certbot lo solicite)

3. **Copiar certificados al proyecto:**
```bash
cd /home/jose/tech-web-server
python scripts/renew_manual_certs.py
```

4. **Verificar funcionamiento:**
```bash
# Verificar estado del servidor
sudo service tech-web-server status

# Verificar certificado
openssl x509 -in ssl/certs/ogolfen.z-sur.com.ar-cert.pem -noout -dates
```

---

## 🔍 Verificación y Monitoreo

### Comandos Útiles

#### Verificar Estado del Certificado
```bash
# Ver información del certificado
python scripts/renew_manual_certs.py

# Ver logs de renovación
tail -f logs/cert_renewal.log

# Verificar certificados Let's Encrypt
sudo certbot certificates
```

#### Verificar Funcionamiento Web
```bash
# Probar HTTPS
curl -I https://tu-dominio.com

# Verificar certificado desde navegador
openssl s_client -connect tu-dominio.com:3453 -servername tu-dominio.com
```

#### Monitorear Logs
```bash
# Logs del servidor web
journalctl -u tech-web-server -f

# Logs de renovación
tail -f logs/cert_renewal.log

# Logs de cron
grep CRON /var/log/syslog | grep cert
```

---

## 🚨 Troubleshooting

### Problemas Comunes

#### 1. Error "Address already in use"
**Problema:** Puerto 443 ocupado por otro servicio
```bash
# Verificar qué usa el puerto
sudo netstat -tlnp | grep :443

# Detener Caddy si está corriendo
sudo systemctl stop caddy
```

#### 2. DNS no se propaga
**Problema:** Registro TXT no visible
```bash
# Verificar propagación DNS
dig TXT _acme-challenge.tu-dominio.com @8.8.8.8
dig TXT _acme-challenge.tu-dominio.com @1.1.1.1

# Esperar más tiempo (hasta 15 minutos)
```

#### 3. Certificado no se copia
**Problema:** Permisos o rutas incorrectas
```bash
# Verificar permisos Let's Encrypt
sudo ls -la /etc/letsencrypt/live/tu-dominio.com/

# Verificar permisos del proyecto
ls -la ssl/certs/
ls -la ssl/private/

# Corregir permisos si es necesario
sudo chown jose:jose ssl/certs/* ssl/private/*
```

#### 4. Servidor no reinicia
**Problema:** Error en el servicio systemd
```bash
# Verificar estado
sudo service tech-web-server status

# Ver logs detallados
journalctl -u tech-web-server -n 50

# Reinicio manual
sudo service tech-web-server restart
```

### Logs de Diagnóstico

#### Verificar Configuración
```bash
# Verificar virtual hosts
cat config/virtual_hosts.yaml

# Verificar configuración .env
grep -E "(SSL|GEOIP|CERT)" .env

# Verificar cron jobs
crontab -l | grep cert
```

#### Archivos de Log Importantes
- `logs/cert_renewal.log` - Logs de renovación automática
- `/var/log/letsencrypt/letsencrypt.log` - Logs de certbot
- `journalctl -u tech-web-server` - Logs del servidor web

---

## 📅 Cronología de Certificados

### Certificado Actual (ogolfen.z-sur.com.ar)
- **Obtenido:** 19 Jun 2025
- **Expira:** ~17 Sep 2025 (89 días)
- **Renovación automática:** ~17 Ago 2025 (30 días antes)
- **Método:** DNS manual

### Proceso de Renovación
1. **Día 59 antes de expirar:** Script detecta necesidad de renovación
2. **Notificación:** Log indica "ACCIÓN REQUERIDA"
3. **Renovación manual:** Ejecutar `./scripts/manual_renewal.sh`
4. **Copia automática:** Script copia nuevos certificados
5. **Reinicio:** Servidor web se reinicia automáticamente

---

## 📖 Ejemplo Práctico: Configuración ogolfen.z-sur.com.ar

### Proceso Completo Realizado (19 Jun 2025)

#### 1. Configuración Inicial
```yaml
# config/virtual_hosts.yaml
virtual_hosts:
  - domain: "ogolfen.z-sur.com.ar"
    document_root: "public"
    ssl_enabled: true
    php_version: "8.3"
    letsencrypt_email: "jlvillaronga@z-sur.com.ar"
```

#### 2. Obtención del Certificado
```bash
# Comando ejecutado
sudo certbot certonly \
    --manual \
    --preferred-challenges dns \
    -d ogolfen.z-sur.com.ar \
    --agree-tos \
    --email jlvillaronga@z-sur.com.ar \
    --no-eff-email

# Registro DNS agregado
_acme-challenge.ogolfen.z-sur.com.ar TXT "valor-proporcionado-por-certbot"
```

#### 3. Configuración del Servidor
```bash
# Certificados copiados a:
ssl/certs/ogolfen.z-sur.com.ar-cert.pem
ssl/private/ogolfen.z-sur.com.ar-key.pem

# Servidor reiniciado
sudo service tech-web-server restart
```

#### 4. Configuración de Renovación Automática
```bash
# Cron job agregado
0 6 * * * cd /home/jose/tech-web-server && python scripts/renew_manual_certs.py >> logs/cert_renewal.log 2>&1

# Scripts creados
scripts/renew_manual_certs.py    # Verificación automática
scripts/manual_renewal.sh        # Renovación manual
```

#### 5. Configuración GeoIP
```bash
# Base de datos extraída
gunzip -c GeoLite2-Country.mmdb.gz > data/geoip/GeoLite2-Country.mmdb

# Configuración .env actualizada
GEOIP_DATABASE_PATH=data/geoip/GeoLite2-Country.mmdb
```

### Resultado Final
- ✅ **HTTPS funcionando:** https://ogolfen.z-sur.com.ar
- ✅ **Certificado válido:** 89 días restantes
- ✅ **Renovación automática:** Configurada
- ✅ **Geolocalización:** Funcionando (AR en lugar de XX)
- ✅ **Dashboard:** Mostrando estadísticas correctas

---

## 🔗 Referencias

- [Documentación oficial Certbot](https://certbot.eff.org/)
- [Let's Encrypt DNS Challenge](https://letsencrypt.org/docs/challenge-types/#dns-01-challenge)
- [Tech Web Server Documentation](README.md)
- [GeoIP Configuration](README.md#geoip-opcional)

---

**Última actualización:** 19 Junio 2025
**Versión:** 1.0
**Autor:** Tech Web Server Team

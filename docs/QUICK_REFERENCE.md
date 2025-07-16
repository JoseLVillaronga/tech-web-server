# 🚀 Referencia Rápida - Tech Web Server

Comandos y procedimientos más comunes para administrar el Tech Web Server.

## 🔧 Gestión del Servidor

### Comandos Básicos
```bash
# Iniciar servidor
sudo service tech-web-server start

# Detener servidor
sudo service tech-web-server stop

# Reiniciar servidor
sudo service tech-web-server restart

# Ver estado
sudo service tech-web-server status

# Ver logs en tiempo real
journalctl -u tech-web-server -f
```

### Desarrollo Local
```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar en modo desarrollo
python main.py

# Verificar funcionamiento
curl http://localhost:3080
curl -k https://localhost:3453
```

## 🔐 Certificados SSL

### Verificar Estado
```bash
# Verificar certificado actual
python scripts/renew_manual_certs.py

# Ver logs de renovación
tail -f logs/cert_renewal.log

# Verificar certificados Let's Encrypt
sudo certbot certificates
```

### Renovación Manual
```bash
# Renovar certificado (proceso completo)
./scripts/manual_renewal.sh

# Solo verificar y copiar (si ya renovaste con certbot)
python scripts/renew_manual_certs.py
```

### Obtener Nuevo Certificado
```bash
# Para dominio nuevo con verificación DNS
sudo certbot certonly \
    --manual \
    --preferred-challenges dns \
    -d nuevo-dominio.com \
    --agree-tos \
    --email tu-email@dominio.com \
    --no-eff-email
```

## 📊 Dashboard y Logs

### Acceso al Dashboard
```bash
# Dashboard web
http://localhost:8000

# API de estadísticas
curl http://localhost:8000/api/stats

# Logs recientes
curl http://localhost:8000/api/logs
```

### MongoDB (Logs Históricos)
```bash
# Conectar a MongoDB
mongosh

# Ver logs recientes
use tech_web_server
db.access_logs.find().limit(10).sort({timestamp: -1})

# Buscar por IP
db.access_logs.find({ip: "192.168.1.100"})

# Buscar por país
db.access_logs.find({country_code: "AR"})
```

## 🌐 Virtual Hosts

### Configuración
```bash
# Editar virtual hosts
nano config/virtual_hosts.yaml

# Recargar configuración (reiniciar servidor)
sudo service tech-web-server restart
```

### Ejemplo Virtual Host
```yaml
virtual_hosts:
  - domain: "mi-sitio.com"
    document_root: "public/mi-sitio"
    ssl_enabled: true
    ssl_redirect: true
    php_enabled: true
    php_version: "8.3"
    letsencrypt_email: "admin@mi-sitio.com"
```

### Pruebas
```bash
# Probar virtual host específico
curl -H "Host: mi-sitio.com" http://localhost:3080

# Probar SSL
curl -k -H "Host: mi-sitio.com" https://localhost:3453
```

## 🐘 PHP-FPM

### Verificar Versiones Disponibles
```bash
# Ver sockets PHP disponibles
ls -la /run/php/php*-fpm.sock

# Verificar permisos (desarrollo)
sudo chmod 666 /run/php/php*.sock
```

### Probar PHP
```bash
# Crear archivo de prueba
echo "<?php phpinfo(); ?>" > public/test.php

# Probar ejecución
curl -H "Host: localhost" http://localhost:3080/test.php
```

## 🌍 GeoIP

### Configuración
```bash
# Verificar base de datos GeoIP
ls -la data/geoip/GeoLite2-Country.mmdb

# Actualizar configuración
nano .env
# GEOIP_DATABASE_PATH=data/geoip/GeoLite2-Country.mmdb
```

### Actualizar Base de Datos
```bash
# Descargar nueva base de datos (requiere cuenta MaxMind)
# Extraer y reemplazar
gunzip -c nueva-base.mmdb.gz > data/geoip/GeoLite2-Country.mmdb

# Reiniciar servidor
sudo service tech-web-server restart
```

## 🔍 Troubleshooting

### Problemas Comunes

#### Puerto ocupado
```bash
# Ver qué usa el puerto
sudo netstat -tlnp | grep :3080
sudo netstat -tlnp | grep :3453

# Matar proceso si es necesario
sudo kill -9 <PID>
```

#### Permisos PHP-FPM
```bash
# Verificar permisos sockets
ls -la /run/php/php*-fpm.sock

# Solución permanente (recomendada)
sudo usermod -a -G www-data $USER
newgrp www-data  # O reiniciar sesión

# Verificar que el usuario esté en el grupo
groups $USER | grep www-data

# Alternativa temporal (solo desarrollo)
sudo chmod 666 /run/php/php*.sock

# Verificar usuario/grupo
ps aux | grep php-fpm
```

#### Certificados SSL
```bash
# Verificar certificados del proyecto
ls -la ssl/certs/
ls -la ssl/private/

# Verificar certificados Let's Encrypt
sudo ls -la /etc/letsencrypt/live/

# Regenerar certificados auto-firmados
cd ssl && ./generate_certificates.sh
```

#### MongoDB
```bash
# Verificar conexión MongoDB
mongosh --eval "db.runCommand('ping')"

# Verificar base de datos
mongosh tech_web_server --eval "db.stats()"

# Ver logs de conexión
journalctl -u tech-web-server | grep -i mongo
```

## 📝 Archivos de Configuración

### Principales
- `.env` - Variables de entorno
- `config/virtual_hosts.yaml` - Configuración de dominios
- `ssl/certs/` - Certificados SSL
- `logs/` - Archivos de log

### Logs Importantes
- `logs/cert_renewal.log` - Renovación de certificados
- `journalctl -u tech-web-server` - Logs del servicio
- `/var/log/letsencrypt/letsencrypt.log` - Logs de certbot

## 🔄 Cron Jobs

### Ver Tareas Configuradas
```bash
# Ver cron del usuario
crontab -l

# Ver tarea de certificados
crontab -l | grep cert
```

### Configuración Actual
```bash
# Verificación diaria de certificados (6:00 AM)
0 6 * * * cd /home/jose/tech-web-server && python scripts/renew_manual_certs.py >> logs/cert_renewal.log 2>&1
```

## 🚀 Comandos de Emergencia

### Reinicio Completo
```bash
# Detener todo
sudo service tech-web-server stop
sudo pkill -f "python.*main.py"

# Limpiar puertos
sudo netstat -tlnp | grep -E ":(3080|3453|8000)"

# Reiniciar
sudo service tech-web-server start
```

### Backup Rápido
```bash
# Backup de configuración
tar -czf backup-config-$(date +%Y%m%d).tar.gz config/ .env ssl/certs/

# Backup de logs
tar -czf backup-logs-$(date +%Y%m%d).tar.gz logs/
```

---

**💡 Tip:** Guarda este archivo como referencia rápida para operaciones diarias del servidor.

**📚 Documentación completa:** [SSL_CERTIFICATES_GUIDE.md](SSL_CERTIFICATES_GUIDE.md)

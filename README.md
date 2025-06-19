# Tech Web Server

Servidor web alternativo a Apache2 construido con Python y asyncio para alta concurrencia.

## 🚀 Características Principales

- **Servidor asyncio** de alta concurrencia (40-300 conexiones simultáneas)
- **Virtual hosts** con configuración independiente
- **Soporte PHP-FPM** con múltiples versiones
- **Certificados SSL/TLS** (Let's Encrypt)
- **Logging avanzado** con geolocalización
- **Dashboard web** de administración
- **Compresión** gzip/brotli
- **Seguridad** integrada

## 📋 Estado del Desarrollo

### ✅ Completado

#### 1. Servidor Web Básico
- [x] Servidor asyncio en puertos personalizables (3080/3453)
- [x] Sistema de configuración (.env + virtual_hosts.yaml)
- [x] Servir archivos estáticos (HTML, CSS, JS, imágenes)
- [x] Detección automática de tipos MIME
- [x] Validación de rutas y seguridad básica

#### 2. Virtual Hosts
- [x] Configuración por dominio
- [x] Document root independiente por virtual host
- [x] Detección automática por header Host
- [x] Soporte para múltiples dominios

#### 3. Integración PHP-FPM
- [x] Cliente FastCGI personalizado
- [x] Soporte para PHP 7.1, 7.4, 8.2, 8.3, 8.4
- [x] Configuración de versión PHP por virtual host
- [x] Parámetros CGI completos
- [x] Manejo de headers HTTP
- [x] Ejecución de archivos PHP

#### 4. Sistema de Logging
- [x] Logging de accesos (IP, ruta, user-agent, país, timestamp)
- [x] Integración con MongoDB
- [x] Geolocalización con GeoLite2 (detección LOCAL/remota)
- [x] Logs habilitables/deshabilitables desde .env
- [x] Logging dual: memoria + MongoDB persistente
- [x] Índices optimizados para consultas rápidas

#### 5. Dashboard Web
- [x] Interfaz web de administración
- [x] Estadísticas en tiempo real (WebSocket)
- [x] Visualización de logs recientes
- [x] Estado de virtual hosts y PHP
- [x] Métricas de rendimiento
- [x] Distribución por países y tipos de request
- [x] Dashboard accesible remotamente (puerto 8000)
- [x] Logs históricos con filtros avanzados
- [x] Paginación inteligente con números de página
- [x] Filtros por fecha, IP, virtual host, status code
- [x] Búsqueda de texto en logs
- [x] Navegación directa por números de página
- [x] Diseño responsive adaptativo

#### 6. SSL/HTTPS
- [x] Certificados SSL auto-firmados
- [x] Soporte HTTPS con SNI (Server Name Indication)
- [x] Configuración SSL por virtual host
- [x] Redirección automática HTTP → HTTPS
- [x] Gestión de certificados SSL
- [ ] Integración Let's Encrypt para producción

### 🔄 En Desarrollo

#### 7. Funcionalidades Avanzadas
- [x] Compresión gzip/brotli
- [ ] Rate limiting
- [ ] Headers de seguridad avanzados
- [ ] Proxy reverso básico
- [ ] WebSocket support

## 🎯 Estado Actual del Sistema

### ✅ **Sistema Completamente Funcional**

El servidor web está **100% operativo** con todas las funcionalidades principales implementadas:

- **🚀 Servidor Web**: Asyncio de alta concurrencia (hasta 300 conexiones)
- **🐘 PHP-FPM**: Soporte completo para múltiples versiones (7.1, 7.4, 8.2, 8.3, 8.4)
- **🌐 Virtual Hosts**: Configuración independiente por dominio
- **🔐 SSL/HTTPS**: Certificados auto-firmados con redirección automática
- **📊 Dashboard**: Interfaz web con estadísticas y paginación inteligente
- **📝 Logging**: Sistema dual (memoria + MongoDB) con geolocalización
- **🗄️ MongoDB**: Base de datos persistente con índices optimizados
- **🗜️ Compresión**: Gzip/Brotli habilitado
- **🔒 Seguridad**: Validación de rutas y headers de seguridad

### 🌟 **Características Destacadas**

- **SSL/HTTPS Completo**: Certificados auto-firmados con redirección automática
- **Dashboard Avanzado**: Paginación inteligente con números de página
- **Logging Inteligente**: Detecta geolocalización (LOCAL/remota) y guarda en MongoDB
- **Dashboard Remoto**: Accesible desde cualquier IP en puerto 8000
- **PHP Flexible**: Cada virtual host puede usar diferente versión de PHP
- **Estadísticas Avanzadas**: Distribución por países, tipos de request, códigos de estado
- **Filtros Históricos**: Búsqueda avanzada en logs con múltiples criterios
- **Índices Optimizados**: Consultas rápidas en MongoDB para análisis histórico

### 📊 **Dashboard Features**

- **🎯 Paginación Inteligente**: Números de página adaptativos con lógica inteligente
- **🔍 Filtros Avanzados**: Por fecha, IP, virtual host, status code, método HTTP
- **📱 Responsive Design**: Se adapta perfectamente a móviles y tablets
- **⚡ Tiempo Real**: WebSocket para estadísticas en vivo
- **📈 Métricas Visuales**: Gráficos y estadísticas de rendimiento
- **🌍 Geolocalización**: Distribución de requests por países

## 🛠️ Instalación y Uso

### Requisitos
- Python 3.12+
- PHP-FPM (versiones 7.1, 7.4, 8.2, 8.3, 8.4)
- MongoDB (opcional, para logging)

### Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd tech-web-server
```

2. **Crear entorno virtual**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar permisos PHP-FPM** (temporal para desarrollo)
```bash
sudo chmod 666 /run/php/php*.sock
```

5. **Ejecutar el servidor**
```bash
python main.py
```

### Configuración

#### Archivo .env
```env
# Servidor
DEFAULT_HTTP_PORT=3080
DEFAULT_HTTPS_PORT=3453
MAX_CONCURRENT_CONNECTIONS=300

# Dashboard
PORT=8000
DASHBOARD_BIND_IP=0.0.0.0

# Logging
LOGS=true
LOG_FILE_PATH=/var/log/webserver/access.log

# MongoDB (para logging persistente)
mongo_host=localhost
mongo_port=27017
mongo_db=tech_web_server
mongo_user=
mongo_pass=

# GeoIP (opcional)
GEOIP_DB_PATH=/var/lib/geoip/GeoLite2-Country.mmdb

# PHP-FPM
PHP_FPM_SOCKETS_71=/run/php/php7.1-fpm.sock
PHP_FPM_SOCKETS_74=/run/php/php7.4-fpm.sock
PHP_FPM_SOCKETS_82=/run/php/php8.2-fpm.sock
PHP_FPM_SOCKETS_83=/run/php/php8.3-fpm.sock
PHP_FPM_SOCKETS_84=/run/php/php8.4-fpm.sock
```

#### Virtual Hosts (config/virtual_hosts.yaml)
```yaml
virtual_hosts:
  - domain: "localhost"
    port: 3080
    document_root: "./public"
    ssl_enabled: true
    ssl_redirect: true
    php_enabled: true
    php_version: "8.3"
    php_pool: "www"

  - domain: "test.local"
    port: 3080
    document_root: "./public/test"
    ssl_enabled: true
    ssl_redirect: true
    php_enabled: true
    php_version: "7.4"
    php_pool: "www"
```

## 🧪 Pruebas

### Servidor funcionando
```bash
curl http://localhost:3080
```

### PHP funcionando
```bash
curl -H "Host: test.local" http://localhost:3080/version.php
```

### Virtual hosts
```bash
# localhost con PHP 8.3
curl -H "Host: localhost" http://localhost:3080/info.php

# test.local con PHP 7.4
curl -H "Host: test.local" http://localhost:3080/version.php
```

### SSL/HTTPS
```bash
# Probar redirección HTTP → HTTPS
curl -v -H "Host: localhost" http://localhost:3080/

# Acceso directo HTTPS (certificado auto-firmado)
curl -k -H "Host: localhost" https://localhost:3453/

# Verificar certificado SSL
openssl s_client -connect localhost:3453 -servername localhost
```

### Dashboard y Logging
```bash
# Acceder al dashboard
curl http://localhost:8000

# Ver estadísticas en tiempo real
curl http://localhost:8000/api/stats

# Ver logs recientes
curl http://localhost:8000/api/logs
```

### MongoDB (verificar logs)
```bash
# Conectar a MongoDB y ver logs
mongosh
use tech_web_server
db.access_logs.find().limit(5).sort({timestamp: -1})
```

## 📁 Estructura del Proyecto

```
tech-web-server/
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   └── config_manager.py      # Gestión de configuración
│   ├── server/
│   │   ├── __init__.py
│   │   └── web_server.py          # Servidor principal
│   ├── php_fpm/
│   │   ├── __init__.py
│   │   ├── fastcgi_client.py      # Cliente FastCGI
│   │   └── php_manager.py         # Gestor de PHP-FPM
│   ├── logging/
│   │   ├── __init__.py
│   │   ├── logger.py              # Sistema de logging
│   │   └── geoip_manager.py       # Geolocalización
│   ├── database/
│   │   ├── __init__.py
│   │   └── mongodb_client.py      # Cliente MongoDB
│   ├── dashboard/
│   │   ├── __init__.py
│   │   ├── dashboard_server.py    # Servidor dashboard
│   │   └── static/                # Archivos estáticos dashboard
│   ├── tls/
│   │   ├── __init__.py
│   │   └── ssl_manager.py         # Gestión de certificados SSL
│   └── utils/                     # (próximo)
├── config/
│   └── virtual_hosts.yaml         # Configuración virtual hosts
├── ssl/
│   ├── certs/                     # Certificados SSL
│   └── generate_certificates.sh   # Script generación certificados
├── public/
│   ├── index.html                 # Página principal
│   ├── info.php                   # Info PHP localhost
│   └── test/
│       ├── index.html             # Página test
│       └── version.php            # phpinfo() test
├── .env                           # Variables de entorno
├── .gitignore                     # Exclusiones Git
├── requirements.txt               # Dependencias Python
├── main.py                        # Punto de entrada
└── README.md                      # Este archivo
```

## 🔧 Desarrollo

### Próximos pasos
1. **SSL/TLS** con Let's Encrypt
2. **Rate limiting** y seguridad avanzada
3. **Optimizaciones de rendimiento**
4. **Métricas avanzadas**

### Commits importantes
- `0a69190` - Plataforma web completa con dashboard y logging
- `20a8ddc` - Soporte SSL/HTTPS completo con certificados
- `3bbb6bc` - Redirección automática HTTP → HTTPS
- `dc94aa0` - Paginación inteligente del dashboard

## 📚 Documentación Completa

### 🔧 Configuración y Administración
- [Configuración inicial](docs/setup.md)
- [Configuración de virtual hosts](docs/virtual-hosts.md)
- [Configuración SSL](docs/ssl-setup.md)
- [Sistema de logging](docs/logging-system.md)
- [Dashboard de administración](docs/dashboard.md)
- [Instalación como servicio](docs/service-installation.md)

### 🚀 Desarrollo y Mejores Prácticas ⭐
- [**Mejores Prácticas del Web Server**](docs/web-server-best-practices.md) - Lecciones aprendidas en campo
- [**Patrones JavaScript Validados**](docs/javascript-patterns-guide.md) - Código probado y optimizado
- [**Guía de Troubleshooting**](docs/troubleshooting-guide.md) - Soluciones a problemas comunes

> 💡 **Nota Importante:** La documentación de desarrollo está basada en **pruebas reales** con el sitio Tech-Support, donde se validó que nuestro web server es **más estricto que Apache2**, lo que resulta en **código de mayor calidad** y mejores prácticas de desarrollo.

## 📝 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🤝 Contribuciones

[Instrucciones para contribuir]

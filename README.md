# Tech Web Server
![ChatGPT Image 19 jun 2025, 22_11_08](https://github.com/user-attachments/assets/3445336e-fa5e-45e1-981b-07ee7960df5d)

Servidor web alternativo a Apache2 construido con Python y asyncio para alta concurrencia.

## 🚀 Características Principales

- **Servidor asyncio** de alta concurrencia (40-300 conexiones simultáneas)
- **Virtual hosts** con configuración independiente
- **Soporte PHP-FPM** con múltiples versiones
- **Rewrite Engine** para aplicaciones MVC (compatible con Apache .htaccess)
- **Certificados SSL/TLS** (Let's Encrypt)
- **Modo multi-puerto HTTP** para máximo rendimiento
- **Soporte proxy reverso** (Caddy, Nginx, Cloudflare)
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
- [x] Integración Let's Encrypt para producción
- [x] Renovación automática de certificados
- [x] Verificación DNS para puertos no estándar

#### 7. Rewrite Engine (URL Rewriting)
- [x] Motor de rewrite basado en configuración YAML
- [x] Soporte para patrones regex
- [x] Condiciones (file_not_exists, dir_not_exists)
- [x] Flags (QSA - Query String Append, L - Last)
- [x] Grupos capturados ($1, $2, etc.)
- [x] Configuración por virtual host
- [x] Compatible con aplicaciones MVC
- [x] Manejo de errores 404 personalizados
- [x] Integración con PHP-FPM

### 🔄 En Desarrollo

#### 7. Funcionalidades Avanzadas
- [x] Compresión gzip/brotli
- [x] Soporte proxy reverso (Caddy, Nginx, Cloudflare)
- [x] Detección de IP real del cliente
- [x] Geolocalización con IPs reales
- [x] Modo multi-puerto HTTP (SSL_ENABLED=false)
- [x] Routing inteligente por (Host, Port)
- [ ] Rate limiting
- [ ] Headers de seguridad avanzados
- [ ] WebSocket support

## 🎯 Estado Actual del Sistema

### ✅ **Sistema Completamente Funcional**

El servidor web está **100% operativo** con todas las funcionalidades principales implementadas:

- **🚀 Servidor Web**: Asyncio de alta concurrencia (hasta 300 conexiones)
- **🐘 PHP-FPM**: Soporte completo para múltiples versiones (7.1, 7.4, 8.2, 8.3, 8.4)
- **🌐 Virtual Hosts**: Configuración independiente por dominio
- **🔄 Rewrite Engine**: URL rewriting para aplicaciones MVC (compatible con Apache)
- **🔐 SSL/HTTPS**: Certificados auto-firmados con redirección automática
- **🔄 Proxy Reverso**: Compatible con Caddy, Nginx, Cloudflare (IPs reales)
- **📊 Dashboard**: Interfaz web con estadísticas y paginación inteligente
- **📝 Logging**: Sistema dual (memoria + MongoDB) con geolocalización
- **🗄️ MongoDB**: Base de datos persistente con índices optimizados
- **🗜️ Compresión**: Gzip/Brotli habilitado
- **🔒 Seguridad**: Validación de rutas y headers de seguridad

### 🌟 **Características Destacadas**

- **SSL/HTTPS Completo**: Certificados auto-firmados con redirección automática
- **Rewrite Engine**: URL rewriting para aplicaciones MVC (compatible con Apache)
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

4. **Crear archivos de configuración locales (Obligatorio)**
> ⚠️ `config/virtual_hosts.yaml` y `.env` están excluidos de Git (`.gitignore`) para proteger credenciales, dominios y rutas locales del servidor. Deben crearse a partir de sus plantillas antes de iniciar la aplicación:

```bash
cp .env.example .env
cp config/virtual_hosts.yaml.example config/virtual_hosts.yaml
```

5. **Configurar permisos PHP-FPM**
```bash
# Solución permanente (recomendada)
sudo usermod -a -G www-data $USER

# Luego reiniciar sesión o ejecutar:
newgrp www-data

# Alternativa temporal (solo para desarrollo)
sudo chmod 666 /run/php/php*.sock
```

6. **Ejecutar el servidor**
```bash
python main.py
```

### Configuración

#### Archivo .env
```env
# Servidor
SSL_ENABLED=true                     # true = SSL tradicional, false = Multi-puerto HTTP
DEFAULT_HTTP_PORT=3080
DEFAULT_HTTPS_PORT=3453
MAX_CONCURRENT_CONNECTIONS=300

# Dashboard
PORT=8000
DASHBOARD_BIND_IP=0.0.0.0

# Logging
LOGS=true
LOG_FILE_PATH=/var/log/webserver/access.log

# Proxy Reverso
PROXY_SUPPORT_ENABLED=true

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

#### Virtual Hosts (`config/virtual_hosts.yaml`)

El archivo `config/virtual_hosts.yaml` es **indispensable** para que el servidor inicie y enrute peticiones. Si no existe, créalo copiando la plantilla base:

```bash
cp config/virtual_hosts.yaml.example config/virtual_hosts.yaml
```

##### Referencia de Campos por Virtual Host

| Campo | Tipo | Obligatorio | Descripción |
| :--- | :--- | :---: | :--- |
| `domain` | `string` | Sí | Nombre de dominio exacto recibido en la cabecera HTTP `Host` (sin puerto). |
| `port` | `int` | Sí | Puerto HTTP del virtual host. Cuando `SSL_ENABLED=false` (modo multi-puerto detrás de Caddy/Nginx), el servidor abre un listener en cada puerto único y enruta por `(domain, port)`. |
| `document_root` | `string` | Sí | Ruta (preferentemente relativa al proyecto, ej. `./public/mi-sitio`) donde residen los archivos del sitio. |
| `ssl_enabled` | `bool` | Sí | `false` cuando el TLS lo termina un proxy reverso externo (Caddy); `true` para usar TLS interno del servidor. |
| `ssl_redirect` | `bool` | Sí | `true` para forzar redirección `301` de HTTP a HTTPS cuando `ssl_enabled: true`. |
| `php_enabled` | `bool` | Sí | `true` para procesar scripts `.php` mediante FastCGI (PHP-FPM); `false` para servir solo archivos estáticos. |
| `php_version` | `string` | Condicional | Versión de PHP-FPM a utilizar (`"7.1"`, `"7.4"`, `"8.2"`, `"8.3"`, `"8.4"`). Requerido si `php_enabled: true`. |
| `php_pool` | `string` | No | Nombre informativo del pool de PHP-FPM (por defecto `"www"`). |
| `rewrite_rules` | `list` | No | Lista ordenada de reglas de reescritura de URLs (ver ejemplo debajo). |

##### Ejemplo de `config/virtual_hosts.yaml`

```yaml
virtual_hosts:
  - domain: "localhost"
    port: 3080
    document_root: "./public"
    ssl_enabled: false
    ssl_redirect: false
    php_enabled: true
    php_version: "8.3"
    php_pool: "www"

  - domain: "app.example.com"
    port: 3083
    document_root: "./public/test"
    ssl_enabled: false
    ssl_redirect: false
    php_enabled: true
    php_version: "7.4"
    php_pool: "www"

    # Rewrite rules para aplicaciones MVC
    rewrite_rules:
      - pattern: "^(.*)$"
        target: "/index.php"
        query_string: "url=$1"
        conditions:
          - type: "file_not_exists"
          - type: "dir_not_exists"
        flags: ["QSA", "L"]
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

### Rewrite Engine (URL Rewriting)
```bash
# Probar ruta MVC que no existe como archivo
curl -v http://localhost:3080/usuarios/123
# Esperado: Se reescribe a /index.php?url=/usuarios/123

# Probar ruta con parámetros
curl -v "http://localhost:3080/servicios?foo=bar"
# Esperado: Se reescribe a /index.php?url=/servicios&foo=bar

# Probar ruta 404 personalizada
curl -v http://localhost:3080/ruta-no-existe
# Esperado: Se renderiza página 404 personalizada

# Probar que archivos estáticos se sirven normalmente
curl -I http://localhost:3080/public/style.css
# Esperado: Status 200 (no se reescribe)
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
│   ├── rewrite/
│   │   ├── __init__.py
│   │   ├── conditions.py          # Condiciones de rewrite
│   │   ├── rewrite_rule.py        # Reglas de rewrite
│   │   └── rewrite_engine.py      # Motor de rewrite
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
├── tests/
│   └── test_rewrite_engine.py     # Tests del rewrite engine
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
- **Nuevo** - Rewrite Engine para aplicaciones MVC (URL rewriting compatible con Apache)

## 📚 Documentación Completa

### 🔧 Configuración y Administración
- [Configuración inicial](docs/setup.md)
- [Configuración de virtual hosts](docs/virtual-hosts.md)
- [**🔄 Rewrite Engine (URL Rewriting)**](GUIA_PRUEBA_REWRITE.md) - Motor de rewrite para aplicaciones MVC
- [**🔐 Certificados SSL/Let's Encrypt**](docs/SSL_CERTIFICATES_GUIDE.md) - Guía completa de SSL
- [**🌐 Configuración Multi-Puerto**](docs/MULTI_PORT_CONFIGURATION.md) - Modo HTTP de alto rendimiento
- [**🔄 Soporte Proxy Reverso**](docs/REVERSE_PROXY_SUPPORT.md) - Caddy, Nginx, Cloudflare
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

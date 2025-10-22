# 🔧 ANÁLISIS DETALLADO DE MÓDULOS

## 1. Servidor Web Principal (`src/server/web_server.py`)

### Responsabilidades
- Manejo de conexiones HTTP asyncio
- Enrutamiento de requests a virtual hosts
- Servir archivos estáticos
- Delegación de archivos PHP a PHP-FPM
- Manejo de errores HTTP

### Métodos Clave

#### `handle_request(request)`
- Identifica virtual host por Host + Puerto
- Valida seguridad (directory traversal)
- Resuelve archivo solicitado
- Delega a PHP-FPM si es .php
- Sirve estático si no es PHP
- Registra en logging

#### `_get_real_client_ip(request)`
- Detecta IP real del cliente
- Soporta headers de proxy: X-Forwarded-For, X-Real-IP, CF-Connecting-IP
- Validación de IPs
- Fallback a IP directa

#### `_should_redirect_to_https(request, vhost)`
- Verifica si necesita redirección HTTP → HTTPS
- Configurable por virtual host

### Características
- ✅ Routing por (Host, Port) en modo multi-puerto
- ✅ Routing por Host en modo SSL
- ✅ Compresión gzip/brotli
- ✅ Detección de tipos MIME
- ✅ Manejo de index.html/index.php
- ✅ Logging de accesos

---

## 2. Gestor de Configuración (`src/config/config_manager.py`)

### Responsabilidades
- Carga variables de entorno (.env)
- Parsea configuración YAML
- Acceso centralizado a configuración
- Recarga en caliente

### Métodos Clave

#### `get(key, default=None)`
- Obtiene valor de configuración

#### `get_virtual_hosts()`
- Retorna lista de virtual hosts

#### `get_virtual_host_by_domain(domain)`
- Busca virtual host por dominio

#### `get_virtual_host_by_domain_and_port(domain, port)`
- Busca virtual host por dominio y puerto (multi-puerto)

#### `get_unique_http_ports()`
- Retorna puertos únicos para modo multi-puerto

### Configuraciones Gestionadas
- Puertos del servidor
- Configuración PHP-FPM
- Parámetros de logging
- Configuración SSL/TLS
- Configuración de seguridad

---

## 3. Cliente FastCGI (`src/php_fpm/fastcgi_client.py`)

### Responsabilidades
- Implementación del protocolo FastCGI
- Comunicación con sockets Unix de PHP-FPM
- Empaquetado/desempaquetado de mensajes
- Manejo de timeouts y errores

### Protocolo FastCGI Implementado
- `FCGI_BEGIN_REQUEST` - Inicio de request
- `FCGI_PARAMS` - Parámetros CGI
- `FCGI_STDIN` - Datos POST
- `FCGI_STDOUT` - Respuesta PHP
- `FCGI_STDERR` - Errores PHP
- `FCGI_END_REQUEST` - Fin de request

### Métodos Clave

#### `_pack_fcgi_record(req_type, req_id, content)`
- Empaqueta registro FastCGI con header

#### `_pack_params(params)`
- Empaqueta parámetros CGI

#### `_unpack_fcgi_record(data)`
- Desempaqueta registro FastCGI

#### `execute_php(script_path, params, post_data)`
- Ejecuta script PHP a través de FastCGI
- Retorna (stdout, stderr)

---

## 4. Gestor PHP (`src/php_fpm/php_manager.py`)

### Responsabilidades
- Gestión de múltiples versiones PHP
- Mapeo de versiones a sockets
- Construcción de parámetros FastCGI
- Parseo de respuestas PHP
- Manejo de headers HTTP

### Versiones Soportadas
- PHP 7.1 → `/run/php/php7.1-fpm.sock`
- PHP 7.4 → `/run/php/php7.4-fpm.sock`
- PHP 8.2 → `/run/php/php8.2-fpm.sock`
- PHP 8.3 → `/run/php/php8.3-fpm.sock`
- PHP 8.4 → `/run/php/php8.4-fpm.sock`

### Métodos Clave

#### `get_available_versions()`
- Retorna versiones PHP disponibles

#### `get_socket_for_version(version)`
- Obtiene socket para versión específica

#### `execute_php(script_path, vhost, request, post_data)`
- Ejecuta PHP con parámetros CGI completos

#### `_get_real_client_ip(request)`
- Detecta IP real del cliente

---

## 5. Cliente MongoDB (`src/database/mongodb_client.py`)

### Responsabilidades
- Conexión asíncrona a MongoDB
- Logging de accesos
- Creación de índices
- Consultas de logs históricos
- Fallback a memoria

### Métodos Clave

#### `connect()`
- Conecta a MongoDB
- Crea índices automáticamente

#### `log_access(ip, country, method, path, status, user_agent, response_time, virtual_host)`
- Registra acceso en MongoDB

#### `get_recent_logs(limit, virtual_host)`
- Obtiene logs recientes

#### `get_historical_logs(page, limit, filters)`
- Obtiene logs históricos con filtros

#### `get_stats()`
- Obtiene estadísticas agregadas

### Índices Creados
- timestamp (descendente)
- virtual_host
- ip
- Compuesto: (virtual_host, timestamp)

---

## 6. Dashboard (`src/dashboard/dashboard_server.py`)

### Responsabilidades
- Servidor web en puerto 8000
- API REST para estadísticas
- WebSocket para datos en tiempo real
- Interfaz HTML del dashboard
- Logs históricos con filtros

### Rutas API

#### GET `/api/stats`
- Estadísticas del servidor (uptime, requests, etc.)

#### GET `/api/virtual-hosts`
- Información de virtual hosts

#### GET `/api/php-status`
- Estado de versiones PHP

#### GET `/api/logs`
- Logs recientes

#### GET `/api/logs/historical`
- Logs históricos con paginación y filtros

#### GET `/api/logs/filter-options`
- Opciones disponibles para filtros

#### GET `/ws`
- WebSocket para estadísticas en tiempo real

### Características
- ✅ Paginación inteligente
- ✅ Filtros avanzados (fecha, IP, virtual host, status code)
- ✅ Búsqueda de texto
- ✅ Distribución por países
- ✅ Estadísticas en tiempo real
- ✅ Responsive design

---

## 7. Gestor SSL (`src/tls/ssl_manager.py`)

### Responsabilidades
- Gestión de certificados SSL
- Creación de contextos SSL
- Soporte SNI
- Carga de certificados

### Métodos Clave

#### `create_ssl_context(domain)`
- Crea contexto SSL para dominio

#### `get_ssl_context(domain)`
- Obtiene contexto SSL (con cache)

#### `is_ssl_available(domain)`
- Verifica disponibilidad de SSL

#### `load_certificate(domain)`
- Carga certificado y clave privada

### Configuración de Seguridad
- TLS 1.2 - 1.3
- Ciphers seguros (ECDHE+AESGCM, etc.)
- Deshabilitación de protocolos antiguos
- ECDH y DH configurados

---

## 8. Geolocalización (`src/utils/geoip.py`)

### Responsabilidades
- Detección de IPs locales vs remotas
- Geolocalización con GeoLite2
- Fallback inteligente

### Métodos Clave

#### `get_country(ip)`
- Obtiene código de país para IP

#### `is_local_ip(ip)`
- Verifica si IP es local

### Características
- ✅ Detección LOCAL para IPs privadas
- ✅ Soporte GeoLite2 (opcional)
- ✅ Fallback a "ZZ" si no disponible
- ✅ Cache de resultados

---

## 🔄 Flujo de Integración

```
Cliente HTTP
    ↓
web_server.handle_request()
    ├─ _get_real_client_ip()
    ├─ Identificar virtual host
    ├─ Validar seguridad
    ├─ ¿Es PHP?
    │   ├─ SÍ: php_manager.execute_php()
    │   │   └─ fastcgi_client.execute_php()
    │   └─ NO: Servir estático
    ├─ mongodb_client.log_access()
    └─ dashboard.update_stats()
```

---

## 📊 Estadísticas de Código

- **Líneas de código**: ~3000+
- **Módulos**: 8 principales
- **Clases**: 15+
- **Métodos**: 100+
- **Documentación**: 1000+ líneas

---

## 🎯 Calidad del Código

- ✅ Type hints completos
- ✅ Docstrings en métodos
- ✅ Manejo de excepciones
- ✅ Logging detallado
- ✅ Arquitectura modular
- ✅ Separación de responsabilidades


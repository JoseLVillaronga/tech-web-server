# Documentación Técnica - Tech Web Server

## Arquitectura General

Tech Web Server está construido con una arquitectura modular que separa las responsabilidades en diferentes componentes:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   HTTP Client   │───▶│  Web Server     │───▶│  PHP-FPM        │
│                 │    │  (asyncio)      │    │  (FastCGI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ Config Manager  │
                       │ Virtual Hosts   │
                       └─────────────────┘
```

## Componentes Principales

### 1. Servidor Web Principal (`src/server/web_server.py`)

**Clase:** `TechWebServer`

**Responsabilidades:**
- Manejo de conexiones HTTP asyncio
- Enrutamiento de requests a virtual hosts
- Servir archivos estáticos
- Delegación de archivos PHP a PHP-FPM
- Manejo de errores HTTP

**Flujo de procesamiento:**
1. Recibe request HTTP
2. Extrae header `Host` para identificar virtual host
3. Resuelve ruta del archivo solicitado
4. Valida seguridad (directory traversal)
5. Si es `.php` → delega a PHP-FPM
6. Si es estático → sirve directamente
7. Retorna respuesta HTTP

### 2. Gestor de Configuración (`src/config/config_manager.py`)

**Clase:** `ConfigManager`

**Responsabilidades:**
- Carga de variables de entorno desde `.env`
- Parseo de configuración de virtual hosts (YAML)
- Acceso centralizado a configuración
- Recarga de configuración en caliente

**Configuraciones gestionadas:**
- Puertos del servidor
- Configuración de PHP-FPM
- Parámetros de logging
- Configuración SSL/TLS
- Configuración de seguridad

### 3. Sistema PHP-FPM (`src/php_fpm/`)

#### Cliente FastCGI (`fastcgi_client.py`)

**Clase:** `FastCGIClient`

**Responsabilidades:**
- Implementación del protocolo FastCGI
- Comunicación con sockets Unix de PHP-FPM
- Empaquetado/desempaquetado de mensajes FastCGI
- Manejo de timeouts y errores

**Protocolo FastCGI implementado:**
- `FCGI_BEGIN_REQUEST` - Inicio de request
- `FCGI_PARAMS` - Parámetros CGI
- `FCGI_STDIN` - Datos POST
- `FCGI_STDOUT` - Respuesta PHP
- `FCGI_STDERR` - Errores PHP
- `FCGI_END_REQUEST` - Fin de request

#### Gestor PHP (`php_manager.py`)

**Clase:** `PHPManager`

**Responsabilidades:**
- Gestión de múltiples versiones PHP
- Mapeo de versiones a sockets
- Construcción de parámetros FastCGI
- Parseo de respuestas PHP
- Manejo de headers HTTP

**Versiones soportadas:**
- PHP 7.1 → `/run/php/php7.1-fpm.sock`
- PHP 7.4 → `/run/php/php7.4-fpm.sock`
- PHP 8.2 → `/run/php/php8.2-fpm.sock`
- PHP 8.3 → `/run/php/php8.3-fpm.sock`
- PHP 8.4 → `/run/php/php8.4-fpm.sock`

## Configuración de Virtual Hosts

### Estructura YAML

```yaml
virtual_hosts:
  - domain: "example.com"
    port: 3080
    document_root: "/path/to/files"
    ssl_enabled: false
    php_enabled: true
    php_version: "8.3"
    php_pool: "www"
```

### Parámetros

- **domain**: Dominio del virtual host
- **port**: Puerto de escucha
- **document_root**: Directorio raíz de archivos
- **ssl_enabled**: Habilitar SSL/TLS
- **php_enabled**: Habilitar procesamiento PHP
- **php_version**: Versión específica de PHP
- **php_pool**: Pool de PHP-FPM a usar

## Protocolo FastCGI

### Parámetros CGI enviados a PHP

```python
{
    'SCRIPT_FILENAME': '/path/to/script.php',
    'REQUEST_METHOD': 'GET|POST|PUT|DELETE',
    'REQUEST_URI': '/path?query=string',
    'QUERY_STRING': 'param=value',
    'CONTENT_TYPE': 'application/x-www-form-urlencoded',
    'CONTENT_LENGTH': '123',
    'SERVER_SOFTWARE': 'TechWebServer/1.0',
    'SERVER_NAME': 'example.com',
    'SERVER_PORT': '3080',
    'REMOTE_ADDR': '192.168.1.100',
    'HTTP_HOST': 'example.com',
    'HTTP_USER_AGENT': 'Mozilla/5.0...',
    'HTTP_ACCEPT': 'text/html,application/xhtml+xml',
    'GATEWAY_INTERFACE': 'CGI/1.1',
    'SERVER_PROTOCOL': 'HTTP/1.1',
    'REDIRECT_STATUS': '200',
    'DOCUMENT_ROOT': '/path/to/document/root'
}
```

### Headers HTTP

Todos los headers HTTP del cliente se convierten a variables CGI:
- `Content-Type` → `HTTP_CONTENT_TYPE`
- `User-Agent` → `HTTP_USER_AGENT`
- `Accept` → `HTTP_ACCEPT`
- `Authorization` → `HTTP_AUTHORIZATION`

## Manejo de Errores

### Códigos de Estado HTTP

- **200 OK**: Archivo servido correctamente
- **403 Forbidden**: Acceso denegado o directory traversal
- **404 Not Found**: Archivo no encontrado
- **500 Internal Server Error**: Error del servidor o PHP

### Errores PHP

Los errores de PHP se capturan desde `FCGI_STDERR` y se logean, pero no se muestran al cliente por seguridad.

## Seguridad

### Validación de Rutas

```python
# Prevención de directory traversal
file_path = file_path.resolve()
document_root = document_root.resolve()

if not str(file_path).startswith(str(document_root)):
    return 403  # Forbidden
```

### Headers de Seguridad

- `Server`: Opcional, configurable para ocultar información
- Validación de paths absolutos
- Restricción a document_root

## Rendimiento

### Asyncio

- Servidor no-bloqueante
- Manejo concurrente de múltiples requests
- Pool de conexiones reutilizable

### PHP-FPM

- Comunicación por sockets Unix (más rápido que TCP)
- Pools separados por versión
- Timeout configurable

## Logging (Próximo)

### Estructura de Log

```json
{
    "timestamp": "2025-06-19T13:21:00Z",
    "ip": "192.168.1.100",
    "country": "AR",
    "method": "GET",
    "path": "/index.php",
    "user_agent": "Mozilla/5.0...",
    "status": 200,
    "response_time": 0.045,
    "virtual_host": "example.com"
}
```

## Próximas Implementaciones

1. **Dashboard Web**: Interfaz de administración
2. **SSL/TLS**: Soporte para HTTPS
3. **Compresión**: gzip/brotli automático
4. **Rate Limiting**: Protección contra abuso
5. **Métricas**: Estadísticas de rendimiento

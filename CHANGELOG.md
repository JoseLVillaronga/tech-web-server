# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-06-19

### Agregado
- **Integración PHP-FPM completa**
  - Cliente FastCGI personalizado (`src/php_fpm/fastcgi_client.py`)
  - Gestor de múltiples versiones PHP (`src/php_fpm/php_manager.py`)
  - Soporte para PHP 7.1, 7.4, 8.2, 8.3, 8.4
  - Configuración de versión PHP por virtual host
  - Parámetros FastCGI completos (headers HTTP, variables CGI)
  - Detección automática de archivos PHP por extensión
  - Manejo correcto de headers de respuesta desde PHP

- **Configuración PHP-FPM**
  - Variables de entorno para sockets de cada versión PHP
  - Timeout configurable para conexiones FastCGI
  - Detección automática de versiones disponibles

- **Archivos de prueba**
  - `public/info.php` - Información PHP para localhost
  - `public/test/version.php` - phpinfo() completo para test.local

### Mejorado
- **Servidor web principal**
  - Manejo de archivos PHP y estáticos en el mismo servidor
  - Información de versiones PHP disponibles al iniciar
  - Mejor manejo de errores en ejecución PHP

- **Sistema de configuración**
  - Soporte para configuración de sockets PHP-FPM
  - Validación de versiones PHP disponibles

### Probado
- ✅ localhost con PHP 8.3.22
- ✅ test.local con PHP 7.4.33
- ✅ phpinfo() funcionando correctamente
- ✅ Variables $_SERVER configuradas correctamente
- ✅ Headers HTTP pasados correctamente a PHP

## [0.1.0] - 2025-06-19

### Agregado
- **Servidor web básico**
  - Servidor asyncio con soporte para alta concurrencia (40-300 conexiones)
  - Puertos personalizables (3080 HTTP, 3453 HTTPS)
  - Servir archivos estáticos (HTML, CSS, JS, imágenes)
  - Detección automática de tipos MIME
  - Validación de rutas y prevención de directory traversal

- **Sistema de virtual hosts**
  - Configuración por dominio en `config/virtual_hosts.yaml`
  - Document root independiente por virtual host
  - Detección automática por header Host
  - Soporte para múltiples dominios

- **Sistema de configuración**
  - Archivo `.env` para configuración global
  - Gestor de configuración (`src/config/config_manager.py`)
  - Carga automática de variables de entorno
  - Configuración de virtual hosts en YAML

- **Estructura del proyecto**
  - Arquitectura modular en `src/`
  - Separación de responsabilidades por módulos
  - Entorno virtual Python
  - Dependencias definidas en `requirements.txt`

- **Seguridad básica**
  - Validación de rutas de archivos
  - Prevención de directory traversal
  - Headers de seguridad básicos
  - Ocultación opcional del header Server

- **Archivos de prueba**
  - `public/index.html` - Página principal
  - `public/test/index.html` - Página de prueba virtual host

### Configuración inicial
- Variables de entorno para servidor, logging, PHP-FPM, SSL
- Virtual hosts de ejemplo (localhost y test.local)
- Gitignore completo para desarrollo Python
- Estructura de directorios modular

### Probado
- ✅ Servidor funcionando en puerto 3080
- ✅ Virtual hosts respondiendo correctamente
- ✅ Archivos estáticos servidos con tipos MIME correctos
- ✅ Seguridad básica funcionando

## [Próximas versiones]

### [0.3.0] - Planificado
- Sistema de logging con MongoDB
- Geolocalización con GeoLite2
- Logs detallados (IP, ruta, user-agent, país, timestamp)

### [0.4.0] - Planificado
- Dashboard web de administración
- Estadísticas en tiempo real
- Visualización de logs
- Métricas de rendimiento

### [0.5.0] - Planificado
- Compresión gzip/brotli
- Soporte SSL/TLS
- Integración Let's Encrypt

### [0.6.0] - Planificado
- Rate limiting
- Headers de seguridad avanzados
- Optimizaciones de rendimiento

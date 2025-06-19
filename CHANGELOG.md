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

- **Compresión gzip/brotli**
  - Compresión automática de respuestas
  - Soporte para múltiples algoritmos
  - Configuración por tipo de contenido

### Probado
- ✅ localhost con PHP 8.3.22
- ✅ test.local con PHP 7.4.33
- ✅ phpinfo() funcionando correctamente
- ✅ Variables $_SERVER configuradas correctamente
- ✅ Headers HTTP pasados correctamente a PHP
- ✅ Compresión gzip/brotli funcionando

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

## [0.3.0] - 2025-06-19 - ✅ COMPLETADO

### Agregado
- **Sistema de logging completo con MongoDB**
  - Cliente MongoDB asíncrono (`src/database/mongodb_client.py`)
  - Logging dual: memoria + MongoDB persistente
  - Base de datos `tech_web_server` creada automáticamente
  - Colección `access_logs` con índices optimizados
  - Información detallada: IP, país, método, path, status, user-agent, tiempo de respuesta
  - Configuración habilitación/deshabilitación desde .env

- **Geolocalización inteligente**
  - Detección automática de IPs locales vs remotas (`src/logging/geoip_manager.py`)
  - Soporte para GeoLite2 (opcional)
  - Fallback inteligente cuando no hay base de datos GeoIP
  - Clasificación LOCAL para IPs privadas

- **Dashboard web funcional**
  - Servidor dashboard completo (`src/dashboard/dashboard_server.py`)
  - Interfaz web moderna en puerto 8000
  - Estadísticas en tiempo real con API REST
  - Visualización de logs recientes
  - Distribución por países, tipos de request, códigos de estado
  - Estado de virtual hosts y versiones PHP disponibles
  - Acceso remoto configurado (0.0.0.0)

### Mejorado
- **Manejo de errores MongoDB**
  - Conexión sin autenticación para MongoDB local
  - Fallback a logging en memoria cuando MongoDB no disponible
  - Validaciones correctas de colecciones MongoDB
  - Mensajes informativos durante inicialización

- **Sistema de logging**
  - Logger principal (`src/logging/logger.py`) con doble destino
  - Índices optimizados para consultas rápidas
  - Cleanup automático de logs antiguos (configurable)

### Probado
- ✅ MongoDB conectado y guardando logs
- ✅ Dashboard accesible remotamente en puerto 8000
- ✅ Estadísticas en tiempo real funcionando
- ✅ Geolocalización detectando IPs locales correctamente
- ✅ API REST del dashboard respondiendo
- ✅ Logs persistentes en MongoDB con toda la información

## [Próximas versiones]

### [0.4.0] - Planificado
- Soporte SSL/TLS
- Integración Let's Encrypt
- Certificados automáticos

### [0.5.0] - Planificado
- Rate limiting
- Headers de seguridad avanzados
- Optimizaciones de rendimiento
- Métricas avanzadas de sistema

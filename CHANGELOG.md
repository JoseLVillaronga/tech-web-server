# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2025-06-24 - ✅ COMPLETADO

### Agregado
- **Modo Multi-Puerto HTTP (`SSL_ENABLED=false`)**
  - Múltiples servidores HTTP en puertos específicos por virtual host
  - Routing inteligente por `(Host, Port)` en lugar de solo `Host`
  - Configuración `SSL_ENABLED=true/false` en `.env` para control global
  - Método `get_unique_http_ports()` en ConfigManager
  - Método `get_virtual_host_by_domain_and_port()` para routing multi-puerto

- **Optimización para Proxy Reverso**
  - Deshabilitación automática de HTTPS cuando `SSL_ENABLED=false`
  - Máximo rendimiento sin overhead SSL interno
  - Ideal para uso detrás de Caddy, Nginx, Cloudflare
  - Cada virtual host puede tener puerto dedicado

- **Documentación completa**
  - Guía específica de Multi-Puerto (`docs/MULTI_PORT_CONFIGURATION.md`)
  - Actualización de guía de Proxy Reverso (`docs/REVERSE_PROXY_SUPPORT.md`)
  - Ejemplos de configuración con Caddy
  - Casos de uso: hosting multi-cliente, microservicios, multi-región

### Mejorado
- **Lógica de inicio de servidores**
  - Creación condicional de servidores HTTP según modo
  - Información detallada de puertos activos al iniciar
  - Validación automática de configuración multi-puerto

- **Sistema de routing**
  - Detección automática de puerto del servidor desde request
  - Fallback inteligente al routing tradicional por Host
  - Compatibilidad 100% con configuraciones existentes

- **Configuración flexible**
  - Campo `port` en virtual_hosts.yaml ahora funcional
  - Soporte para puertos compartidos y dedicados
  - Validación de configuración SSL vs Multi-Puerto

### Probado
- ✅ **Modo SSL (`SSL_ENABLED=true`)**: Comportamiento tradicional preservado
- ✅ **Modo Multi-Puerto (`SSL_ENABLED=false`)**: Múltiples puertos HTTP funcionando
- ✅ **Puerto 3080**: `localhost` y `test.local` (compartido)
- ✅ **Puerto 3090**: `admin.local` (dedicado)
- ✅ **Puerto 3091**: `api.local` (dedicado)
- ✅ **HTTPS deshabilitado**: Correctamente cuando SSL_ENABLED=false
- ✅ **Routing inteligente**: Por (Host, Port) funcionando
- ✅ **Compatibilidad Caddy**: Proxy reverso funcionando perfectamente

### Casos de Uso Validados
- 🏢 **Hosting Multi-Cliente**: Cada cliente en puerto dedicado
- 🔧 **Microservicios**: API, admin, frontend en puertos separados
- 🌍 **Multi-Región**: Servicios por región en puertos específicos
- ⚡ **Alto Rendimiento**: Sin overhead SSL, máxima velocidad PHP-FPM

### Beneficios
- 🚀 **Performance**: Sin SSL interno = máximo rendimiento
- 🔧 **Flexibilidad**: Versiones PHP diferentes por puerto
- 🛡️ **Seguridad**: Tech Web Server solo localhost, Caddy expuesto
- 📊 **Aislamiento**: Cada servicio completamente independiente
- 🔄 **Escalabilidad**: Fácil agregar nuevos servicios/puertos

## [0.6.0] - 2025-06-21 - ✅ COMPLETADO

### Agregado
- **Soporte completo para proxy reverso**
  - Función `_get_real_client_ip()` en servidor web (`src/server/web_server.py`)
  - Función `_get_real_client_ip()` en PHP manager (`src/php_fpm/php_manager.py`)
  - Detección automática de IP real del cliente
  - Soporte para múltiples headers de proxy: `X-Forwarded-For`, `X-Real-IP`, `X-Client-IP`, `CF-Connecting-IP`, `True-Client-IP`
  - Validación de IPs para seguridad
  - Configuración habilitación/deshabilitación (`PROXY_SUPPORT_ENABLED`)

- **Geolocalización con IPs reales**
  - Modificación en `config.php` para forzar actualización de país
  - Detección de cambios de IP del cliente
  - Actualización automática cuando país es `ZZ` (desconocido)
  - Tracking de IP por sesión (`$_SESSION['lastIP']`)

- **Documentación completa**
  - Guía detallada de proxy reverso (`docs/REVERSE_PROXY_SUPPORT.md`)
  - Ejemplos de configuración para Caddy, Nginx, Cloudflare
  - Casos de prueba y troubleshooting
  - Actualización del README principal

### Mejorado
- **Compatibilidad con Caddy**
  - Integración perfecta con Caddy como proxy reverso
  - Headers `X-Forwarded-For` procesados correctamente
  - IPs reales pasadas a aplicaciones PHP

- **Sistema de logging**
  - Logs ahora muestran IPs reales de clientes
  - Geolocalización funcional con códigos de país correctos
  - Estadísticas precisas por país en dashboard

- **Aplicaciones PHP**
  - Variable `$_SERVER['REMOTE_ADDR']` contiene IP real
  - Clase `Visitas` registra IPs y países correctos
  - Librería `geoiploc.php` funciona con IPs reales

### Probado
- ✅ Caddy + Tech Web Server funcionando perfectamente
- ✅ IPs reales detectadas: `191.85.12.36`, `70.171.207.63`
- ✅ Países correctos: `AR` (Argentina), `US` (Estados Unidos)
- ✅ Dashboard muestra estadísticas reales
- ✅ Geolocalización funcional al 100%
- ✅ Aplicaciones PHP reciben IPs reales

### Beneficios
- 📈 **Analytics precisos** - Estadísticas reales de visitantes por país
- 🔒 **Seguridad mejorada** - Logs de seguridad con IPs reales
- 🌍 **Geolocalización correcta** - Contenido personalizado por ubicación
- 📊 **Dashboard útil** - Métricas reales de tráfico internacional
- 🔧 **Compatibilidad total** - Funciona con infraestructura moderna

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

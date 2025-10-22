# 🏗️ ANÁLISIS DE ARQUITECTURA

## 📐 Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTES HTTP                             │
│  (Navegadores, APIs, Proxies Reversos, etc.)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │   SERVIDOR WEB ASYNCIO (aiohttp)   │
        │   Puerto 3080 (HTTP)               │
        │   Puerto 3453 (HTTPS)              │
        │   Puerto 8000 (Dashboard)          │
        └────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    ┌────────┐    ┌──────────┐    ┌──────────┐
    │ CONFIG │    │ ROUTING  │    │ SECURITY │
    │MANAGER │    │ (Host,   │    │VALIDATION│
    │        │    │ Port)    │    │          │
    └────────┘    └──────────┘    └──────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
    ┌──────────────┐            ┌──────────────┐
    │ ARCHIVOS     │            │ PHP-FPM      │
    │ ESTÁTICOS    │            │ (FastCGI)    │
    │              │            │              │
    │ - HTML       │            │ - 7.1        │
    │ - CSS        │            │ - 7.4        │
    │ - JS         │            │ - 8.2        │
    │ - Imágenes   │            │ - 8.3        │
    │              │            │ - 8.4        │
    └──────────────┘            └──────────────┘
        │                                 │
        └────────────────┬────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
    ┌──────────────┐            ┌──────────────┐
    │ LOGGING      │            │ DASHBOARD    │
    │              │            │              │
    │ - MongoDB    │            │ - API REST   │
    │ - Memoria    │            │ - WebSocket  │
    │ - GeoIP      │            │ - HTML5      │
    │              │            │ - Filtros    │
    └──────────────┘            └──────────────┘
```

---

## 🔄 Flujo de Procesamiento de Requests

```
1. RECEPCIÓN
   ├─ Cliente conecta a puerto 3080/3453
   ├─ Servidor asyncio acepta conexión
   └─ Request HTTP parseado

2. IDENTIFICACIÓN
   ├─ Extrae header Host
   ├─ Obtiene puerto del servidor
   ├─ Busca virtual host por (Host, Port)
   └─ Fallback a primer virtual host si no encuentra

3. VALIDACIÓN
   ├─ Valida seguridad (directory traversal)
   ├─ Verifica rutas bloqueadas (.git, node_modules, etc.)
   ├─ Resuelve ruta del archivo
   └─ Verifica que esté dentro de document_root

4. PROCESAMIENTO
   ├─ ¿Es archivo PHP?
   │  ├─ SÍ: Delega a PHP-FPM
   │  │   ├─ Construye parámetros CGI
   │  │   ├─ Conecta a socket Unix
   │  │   ├─ Envía request FastCGI
   │  │   ├─ Recibe respuesta PHP
   │  │   └─ Parsea headers y body
   │  └─ NO: Sirve archivo estático
   │      ├─ Lee archivo
   │      ├─ Detecta tipo MIME
   │      ├─ Aplica compresión (gzip/brotli)
   │      └─ Envía respuesta

5. LOGGING
   ├─ Obtiene IP real del cliente
   ├─ Detecta país (GeoIP)
   ├─ Registra en MongoDB
   ├─ Registra en memoria
   └─ Actualiza estadísticas

6. RESPUESTA
   ├─ Envía headers HTTP
   ├─ Envía body comprimido
   └─ Cierra conexión
```

---

## 🏛️ Capas de Arquitectura

### Capa 1: Presentación
- **Componentes**: Servidor HTTP, Dashboard
- **Responsabilidad**: Interfaz con clientes
- **Tecnología**: aiohttp, HTML5, WebSocket

### Capa 2: Aplicación
- **Componentes**: Routing, Validación, Procesamiento
- **Responsabilidad**: Lógica de negocio
- **Tecnología**: Python asyncio

### Capa 3: Integración
- **Componentes**: PHP-FPM, FastCGI
- **Responsabilidad**: Ejecución de código
- **Tecnología**: Sockets Unix, FastCGI

### Capa 4: Persistencia
- **Componentes**: MongoDB, Memoria
- **Responsabilidad**: Almacenamiento de datos
- **Tecnología**: MongoDB, Python dict

### Capa 5: Infraestructura
- **Componentes**: SSL/TLS, Geolocalización
- **Responsabilidad**: Servicios transversales
- **Tecnología**: OpenSSL, GeoLite2

---

## 📦 Módulos y Dependencias

```
main.py
  └─ server/web_server.py (TechWebServer)
      ├─ config/config_manager.py (ConfigManager)
      ├─ php_fpm/php_manager.py (PHPManager)
      │   └─ php_fpm/fastcgi_client.py (FastCGIClient)
      ├─ dashboard/dashboard_server.py (DashboardServer)
      ├─ database/mongodb_client.py (MongoDBClient)
      ├─ tls/ssl_manager.py (SSLManager)
      └─ utils/geoip.py (GeoIPManager)
```

---

## 🔌 Interfaces Externas

### Entrada
- **HTTP**: Puerto 3080 (clientes)
- **HTTPS**: Puerto 3453 (clientes)
- **Dashboard**: Puerto 8000 (administradores)

### Salida
- **PHP-FPM**: Sockets Unix (/run/php/php*.sock)
- **MongoDB**: TCP 27017 (localhost)
- **GeoIP**: Archivo local (GeoLite2-Country.mmdb)

### Configuración
- **.env**: Variables de entorno
- **virtual_hosts.yaml**: Configuración de dominios
- **Certificados SSL**: Archivos en ssl/

---

## 🔐 Flujo de Seguridad

```
Request HTTP
    │
    ▼
┌─────────────────────────┐
│ Validar IP del cliente  │
│ (proxy reverso)         │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Validar ruta solicitada │
│ (directory traversal)   │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Verificar rutas         │
│ bloqueadas              │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Verificar SSL/TLS       │
│ (si está habilitado)    │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Procesar request        │
│ (seguro)                │
└─────────────────────────┘
```

---

## 📊 Flujo de Datos

### Request HTTP
```
Cliente
  │
  ├─ Headers HTTP
  │  ├─ Host: example.com
  │  ├─ User-Agent: Mozilla/5.0
  │  ├─ Accept-Encoding: gzip, deflate
  │  └─ X-Forwarded-For: 191.85.12.36 (proxy)
  │
  ├─ Body (si POST)
  │  └─ Datos del formulario
  │
  └─ Cookies
     └─ Session ID, etc.
```

### Response HTTP
```
Servidor
  │
  ├─ Status Code: 200 OK
  │
  ├─ Headers HTTP
  │  ├─ Content-Type: text/html
  │  ├─ Content-Encoding: gzip
  │  ├─ Cache-Control: max-age=3600
  │  └─ Set-Cookie: session=...
  │
  └─ Body
     └─ HTML/JSON/Binario comprimido
```

---

## 🔄 Ciclo de Vida de una Conexión

```
1. CONEXIÓN
   ├─ Cliente conecta a puerto 3080
   ├─ Servidor acepta conexión
   └─ Socket establecido

2. REQUEST
   ├─ Cliente envía HTTP request
   ├─ Servidor parsea headers y body
   └─ Validación inicial

3. PROCESAMIENTO
   ├─ Identificar virtual host
   ├─ Validar seguridad
   ├─ Procesar (PHP o estático)
   └─ Generar respuesta

4. LOGGING
   ├─ Registrar en MongoDB
   ├─ Registrar en memoria
   └─ Actualizar estadísticas

5. RESPUESTA
   ├─ Enviar headers HTTP
   ├─ Enviar body
   └─ Flush buffer

6. CIERRE
   ├─ Cliente cierra conexión
   ├─ Servidor libera recursos
   └─ Conexión finalizada
```

---

## 🎯 Patrones de Diseño

### 1. Singleton
- **ConfigManager**: Una instancia global
- **MongoDBClient**: Una instancia global
- **SSLManager**: Una instancia global

### 2. Factory
- **PHPManager**: Crea FastCGIClient según versión
- **SSLManager**: Crea contextos SSL por dominio

### 3. Strategy
- **Routing**: Por Host (SSL) o (Host, Port) (Multi-puerto)
- **Compresión**: gzip o brotli según cliente

### 4. Observer
- **Dashboard**: Observa estadísticas en tiempo real
- **WebSocket**: Notifica cambios a clientes

### 5. Adapter
- **FastCGIClient**: Adapta protocolo FastCGI a Python
- **MongoDBClient**: Adapta MongoDB a logging

---

## 📈 Escalabilidad

### Horizontal
- Múltiples instancias detrás de Caddy/Nginx
- Cada instancia con su puerto
- MongoDB compartido para logging

### Vertical
- Aumentar MAX_CONCURRENT_CONNECTIONS
- Aumentar pool de PHP-FPM
- Aumentar memoria del servidor

### Optimizaciones
- Índices en MongoDB
- Caché de certificados SSL
- Compresión de respuestas
- Sockets Unix (no TCP)

---

## 🔧 Configurabilidad

### Por Entorno
```
Desarrollo:
  SSL_ENABLED=false
  LOGS=true
  mongo_host=localhost

Producción:
  SSL_ENABLED=false (con Caddy)
  LOGS=true
  mongo_host=mongodb.prod
  PROXY_SUPPORT_ENABLED=true
```

### Por Virtual Host
```yaml
- domain: "api.example.com"
  port: 3091
  php_version: "8.4"
  php_pool: "api"
```

---

## 🚀 Rendimiento

### Optimizaciones Implementadas
1. **Asyncio**: No-bloqueante
2. **Sockets Unix**: Rápido
3. **Compresión**: Reduce ancho de banda
4. **Índices MongoDB**: Consultas rápidas
5. **Cache SSL**: Contextos reutilizables

### Benchmarks Esperados
- **Requests/segundo**: 1000+ (con PHP-FPM)
- **Latencia**: <50ms (local)
- **Throughput**: 100+ Mbps
- **Conexiones simultáneas**: 300

---

## 🔐 Seguridad en Capas

1. **Capa de Red**: TLS 1.2+
2. **Capa de Aplicación**: Validación de rutas
3. **Capa de Datos**: MongoDB con índices
4. **Capa de Proceso**: Aislamiento por virtual host
5. **Capa de Infraestructura**: Permisos de archivos

---

## 📊 Monitoreo y Observabilidad

### Métricas Disponibles
- Requests totales
- Requests por minuto
- Conexiones activas
- Errores
- Uptime
- Distribución por país
- Distribución por status code

### Logs Disponibles
- Access logs (MongoDB)
- Error logs (stderr)
- Application logs (stdout)
- Dashboard logs (en memoria)

### Alertas Posibles
- Tasa de error alta
- Conexiones máximas alcanzadas
- MongoDB desconectado
- PHP-FPM offline
- Certificado SSL próximo a expirar


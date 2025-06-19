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

### 🔄 En Desarrollo

#### 4. Sistema de Logging
- [ ] Logging de accesos (IP, ruta, user-agent, país, timestamp)
- [ ] Integración con MongoDB
- [ ] Geolocalización con GeoLite2
- [ ] Logs habilitables/deshabilitables desde .env

#### 5. Dashboard Web
- [ ] Interfaz web de administración
- [ ] Estadísticas en tiempo real
- [ ] Visualización de logs
- [ ] Estado de virtual hosts
- [ ] Métricas de rendimiento

#### 6. Funcionalidades Avanzadas
- [ ] Compresión gzip/brotli
- [ ] Soporte SSL/TLS
- [ ] Rate limiting
- [ ] Headers de seguridad

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
    ssl_enabled: false
    php_enabled: true
    php_version: "8.3"
    php_pool: "www"
  
  - domain: "test.local"
    port: 3080
    document_root: "./public/test"
    ssl_enabled: false
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
│   ├── logging/                   # (próximo)
│   ├── dashboard/                 # (próximo)
│   ├── ssl/                       # (próximo)
│   └── utils/                     # (próximo)
├── config/
│   └── virtual_hosts.yaml         # Configuración virtual hosts
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
1. **Sistema de logging** con MongoDB y geolocalización
2. **Dashboard web** con estadísticas en tiempo real
3. **Compresión** gzip/brotli
4. **SSL/TLS** con Let's Encrypt
5. **Rate limiting** y seguridad avanzada

### Commits importantes
- `63027a3` - Implementación básica del servidor web
- `f412383` - Integración PHP-FPM completa

## 📝 Licencia

[Especificar licencia]

## 🤝 Contribuciones

[Instrucciones para contribuir]

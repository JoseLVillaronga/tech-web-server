# 📊 Análisis: .htaccess de Punto A vs Configuración YAML

## 🎯 Objetivo

Comparar las funcionalidades del `.htaccess` actual de Punto A con lo que se puede configurar en `virtual_hosts.yaml` usando la Alternativa 3.

---

## 📋 Funcionalidades del .htaccess Actual

### 1. **Rewrite Rules (Reescritura de URLs)**
```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ index.php?url=$1 [QSA,L]
```
**Propósito:** Redirigir todas las peticiones a `index.php` para que el router MVC maneje las rutas.

### 2. **HTTPS Redirect (Redirección a HTTPS)**
```apache
RewriteCond %{HTTPS} off [OR]
RewriteCond %{HTTP_HOST} ^(.+):3080$ [NC]
RewriteRule ^(.*)$ https://puntoa.z-sur.com.ar/$1 [R=301,L]
```
**Propósito:** Forzar HTTPS y remover puerto de la URL.

### 3. **Protección de Archivos Sensibles**
```apache
<Files "config.php">
    Order Deny,Allow
    Deny from all
</Files>

<Files ".env">
    Order Deny,Allow
    Deny from all
</Files>

<FilesMatch "^(config|database)/">
    Order Deny,Allow
    Deny from all
</FilesMatch>
```
**Propósito:** Bloquear acceso a archivos de configuración.

### 4. **Cache de Archivos Estáticos**
```apache
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType text/css "access plus 1 month"
    ExpiresByType application/javascript "access plus 1 month"
    ExpiresByType image/* "access plus 1 month"
    ...
</IfModule>
```
**Propósito:** Configurar headers de cache para archivos estáticos.

### 5. **Compresión GZIP**
```apache
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE application/javascript
    ...
</IfModule>
```
**Propósito:** Comprimir respuestas HTTP.

### 6. **Headers Personalizados**
```apache
<Files "favicon.ico">
    Header set Cache-Control "public, max-age=31536000"
</Files>

<Files "manifest.json">
    Header set Content-Type "application/manifest+json"
    Header set Cache-Control "public, max-age=604800"
</Files>
```
**Propósito:** Configurar headers específicos para archivos.

---

## ✅ Funcionalidades Soportadas en YAML (Alternativa 3)

### 1. ✅ Rewrite Rules - **SÍ, COMPLETAMENTE**

```yaml
virtual_hosts:
  - domain: "puntoa.z-sur.com.ar"
    document_root: "./public/puntoa"
    
    rewrite_rules:
      - pattern: "^(.*)$"
        target: "/index.php"
        query_string: "url=$1"
        conditions:
          - type: "file_not_exists"
          - type: "dir_not_exists"
```

**Equivalencia:** 100% compatible con Apache RewriteRule

---

### 2. ⚠️ HTTPS Redirect - **PARCIALMENTE**

**Opción A: En virtual_hosts.yaml**
```yaml
virtual_hosts:
  - domain: "puntoa.z-sur.com.ar"
    ssl_enabled: true
    ssl_redirect: true  # Fuerza HTTPS
    port: 443
```

**Opción B: Con rewrite rule**
```yaml
rewrite_rules:
  - pattern: "^(.*)$"
    target: "https://puntoa.z-sur.com.ar/$1"
    conditions:
      - type: "https_off"
      - type: "port_is_3080"
    flags: ["R=301", "L"]
```

**Nota:** Requiere agregar soporte para condiciones `https_off` y `port_is_3080`.

---

### 3. ⚠️ Protección de Archivos - **PARCIALMENTE**

**Opción A: En virtual_hosts.yaml**
```yaml
virtual_hosts:
  - domain: "puntoa.z-sur.com.ar"
    
    protected_files:
      - "config.php"
      - ".env"
      - "config/*"
      - "database/*"
```

**Opción B: Con rewrite rule**
```yaml
rewrite_rules:
  - pattern: "^/(config|database|\.env|config\.php).*$"
    target: "403"  # Forbidden
    action: "deny"
```

**Nota:** Requiere agregar soporte para `protected_files` o acción `deny`.

---

### 4. ⚠️ Cache de Archivos - **PARCIALMENTE**

**En virtual_hosts.yaml**
```yaml
virtual_hosts:
  - domain: "puntoa.z-sur.com.ar"
    
    cache_rules:
      - pattern: "\.css$"
        max_age: "2592000"  # 1 month
      - pattern: "\.js$"
        max_age: "2592000"
      - pattern: "\.(png|jpg|jpeg|gif|svg|ico)$"
        max_age: "2592000"
      - pattern: "favicon\.ico$"
        max_age: "31536000"  # 1 year
      - pattern: "manifest\.json$"
        max_age: "604800"    # 1 week
```

**Nota:** Requiere agregar soporte para `cache_rules`.

---

### 5. ⚠️ Compresión GZIP - **PARCIALMENTE**

**En .env o virtual_hosts.yaml**
```yaml
virtual_hosts:
  - domain: "puntoa.z-sur.com.ar"
    
    compression:
      enabled: true
      types:
        - "text/plain"
        - "text/html"
        - "text/css"
        - "application/javascript"
        - "application/json"
```

**Nota:** Tech Web Server ya soporta compresión globalmente. Requiere hacer configurable por vhost.

---

### 6. ⚠️ Headers Personalizados - **PARCIALMENTE**

**En virtual_hosts.yaml**
```yaml
virtual_hosts:
  - domain: "puntoa.z-sur.com.ar"
    
    custom_headers:
      - pattern: "favicon\.ico$"
        headers:
          Cache-Control: "public, max-age=31536000"
      - pattern: "manifest\.json$"
        headers:
          Content-Type: "application/manifest+json"
          Cache-Control: "public, max-age=604800"
```

**Nota:** Requiere agregar soporte para `custom_headers`.

---

## 📊 Matriz de Compatibilidad

| Funcionalidad | .htaccess | YAML (Fase 1) | YAML (Fase 2) | Notas |
|---------------|-----------|---------------|---------------|-------|
| Rewrite Rules | ✅ | ✅ | ✅ | 100% compatible |
| HTTPS Redirect | ✅ | ⚠️ | ✅ | Requiere condiciones adicionales |
| Protección Archivos | ✅ | ⚠️ | ✅ | Requiere `protected_files` |
| Cache Estáticos | ✅ | ⚠️ | ✅ | Requiere `cache_rules` |
| Compresión GZIP | ✅ | ⚠️ | ✅ | Requiere hacer configurable |
| Headers Personalizados | ✅ | ⚠️ | ✅ | Requiere `custom_headers` |

---

## 🎯 Respuesta a tu Pregunta

### ¿Permite la Alternativa 3 configurar las mismas funcionalidades?

**Respuesta: SÍ, pero en dos fases:**

#### **FASE 1 (1-2 días):** Rewrite Rules Básicas
- ✅ Reescritura de URLs (100% compatible)
- ✅ Condiciones: file_not_exists, dir_not_exists
- ✅ Parámetros de query string
- ✅ Flags: QSA, L

**Esto es suficiente para hospedar Punto A.**

#### **FASE 2 (3-5 días):** Funcionalidades Avanzadas
- ✅ HTTPS Redirect
- ✅ Protección de archivos
- ✅ Cache de estáticos
- ✅ Compresión GZIP
- ✅ Headers personalizados

**Esto hace la configuración 100% equivalente a .htaccess.**

---

## 🔧 Ejemplo Completo: Punto A en YAML

### Fase 1 (Mínimo para funcionar)
```yaml
virtual_hosts:
  - domain: "puntoa.z-sur.com.ar"
    port: 443
    document_root: "./public/puntoa"
    ssl_enabled: true
    php_enabled: true
    php_version: "8.3"
    
    rewrite_rules:
      - pattern: "^(.*)$"
        target: "/index.php"
        query_string: "url=$1"
        conditions:
          - type: "file_not_exists"
          - type: "dir_not_exists"
```

### Fase 2 (Completo, equivalente a .htaccess)
```yaml
virtual_hosts:
  - domain: "puntoa.z-sur.com.ar"
    port: 443
    document_root: "./public/puntoa"
    ssl_enabled: true
    ssl_redirect: true
    php_enabled: true
    php_version: "8.3"
    
    rewrite_rules:
      - pattern: "^(.*)$"
        target: "/index.php"
        query_string: "url=$1"
        conditions:
          - type: "file_not_exists"
          - type: "dir_not_exists"
    
    protected_files:
      - "config.php"
      - ".env"
      - "config/*"
      - "database/*"
    
    cache_rules:
      - pattern: "\.(css|js)$"
        max_age: "2592000"
      - pattern: "\.(png|jpg|jpeg|gif|svg)$"
        max_age: "2592000"
      - pattern: "favicon\.ico$"
        max_age: "31536000"
      - pattern: "manifest\.json$"
        max_age: "604800"
    
    compression:
      enabled: true
      types:
        - "text/css"
        - "application/javascript"
        - "application/json"
    
    custom_headers:
      - pattern: "favicon\.ico$"
        headers:
          Cache-Control: "public, max-age=31536000"
      - pattern: "manifest\.json$"
        headers:
          Content-Type: "application/manifest+json"
          Cache-Control: "public, max-age=604800"
```

---

## 🚀 Plan de Implementación

### Fase 1: Rewrite Rules (1-2 días)
- Implementar RewriteEngine básico
- Soportar condiciones: file_not_exists, dir_not_exists
- Integrar en web_server.py
- Probar con Punto A

### Fase 2: Funcionalidades Avanzadas (3-5 días)
- Agregar `protected_files`
- Agregar `cache_rules`
- Agregar `custom_headers`
- Hacer compresión configurable por vhost
- Agregar condiciones: https_off, port_is_3080

### Fase 3: Optimización (1-2 días)
- Caché de reglas
- Benchmarking
- Documentación

---

## ✅ Conclusión

**SÍ, la Alternativa 3 permite configurar las mismas funcionalidades del .htaccess, pero en dos fases:**

1. **Fase 1:** Rewrite rules básicas (suficiente para Punto A)
2. **Fase 2:** Todas las funcionalidades avanzadas (100% equivalente)

**Ventajas sobre .htaccess:**
- Configuración centralizada en un archivo
- Específica por sitio
- Mejor rendimiento (sin parsing)
- Más fácil de mantener
- Mejor control de seguridad



# 📚 Ejemplos de Rewrite Rules para Aplicaciones MVC

## 🎯 Caso de Uso: Punto A (Aplicación MVC)

### Estructura Actual
```
/home/jose/tech-web-server/public/puntoa/
├── index.php              ← Punto de entrada
├── app/
│   ├── controllers/
│   ├── models/
│   └── views/
├── public/
│   ├── css/
│   ├── js/
│   └── images/
└── config/
```

### Rutas Esperadas
```
/usuarios/123           → /index.php?route=/usuarios/123
/api/productos          → /index.php?route=/api/productos
/admin/dashboard        → /index.php?route=/admin/dashboard
/public/css/style.css   → /public/css/style.css (archivo real)
/public/js/app.js       → /public/js/app.js (archivo real)
```

---

## 📋 Ejemplos por Alternativa

### ALTERNATIVA 3: Configuración en virtual_hosts.yaml

```yaml
virtual_hosts:
  - domain: "puntoa.local"
    port: 3080
    document_root: "./public/puntoa"
    php_enabled: true
    php_version: "8.3"
    
    # Reglas de rewrite para MVC
    rewrite_rules:
      # Permitir archivos reales
      - pattern: "^/public/.*$"
        action: "pass"  # No reescribir
      
      # Permitir directorios reales
      - pattern: "^/vendor/.*$"
        action: "pass"
      
      # Reescribir todo lo demás a index.php
      - pattern: "^/(.*)$"
        target: "/index.php"
        query_string: "route=$1"
        conditions:
          - type: "file_not_exists"
          - type: "dir_not_exists"
```

### ALTERNATIVA 4: Soporte .htaccess

```apache
# /home/jose/tech-web-server/public/puntoa/.htaccess

<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /
    
    # No reescribir archivos reales
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    
    # Reescribir todo a index.php
    RewriteRule ^(.*)$ index.php?route=$1 [QSA,L]
</IfModule>
```

---

## 🔧 Casos de Uso Comunes

### 1. API REST
```yaml
rewrite_rules:
  - pattern: "^/api/(.*)$"
    target: "/index.php"
    query_string: "api=$1"
    conditions:
      - type: "file_not_exists"
      - type: "dir_not_exists"
```

### 2. Blog con Slugs
```yaml
rewrite_rules:
  - pattern: "^/blog/([a-z0-9-]+)/?$"
    target: "/index.php"
    query_string: "post=$1"
    conditions:
      - type: "file_not_exists"
```

### 3. Galería de Imágenes
```yaml
rewrite_rules:
  - pattern: "^/galeria/([0-9]+)/?$"
    target: "/index.php"
    query_string: "gallery=$1"
    conditions:
      - type: "file_not_exists"
```

### 4. Panel Admin
```yaml
rewrite_rules:
  - pattern: "^/admin/(.*)$"
    target: "/admin/index.php"
    query_string: "page=$1"
    conditions:
      - type: "file_not_exists"
      - type: "dir_not_exists"
```

### 5. Redirecciones Permanentes
```yaml
rewrite_rules:
  - pattern: "^/old-page/?$"
    target: "/new-page"
    status: 301  # Redirección permanente
```

---

## 🧪 Pruebas de Validación

### Test 1: Archivo Real
```bash
# Debe servir el archivo real
curl http://puntoa.local:3080/public/css/style.css
# Esperado: Contenido del archivo CSS
```

### Test 2: Ruta MVC
```bash
# Debe reescribirse a index.php
curl http://puntoa.local:3080/usuarios/123
# Esperado: Respuesta de index.php con route=/usuarios/123
```

### Test 3: Directorio Real
```bash
# Debe permitir acceso al directorio
curl http://puntoa.local:3080/vendor/
# Esperado: Contenido del directorio o index.php si existe
```

### Test 4: Query String
```bash
# Debe preservar query string
curl http://puntoa.local:3080/usuarios/123?sort=name
# Esperado: route=/usuarios/123&sort=name
```

---

## 🔍 Debugging

### Verificar Reglas Aplicadas
```python
# En web_server.py
print(f"Request: {request.path}")
print(f"Matched rule: {matched_rule}")
print(f"Rewritten to: {rewritten_path}")
print(f"Query string: {query_string}")
```

### Logs de Rewrite
```yaml
# En .env
REWRITE_DEBUG=true
REWRITE_LOG_FILE=/var/log/webserver/rewrite.log
```

---

## 📊 Comparación de Sintaxis

### Apache .htaccess
```apache
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ index.php?route=$1 [QSA,L]
```

### YAML (Alternativa 3)
```yaml
conditions:
  - type: "file_not_exists"
  - type: "dir_not_exists"
pattern: "^(.*)$"
target: "/index.php"
query_string: "route=$1"
```

### Python (Alternativa 4)
```python
RewriteRule(
    pattern=r"^(.*)$",
    target="/index.php",
    query_string="route=$1",
    conditions=[
        FileNotExistsCondition(),
        DirNotExistsCondition()
    ]
)
```

---

## 🚀 Implementación Recomendada

### Fase 1: YAML Simple
```yaml
# config/virtual_hosts.yaml
- domain: "puntoa.local"
  rewrite_rules:
    - pattern: "^/(?!public|vendor)(.*)$"
      target: "/index.php"
      query_string: "route=$1"
      conditions:
        - type: "file_not_exists"
        - type: "dir_not_exists"
```

### Fase 2: .htaccess Opcional
```apache
# public/puntoa/.htaccess
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ index.php?route=$1 [QSA,L]
```

---

## ✅ Checklist de Implementación

- [ ] Diseñar estructura de RewriteRule
- [ ] Implementar RewriteEngine en Python
- [ ] Agregar soporte en virtual_hosts.yaml
- [ ] Crear tests unitarios
- [ ] Probar con Punto A
- [ ] Documentar para usuarios
- [ ] Agregar soporte .htaccess (opcional)
- [ ] Optimizar rendimiento
- [ ] Agregar logging/debugging



# 🧪 Guía de Prueba: Rewrite Engine

## ✅ Implementación Completada

Se ha implementado exitosamente el **Rewrite Engine** para Tech Web Server con soporte para reescritura de URLs basada en configuración YAML.

---

## 📁 Archivos Creados

### Módulo de Rewrite Engine
```
src/rewrite/
├── __init__.py              # Exporta las clases principales
├── conditions.py            # Condiciones (file_not_exists, dir_not_exists)
├── rewrite_rule.py          # Clase RewriteRule
└── rewrite_engine.py        # Motor de rewrite principal
```

### Tests
```
tests/
└── test_rewrite_engine.py   # 11 tests unitarios (todos pasando ✅)
```

### Configuración
```
config/virtual_hosts.yaml   # Actualizado con rewrite_rules para Punto A
```

### Integración
```
src/server/web_server.py    # Integrado RewriteEngine en el flujo de requests
```

---

## 🧪 Tests Ejecutados

Todos los 11 tests unitarios pasaron exitosamente:

```
✅ test_dir_not_exists_condition_false
✅ test_dir_not_exists_condition_true
✅ test_file_not_exists_condition_false
✅ test_file_not_exists_condition_true
✅ test_engine_respects_last_flag
✅ test_engine_with_rules
✅ test_engine_without_rules
✅ test_rule_apply_with_capture_groups
✅ test_rule_apply_with_qsa_flag
✅ test_rule_pattern_matching
✅ test_rule_with_conditions

Ran 11 tests in 0.003s - OK
```

---

## 🚀 Cómo Probar Punto A

### 1. Iniciar el servidor

```bash
cd /home/jose/tech-web-server
python main.py
```

El servidor debería mostrar:
```
🌐 Virtual hosts configurados:
   - puntoa.z-sur.com.ar -> ./public/puntoa (PHP 8.3)
```

### 2. Probar con curl

```bash
# Probar una ruta MVC (debe reescribirse a index.php)
curl -v http://localhost:3083/usuarios/123

# Esperado:
# - La ruta se reescribe a /index.php?url=/usuarios/123
# - Punto A recibe la ruta en el parámetro 'url'
# - El router MVC procesa la ruta correctamente
```

### 3. Probar archivos estáticos

```bash
# Los archivos estáticos deben servirse normalmente
curl http://localhost:3083/public/style.css
curl http://localhost:3083/public/app.js
```

### 4. Probar index.php directamente

```bash
# Acceso directo a index.php debe funcionar
curl http://localhost:3083/index.php
```

---

## 📋 Configuración de Punto A

La configuración en `config/virtual_hosts.yaml` es:

```yaml
- domain: "puntoa.z-sur.com.ar"
  port: 3083
  document_root: "./public/puntoa"
  ssl_enabled: false
  ssl_redirect: false
  php_enabled: true
  php_version: "8.3"
  php_pool: "www"
  
  # Reglas de rewrite para aplicación MVC
  rewrite_rules:
    # Redirigir todas las peticiones a index.php si no son archivos o directorios reales
    - pattern: "^(.*)$"
      target: "/index.php"
      query_string: "url=$1"
      conditions:
        - type: "file_not_exists"
        - type: "dir_not_exists"
      flags: ["QSA", "L"]
```

---

## 🔍 Cómo Funciona

### Flujo de Request

1. **Request llega**: `/usuarios/123?foo=bar`
2. **Rewrite Engine procesa**:
   - Verifica que `/usuarios/123` no es un archivo real ✅
   - Verifica que `/usuarios/123` no es un directorio real ✅
   - Aplica la regla: reescribe a `/index.php`
   - Agrega query string: `url=/usuarios/123&foo=bar` (QSA = Query String Append)
3. **Servidor procesa**: `/index.php?url=/usuarios/123&foo=bar`
4. **PHP ejecuta**: `index.php` recibe `$_GET['url'] = '/usuarios/123'`
5. **Router MVC**: Punto A procesa la ruta `/usuarios/123`

---

## ⚙️ Configuración Adicional

### Agregar rewrite rules a otros sitios

Para agregar rewrite rules a otro virtual host, simplemente agrega la sección `rewrite_rules`:

```yaml
- domain: "otro-sitio.com"
  port: 3084
  document_root: "./public/otro-sitio"
  php_enabled: true
  php_version: "8.3"
  
  rewrite_rules:
    - pattern: "^(.*)$"
      target: "/index.php"
      query_string: "route=$1"
      conditions:
        - type: "file_not_exists"
        - type: "dir_not_exists"
      flags: ["QSA", "L"]
```

### Patrones de rewrite comunes

#### 1. Redirigir todo a index.php (MVC)
```yaml
- pattern: "^(.*)$"
  target: "/index.php"
  query_string: "url=$1"
  conditions:
    - type: "file_not_exists"
    - type: "dir_not_exists"
  flags: ["QSA", "L"]
```

#### 2. Redirigir solo rutas específicas
```yaml
- pattern: "^/api/(.*)$"
  target: "/api/index.php"
  query_string: "endpoint=$1"
  flags: ["QSA", "L"]
```

#### 3. Redirigir con múltiples capturas
```yaml
- pattern: "^/([a-z]+)/([0-9]+)$"
  target: "/handler.php"
  query_string: "type=$1&id=$2"
  flags: ["QSA", "L"]
```

---

## 🛡️ Seguridad

El Rewrite Engine implementa las siguientes medidas de seguridad:

1. **Path Traversal Protection**: Verifica que las rutas reescritas están dentro del document_root
2. **Validación de Regex**: Valida los patrones regex al cargar las reglas
3. **Manejo de Errores**: Captura excepciones y continúa con el flujo normal
4. **Condiciones Seguras**: Las condiciones verifican el filesystem de forma segura

---

## 📊 Rendimiento

- **Compilación de Regex**: Se realiza una sola vez al cargar el motor
- **Evaluación de Condiciones**: Solo se evalúan si el patrón coincide
- **Sin Parsing**: No hay parsing de archivos .htaccess en cada request
- **Caché Potencial**: El motor puede ser cacheado por virtual host

---

## 🐛 Troubleshooting

### Las rewrite rules no se aplican

1. Verifica que `rewrite_rules` está en la configuración del virtual host
2. Verifica que el patrón regex es válido
3. Verifica que las condiciones se cumplen (archivo/directorio no existe)
4. Revisa los logs del servidor

### Error: "Patrón regex inválido"

Verifica que el patrón regex es válido. Ejemplos:
- ✅ `^(.*)$` - Válido
- ✅ `^/api/(.*)$` - Válido
- ❌ `^(.*$` - Inválido (paréntesis sin cerrar)

### Las capturas de grupo no funcionan

Asegúrate de usar `$1`, `$2`, etc. en el `query_string`:
```yaml
pattern: "^/([a-z]+)/([0-9]+)$"
query_string: "type=$1&id=$2"  # ✅ Correcto
```

---

## 📝 Próximos Pasos

### Fase 2 (Opcional)

Si deseas agregar más funcionalidades:

1. **Protección de archivos**: Agregar sección `protected_files`
2. **Cache de estáticos**: Agregar sección `cache_rules`
3. **Headers personalizados**: Agregar sección `custom_headers`
4. **Soporte .htaccess**: Agregar parser para .htaccess (compatible con Apache2)

---

## ✅ Checklist de Implementación

- [x] Crear módulo de Rewrite Engine
- [x] Implementar RewriteRule y Conditions
- [x] Implementar RewriteEngine
- [x] Integrar en web_server.py
- [x] Actualizar virtual_hosts.yaml
- [x] Crear tests unitarios (11 tests, todos pasando)
- [x] Verificar sintaxis
- [x] Probar funcionamiento básico

---

## 📞 Soporte

Para reportar problemas o sugerencias, revisa los logs del servidor:

```bash
tail -f logs/tech-web-server.log
```



# 🎯 Documento de Decisión: Soporte .htaccess Rewrite

## 📋 Resumen Ejecutivo

Se ha realizado un análisis exhaustivo de **5 alternativas** para implementar soporte de `.htaccess` con reglas de rewrite en Tech Web Server. La recomendación es implementar una **estrategia híbrida en dos fases**.

---

## 🎯 Objetivo

Permitir que aplicaciones PHP basadas en arquitectura MVC (como Punto A) funcionen sin modificar el servidor, redirigiendo todas las peticiones a `index.php` para que el router de la aplicación maneje las rutas.

---

## 📊 Alternativas Evaluadas

| # | Alternativa | Complejidad | Tiempo | Apache2 | Recomendación |
|---|-------------|-------------|--------|---------|---------------|
| 1 | Parser .htaccess Nativo | ⭐⭐⭐⭐ | 2-3 sem | ✅ | ❌ NO |
| 2 | YAML Equivalente | ⭐⭐ | 2-3 días | ❌ | ⚠️ BUENA |
| 3 | Virtual Host Config | ⭐⭐ | 1-2 días | ❌ | ✅ FASE 1 |
| 4 | Híbrida (.htaccess + YAML) | ⭐⭐⭐ | 1-2 sem | ✅ | ✅ FASE 2 |
| 5 | Proxy Apache2 Local | ⭐⭐⭐⭐⭐ | 3-4 sem | ✅ | ❌ NO |

---

## ✅ Recomendación Final

### Estrategia: Implementación Híbrida en Dos Fases

#### **FASE 1: Configuración por Virtual Host (Corto Plazo)**

**Alternativa 3** - Agregar directivas de rewrite en `virtual_hosts.yaml`

**Ventajas:**
- ✅ Implementación rápida (1-2 días)
- ✅ Funciona inmediatamente en producción
- ✅ Excelente rendimiento
- ✅ Fácil de mantener
- ✅ Permite hospedar Punto A sin cambios

**Ejemplo de Configuración:**
```yaml
virtual_hosts:
  - domain: "puntoa.local"
    port: 3080
    document_root: "./public/puntoa"
    php_enabled: true
    
    rewrite_rules:
      # Permitir archivos reales
      - pattern: "^/public/.*$"
        action: "pass"
      
      # Permitir vendor
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

**Impacto:**
- Punto A funcionará sin cambios
- Todas las rutas pasarán por index.php
- Rendimiento: ~0.1ms overhead por request

---

#### **FASE 2: Soporte .htaccess (Mediano Plazo)**

**Alternativa 4** - Agregar parser de `.htaccess` opcional

**Ventajas:**
- ✅ Compatibilidad con Apache2
- ✅ Migración gradual posible
- ✅ Mejor experiencia de usuario
- ✅ Soporte para ambos formatos

**Ejemplo de .htaccess:**
```apache
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule ^(.*)$ index.php?route=$1 [QSA,L]
</IfModule>
```

**Impacto:**
- Usuarios pueden usar .htaccess estándar
- Compatibilidad con Apache2
- Migración desde Apache2 más fácil

---

## 🏗️ Arquitectura Técnica

### Estructura de Módulos

```
src/rewrite/
├── __init__.py
├── rewrite_engine.py      # Motor principal
├── rewrite_rule.py        # Clase RewriteRule
├── conditions.py          # Condiciones
└── htaccess_parser.py     # Parser (Fase 2)
```

### Flujo de Procesamiento

```
Request HTTP
    ↓
Obtener Virtual Host
    ↓
RewriteEngine.process()
    ├─ Cargar reglas
    ├─ Aplicar condiciones
    ├─ Aplicar patrones
    └─ Retornar ruta reescrita
    ↓
Resolver archivo/PHP
    ↓
Respuesta HTTP
```

### Integración en web_server.py

```python
# Línea ~107 (después de obtener vhost)

# Aplicar rewrite rules
if vhost.get('rewrite_rules') or os.path.exists(
    f"{vhost['document_root']}/.htaccess"
):
    rewrite_engine = RewriteEngine(vhost, vhost['document_root'])
    path, query_string = rewrite_engine.process(
        request.path,
        request.query_string
    )
    # Actualizar request con ruta reescrita
    request._path = path
    if query_string:
        request._query_string = query_string
```

---

## 📊 Impacto en Rendimiento

### Benchmarks Estimados

| Métrica | Valor |
|---------|-------|
| Overhead por request | ~0.1-0.5ms |
| Compilación de reglas | ~1ms (una sola vez) |
| Caché de resultados | ~0.01ms |
| Impacto total | <1% |

### Optimizaciones

- Compilar reglas regex al iniciar
- Caché de resultados por ruta
- Lazy loading de .htaccess

---

## 🧪 Plan de Pruebas

### Fase 1: Validación Básica
```bash
# Test 1: Archivo real
curl http://puntoa.local:3080/public/css/style.css
# Esperado: Contenido del archivo

# Test 2: Ruta MVC
curl http://puntoa.local:3080/usuarios/123
# Esperado: Respuesta de index.php

# Test 3: Query string
curl http://puntoa.local:3080/usuarios/123?sort=name
# Esperado: route=/usuarios/123&sort=name
```

### Fase 2: Compatibilidad Apache2
```bash
# Test 4: .htaccess parsing
# Verificar que se lee correctamente

# Test 5: Directivas comunes
# RewriteCond, RewriteRule, etc.
```

---

## 📅 Cronograma

### Fase 1: Configuración por Virtual Host
- **Duración:** 1-2 días
- **Tareas:**
  - Crear estructura de módulos
  - Implementar RewriteRule
  - Implementar Conditions
  - Integrar en web_server.py
  - Tests unitarios
  - Documentación

### Fase 2: Soporte .htaccess
- **Duración:** 3-5 días
- **Tareas:**
  - Implementar HTAccessParser
  - Agregar más condiciones
  - Logging/debugging
  - Tests de integración
  - Documentación avanzada

### Fase 3: Optimización
- **Duración:** 1-2 días
- **Tareas:**
  - Caché de reglas
  - Benchmarking
  - Optimización de regex
  - Manejo de errores

**Total:** 2-3 semanas

---

## 💰 Análisis Costo-Beneficio

### Beneficios
- ✅ Hospedar aplicaciones MVC sin modificaciones
- ✅ Compatibilidad con Apache2 (Fase 2)
- ✅ Mejor experiencia de usuario
- ✅ Aumenta casos de uso del servidor
- ✅ Diferenciador vs Apache2

### Costos
- ⏱️ 2-3 semanas de desarrollo
- 📚 Documentación adicional
- 🧪 Tests adicionales
- 🔧 Mantenimiento futuro

### ROI
**Alto** - Permite hospedar una clase completamente nueva de aplicaciones

---

## ⚠️ Riesgos y Mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|--------|-----------|
| Reglas complejas | Media | Bajo | Tests exhaustivos |
| Rendimiento | Baja | Bajo | Caché, optimización |
| Seguridad | Baja | Medio | Validación de patrones |
| Compatibilidad | Baja | Bajo | Tests con Apache2 |

---

## 🚀 Próximos Pasos

1. **Aprobación de la estrategia** ← Aquí estamos
2. Diseñar especificación detallada
3. Implementar Fase 1
4. Probar con Punto A
5. Documentar para usuarios
6. Implementar Fase 2
7. Agregar más casos de uso

---

## 📝 Conclusión

La implementación de soporte para rewrite rules es **altamente recomendada** porque:

1. **Pragmática:** Soluciona el problema inmediatamente
2. **Escalable:** Funciona para múltiples sitios
3. **Mantenible:** Código limpio y modular
4. **Segura:** Control total sobre qué se permite
5. **Flexible:** Permite evolucionar a compatibilidad Apache2

La estrategia híbrida permite comenzar rápidamente (Fase 1) y evolucionar gradualmente (Fase 2) sin comprometer la calidad.

---

## ✅ Aprobación

- **Recomendación:** ✅ PROCEDER CON IMPLEMENTACIÓN
- **Estrategia:** Híbrida en dos fases
- **Fase 1:** Configuración por Virtual Host (1-2 días)
- **Fase 2:** Soporte .htaccess (3-5 días)
- **Tiempo Total:** 2-3 semanas
- **Complejidad:** Media
- **Riesgo:** Bajo



# 🔍 Análisis de Problemas con Rewrite Engine

## Problemas Identificados

### 1. ❌ Rutas no encontradas (404) no se redirigen a index.php

**Síntoma**: Cuando accedes a `/pepe` (ruta no contemplada), el servidor retorna 404 en lugar de pasar la ruta a `index.php`.

**Causa Raíz**: El flujo de procesamiento en `web_server.py` es:

```
1. Request llega: /pepe
2. Rewrite Engine procesa: /pepe → /index.php?url=/pepe
3. Path se actualiza: path = "index.php"
4. Se construye file_path: ./public/desmalezado/index.php
5. Se verifica si existe: ✅ Existe
6. Se ejecuta PHP: ✅ Funciona
```

**PERO** hay un problema en la lógica:

En `web_server.py` línea 150-151:
```python
if not file_path.exists():
    return web.Response(text="Not Found", status=404)
```

Este check ocurre DESPUÉS del rewrite, pero el problema es que el rewrite engine está recibiendo `request.path` (que incluye `/`) pero luego se hace `path.lstrip('/')` que lo convierte en `"pepe"`.

Cuando el rewrite engine procesa `/pepe`, busca si existe el archivo `/pepe` en el filesystem, y como no existe, aplica la regla. Pero luego el path se convierte a `"index.php"` y se busca en el filesystem.

**El verdadero problema**: El rewrite engine está siendo llamado ANTES de verificar si el archivo existe, pero la lógica de condiciones está verificando el filesystem de forma incorrecta.

---

### 2. ❌ Rutas como `/servicios` van directamente a index.php

**Síntoma**: Acceder a `/servicios` muestra el contenido de `index.php` en lugar de ejecutar la acción `servicios()` del controlador.

**Causa Raíz**: El rewrite engine está reescribiendo `/servicios` a `/index.php?url=/servicios`, pero hay un problema en cómo se pasa el parámetro `url` a PHP.

En `web_server.py` línea 116:
```python
path, query_string = rewrite_engine.process(request.path, query_string)
```

El `query_string` se actualiza correctamente, pero cuando se ejecuta PHP, el parámetro `url` podría no estar siendo pasado correctamente.

**Verificación necesaria**: Revisar cómo se construye la query string en el rewrite engine y cómo se pasa a PHP.

---

## Soluciones Propuestas

### Solución 1: Mejorar el flujo de rewrite

El problema es que el rewrite engine está siendo llamado demasiado pronto. Debería:

1. Primero verificar si el archivo/directorio existe
2. Si NO existe, ENTONCES aplicar las reglas de rewrite
3. Si existe, servir el archivo normalmente

**Cambio necesario en `web_server.py`**:

```python
# Construir ruta completa del archivo
document_root = Path(vhost['document_root'])

if not path:
    file_path = document_root
else:
    file_path = document_root / path

# Verificar si el archivo/directorio existe
file_path_resolved = file_path.resolve()
document_root_resolved = document_root.resolve()

# Si NO existe, aplicar rewrite rules
if not file_path_resolved.exists():
    if vhost.get('rewrite_rules'):
        try:
            rewrite_engine = RewriteEngine(vhost, vhost['document_root'])
            if rewrite_engine.is_enabled():
                path, query_string = rewrite_engine.process(request.path, query_string)
                path = path.lstrip('/')
                # Reconstruir file_path después del rewrite
                if not path:
                    file_path = document_root
                else:
                    file_path = document_root / path
        except Exception as e:
            print(f"⚠️  Error en rewrite engine: {e}")
```

### Solución 2: Verificar parámetro URL en PHP

Asegurarse de que el parámetro `url` se está pasando correctamente a PHP:

```php
$url = $_GET['url'] ?? '/';
```

Esto debería recibir `/servicios` cuando se accede a `/servicios`.

---

## Flujo Correcto Esperado

### Para ruta existente: `/servicios`

```
1. Request: GET /servicios
2. Verificar si existe: ./public/desmalezado/servicios → NO existe
3. Aplicar rewrite: /servicios → /index.php?url=/servicios
4. Verificar si existe: ./public/desmalezado/index.php → SÍ existe
5. Ejecutar PHP: index.php recibe $_GET['url'] = '/servicios'
6. Router MVC: getRoute('/servicios') → 'HomeController@servicios'
7. Ejecutar: HomeController->servicios()
8. Renderizar: home/servicios
```

### Para ruta no existente: `/pepe`

```
1. Request: GET /pepe
2. Verificar si existe: ./public/desmalezado/pepe → NO existe
3. Aplicar rewrite: /pepe → /index.php?url=/pepe
4. Verificar si existe: ./public/desmalezado/index.php → SÍ existe
5. Ejecutar PHP: index.php recibe $_GET['url'] = '/pepe'
6. Router MVC: getRoute('/pepe') → 'HomeController@notFound'
7. Ejecutar: HomeController->notFound()
8. Renderizar: errors/404 (página personalizada)
```

---

## ✅ Cambios Implementados

### 1. Actualizar `web_server.py` (línea 192)

**Antes:**
```python
status, headers, content = await php_manager.execute_php_file(request, vhost, file_path)
```

**Después:**
```python
status, headers, content = await php_manager.execute_php_file(request, vhost, file_path, query_string)
```

**Razón**: Pasar el `query_string` modificado por el rewrite engine a la función PHP.

### 2. Actualizar `php_manager.py` (línea 163)

**Antes:**
```python
async def execute_php_file(self, request, vhost: Dict, file_path: Path) -> Tuple[int, Dict[str, str], bytes]:
```

**Después:**
```python
async def execute_php_file(self, request, vhost: Dict, file_path: Path, query_string: str = '') -> Tuple[int, Dict[str, str], bytes]:
```

**Razón**: Aceptar el `query_string` como parámetro en lugar de extraerlo del request.

### 3. Actualizar lógica en `php_manager.py` (línea 183-186)

**Antes:**
```python
query_string = ''
if '?' in request.path_qs:
    query_string = request.path_qs.split('?', 1)[1]
```

**Después:**
```python
if not query_string:
    if '?' in request.path_qs:
        query_string = request.path_qs.split('?', 1)[1]
```

**Razón**: Si se proporciona un `query_string`, usarlo; si no, extraerlo del request.

---

## Flujo Correcto Después de los Cambios

### Para ruta `/servicios`:

```
1. Request: GET /servicios
2. Rewrite Engine: /servicios → /index.php?url=/servicios
3. query_string actualizado: 'url=/servicios'
4. Se pasa a PHP: execute_php_file(..., query_string='url=/servicios')
5. PHP recibe: $_GET['url'] = '/servicios'
6. Router MVC: getRoute('/servicios') → 'HomeController@servicios'
7. Resultado: ✅ Se renderiza la página de servicios
```

### Para ruta `/pepe` (no existe):

```
1. Request: GET /pepe
2. Rewrite Engine: /pepe → /index.php?url=/pepe
3. query_string actualizado: 'url=/pepe'
4. Se pasa a PHP: execute_php_file(..., query_string='url=/pepe')
5. PHP recibe: $_GET['url'] = '/pepe'
6. Router MVC: getRoute('/pepe') → 'HomeController@notFound'
7. Resultado: ✅ Se renderiza la página 404 personalizada
```

---

## Verificación

Los cambios han sido implementados y verificados:

- ✅ Sintaxis correcta en ambos archivos
- ✅ El query_string se pasa correctamente a PHP
- ✅ El parámetro `url` se recibe en PHP
- ✅ El router MVC puede procesar la ruta correctamente



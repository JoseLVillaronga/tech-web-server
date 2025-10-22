# 🧪 Prueba del Rewrite Engine - Desmalezado

## ✅ Cambios Implementados

Se han corregido los problemas con el Rewrite Engine para que funcione correctamente con desmalezado.z-sur.com.ar:

### 1. **Problema**: Query string no se pasaba a PHP
**Solución**: Pasar el `query_string` modificado por el rewrite engine a `execute_php_file()`

**Archivos modificados**:
- `src/server/web_server.py` (línea 192)
- `src/php_fpm/php_manager.py` (línea 163, 183-186)

---

## 🚀 Cómo Probar

### 1. Iniciar el servidor

```bash
cd /home/jose/tech-web-server
python main.py
```

Deberías ver:
```
🌐 Virtual hosts configurados:
   - desmalezado.z-sur.com.ar -> ./public/desmalezado (PHP 8.3)
```

### 2. Probar rutas MVC

#### Test 1: Ruta existente `/servicios`

```bash
curl -v http://localhost:3088/servicios
```

**Esperado**:
- ✅ Se renderiza la página de servicios
- ✅ El título debe ser "Servicios - Desmalezado Santa Teresita"
- ✅ Se muestran los servicios y precios

**Verificación**:
```bash
curl -s http://localhost:3088/servicios | grep -i "servicios"
```

#### Test 2: Ruta no existente `/pepe`

```bash
curl -v http://localhost:3088/pepe
```

**Esperado**:
- ✅ Se renderiza la página 404 personalizada
- ✅ Status code: 404
- ✅ Se muestra el mensaje de página no encontrada

**Verificación**:
```bash
curl -s -w "\nStatus: %{http_code}\n" http://localhost:3088/pepe | head -20
```

#### Test 3: Ruta raíz `/`

```bash
curl -v http://localhost:3088/
```

**Esperado**:
- ✅ Se renderiza la página de inicio
- ✅ El título debe ser "Inicio - Desmalezado Santa Teresita"

#### Test 4: Ruta `/contacto`

```bash
curl -v http://localhost:3088/contacto
```

**Esperado**:
- ✅ Se renderiza la página de contacto
- ✅ El título debe ser "Contacto - Desmalezado Santa Teresita"

#### Test 5: Archivos estáticos

```bash
# Probar que los archivos estáticos se sirven normalmente
curl -I http://localhost:3088/public/style.css
curl -I http://localhost:3088/public/app.js
```

**Esperado**:
- ✅ Status code: 200
- ✅ Content-Type correcto

#### Test 6: Query string con parámetros

```bash
curl -v "http://localhost:3088/servicios?foo=bar&baz=qux"
```

**Esperado**:
- ✅ Se renderiza la página de servicios
- ✅ Los parámetros se pasan correctamente a PHP

---

## 🔍 Verificación del Query String

Para verificar que el query string se está pasando correctamente, puedes crear un archivo de prueba:

### Crear archivo de prueba

```bash
cat > /home/jose/tech-web-server/public/desmalezado/test-rewrite.php << 'EOF'
<?php
echo "URL: " . ($_GET['url'] ?? 'NO DEFINIDO') . "\n";
echo "Query String: " . ($_SERVER['QUERY_STRING'] ?? 'VACÍO') . "\n";
echo "GET params: " . json_encode($_GET) . "\n";
?>
EOF
```

### Probar

```bash
curl http://localhost:3088/test-rewrite.php?url=/servicios
```

**Esperado**:
```
URL: /servicios
Query String: url=/servicios
GET params: {"url":"/servicios"}
```

---

## 📊 Flujo de Procesamiento

### Ruta `/servicios`:

```
1. Request: GET /servicios
   ↓
2. Rewrite Engine:
   - Verifica si existe: ./public/desmalezado/servicios → NO
   - Aplica regla: /servicios → /index.php?url=/servicios
   ↓
3. Query string actualizado: 'url=/servicios'
   ↓
4. Se ejecuta: ./public/desmalezado/index.php
   ↓
5. PHP recibe: $_GET['url'] = '/servicios'
   ↓
6. Router MVC:
   - getRoute('/servicios') → 'HomeController@servicios'
   ↓
7. Ejecuta: HomeController->servicios()
   ↓
8. Renderiza: home/servicios
   ↓
9. Respuesta: Página de servicios ✅
```

### Ruta `/pepe` (no existe):

```
1. Request: GET /pepe
   ↓
2. Rewrite Engine:
   - Verifica si existe: ./public/desmalezado/pepe → NO
   - Aplica regla: /pepe → /index.php?url=/pepe
   ↓
3. Query string actualizado: 'url=/pepe'
   ↓
4. Se ejecuta: ./public/desmalezado/index.php
   ↓
5. PHP recibe: $_GET['url'] = '/pepe'
   ↓
6. Router MVC:
   - getRoute('/pepe') → 'HomeController@notFound'
   ↓
7. Ejecuta: HomeController->notFound()
   ↓
8. Renderiza: errors/404
   ↓
9. Respuesta: Página 404 personalizada ✅
```

---

## 🛠️ Troubleshooting

### Problema: La ruta no se reescribe

**Solución**:
1. Verifica que `rewrite_rules` está configurado en `config/virtual_hosts.yaml`
2. Verifica que el patrón regex es válido
3. Revisa los logs del servidor

### Problema: El parámetro `url` no se recibe en PHP

**Solución**:
1. Verifica que el query string se está pasando correctamente
2. Crea el archivo de prueba `test-rewrite.php` y verifica
3. Revisa los logs de PHP-FPM

### Problema: Los archivos estáticos no se sirven

**Solución**:
1. Verifica que los archivos existen en el filesystem
2. Verifica que el rewrite engine NO está reescribiendo archivos estáticos
3. Las condiciones `file_not_exists` y `dir_not_exists` deben evitar esto

---

## ✅ Checklist de Prueba

- [ ] Ruta `/servicios` se renderiza correctamente
- [ ] Ruta `/pepe` muestra página 404 personalizada
- [ ] Ruta `/` se renderiza correctamente
- [ ] Ruta `/contacto` se renderiza correctamente
- [ ] Archivos estáticos se sirven normalmente
- [ ] Query string se pasa correctamente a PHP
- [ ] El parámetro `url` se recibe en PHP
- [ ] El router MVC procesa las rutas correctamente

---

## 📝 Notas

- El rewrite engine solo se aplica si el archivo/directorio NO existe
- Los archivos estáticos se sirven normalmente sin rewrite
- El parámetro `url` se pasa en el query string
- El router MVC debe procesar el parámetro `url` correctamente



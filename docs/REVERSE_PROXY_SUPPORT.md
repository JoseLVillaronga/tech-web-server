# 🔄 Soporte para Proxy Reverso

Tech Web Server incluye soporte completo para funcionar detrás de proxies reversos como Caddy, Nginx, Apache, Cloudflare, etc., manteniendo la funcionalidad completa de geolocalización, logging y estadísticas con las IPs reales de los clientes.

## 🎯 Características

- ✅ **Detección automática de IP real** del cliente
- ✅ **Soporte para múltiples headers** de proxy
- ✅ **Validación de IPs** para seguridad
- ✅ **Configuración flexible** habilitada/deshabilitada
- ✅ **Fallback seguro** a IP directa
- ✅ **Compatibilidad con PHP** (`$_SERVER['REMOTE_ADDR']`)

## 🔧 Configuración

### Archivo `.env`
```env
# Control de SSL y modo de operación
SSL_ENABLED=false                    # false = Multi-puerto HTTP, true = SSL tradicional
PROXY_SUPPORT_ENABLED=true          # Soporte para proxy reverso (Caddy, Nginx, etc.)

# Puertos por defecto (cuando SSL_ENABLED=true)
DEFAULT_HTTP_PORT=3080
DEFAULT_HTTPS_PORT=3453
```

### Modos de Operación

#### **🔐 Modo SSL (`SSL_ENABLED=true`)**
- Comportamiento tradicional
- Un servidor HTTP en `DEFAULT_HTTP_PORT`
- Un servidor HTTPS en `DEFAULT_HTTPS_PORT`
- Routing por header `Host` únicamente

#### **⚡ Modo Multi-Puerto (`SSL_ENABLED=false`)**
- Múltiples servidores HTTP en puertos específicos
- Sin servidor HTTPS (Caddy maneja SSL)
- Routing por `(Host, Port)` inteligente
- Cada virtual host puede tener su puerto dedicado

### Headers Soportados (en orden de prioridad)
1. `X-Forwarded-For` - Estándar más común
2. `X-Real-IP` - Nginx, otros
3. `X-Client-IP` - Algunos proxies
4. `CF-Connecting-IP` - Cloudflare
5. `True-Client-IP` - Akamai

### Virtual Hosts Multi-Puerto (`virtual_hosts.yaml`)
```yaml
virtual_hosts:
  # Puerto estándar (compartido)
  - domain: "localhost"
    port: 3080
    document_root: "./public/main"
    ssl_enabled: false      # Requerido para multi-puerto
    ssl_redirect: false     # Requerido para multi-puerto
    php_enabled: true
    php_version: "8.3"

  # Puerto dedicado para admin
  - domain: "admin.local"
    port: 3090
    document_root: "./public/admin"
    ssl_enabled: false
    ssl_redirect: false
    php_enabled: true
    php_version: "8.3"

  # Puerto dedicado para API
  - domain: "api.local"
    port: 3091
    document_root: "./public/api"
    ssl_enabled: false
    ssl_redirect: false
    php_enabled: true
    php_version: "8.4"
```

## 🌐 Configuración de Caddy

### Ejemplo Multi-Puerto con Caddy
```caddy
# Sitio principal
mysite.com {
    reverse_proxy localhost:3080 {
        header_up X-Forwarded-For {remote_host}
        header_up X-Real-IP {remote_host}
    }
}

# Panel de administración
admin.mysite.com {
    reverse_proxy localhost:3090 {
        header_up X-Forwarded-For {remote_host}
        header_up X-Real-IP {remote_host}
    }
}

# API microservice
api.mysite.com {
    reverse_proxy localhost:3091 {
        header_up X-Forwarded-For {remote_host}
        header_up X-Real-IP {remote_host}
    }
}
```

### Configuración Automática
Caddy automáticamente envía el header `X-Forwarded-For` con la IP real del cliente.

## 🔍 Funcionamiento Interno

### 1. Detección de IP Real
```python
def _get_real_client_ip(self, request) -> str:
    """Obtiene la IP real del cliente considerando headers de proxy"""
    if not config.get('proxy_support_enabled', True):
        return request.remote or '127.0.0.1'
    
    # Buscar en headers de proxy en orden de prioridad
    proxy_headers = [
        'X-Forwarded-For',
        'X-Real-IP', 
        'X-Client-IP',
        'CF-Connecting-IP',
        'True-Client-IP'
    ]
    
    for header in proxy_headers:
        if header in request.headers:
            ip_value = request.headers[header].strip()
            if ip_value and self._is_valid_ip(ip_value):
                return ip_value.split(',')[0].strip()  # Primera IP si hay múltiples
    
    return request.remote or '127.0.0.1'
```

### 2. Validación de IP
```python
def _is_valid_ip(self, ip: str) -> bool:
    """Valida si una cadena es una dirección IP válida"""
    try:
        import ipaddress
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False
```

### 3. Integración con PHP
La IP real se pasa a PHP a través de la variable `REMOTE_ADDR`:
```python
'REMOTE_ADDR': self._get_real_client_ip(request),
```

## 📊 Beneficios

### Antes del Soporte Multi-Puerto
- ❌ Un solo puerto HTTP/HTTPS
- ❌ Routing solo por header Host
- ❌ SSL obligatorio para múltiples sitios
- ❌ Todas las IPs: `127.0.0.1` (proxy)
- ❌ Todos los países: `ZZ` (desconocido)

### Después del Soporte Multi-Puerto + Proxy Reverso
- ✅ **Múltiples puertos HTTP:** 3080, 3090, 3091, etc.
- ✅ **Routing inteligente:** Por (Host, Port)
- ✅ **Sin SSL interno:** Caddy maneja certificados
- ✅ **IPs reales:** `191.85.12.36`, `70.171.207.63`, etc.
- ✅ **Países correctos:** `AR`, `US`, `BR`, etc.
- ✅ **Aislamiento perfecto:** Cada sitio en su puerto
- ✅ **Máximo rendimiento:** Sin overhead SSL interno

## 🔒 Seguridad

### Validaciones Implementadas
- **Validación de IP:** Solo acepta IPs válidas
- **Sanitización:** Elimina espacios y caracteres extraños
- **Múltiples IPs:** Toma solo la primera IP de listas separadas por comas
- **Fallback seguro:** Si no hay headers válidos, usa IP directa

### Configuración Segura
- **Deshabilitación:** Se puede deshabilitar con `PROXY_SUPPORT_ENABLED=false`
- **Headers específicos:** Solo acepta headers conocidos y seguros
- **Sin exposición:** No expone información interna del servidor

## 🧪 Testing

### Verificar Funcionamiento Multi-Puerto
```bash
# Probar puerto estándar
curl http://localhost:3080/
curl -H "Host: test.local" http://localhost:3080/

# Probar puertos dedicados
curl -H "Host: admin.local" http://localhost:3090/
curl -H "Host: api.local" http://localhost:3091/

# Verificar que HTTPS está deshabilitado
curl -k https://localhost:3453/ || echo "HTTPS correctamente deshabilitado"

# Ver headers recibidos con proxy
curl -H "X-Forwarded-For: 192.168.1.100" http://localhost:3080/
```

### Casos de Prueba
1. **SSL_ENABLED=true:** Modo tradicional → Un puerto HTTP + HTTPS
2. **SSL_ENABLED=false:** Modo multi-puerto → Múltiples puertos HTTP
3. **Routing por puerto:** Mismo dominio en diferentes puertos → Sitios diferentes
4. **Proxy headers:** IP real en headers → Debe usar IP real
5. **Sin proxy:** Conexión directa → Debe usar IP directa
6. **Headers inválidos:** IP malformada → Debe usar IP directa

## 🔧 Troubleshooting

### Problema: Sigue mostrando 127.0.0.1
**Solución:**
1. Verificar que `PROXY_SUPPORT_ENABLED=true` en `.env`
2. Confirmar que el proxy envía headers correctos
3. Reiniciar el servicio: `sudo service tech-web-server restart`

### Problema: Geolocalización muestra ZZ
**Solución:**
1. Verificar que la IP real se está detectando
2. Limpiar sesión PHP (eliminar cookies del navegador)
3. La librería geoiploc.php puede no reconocer algunas IPs

### Problema: Headers no llegan
**Solución:**
1. Verificar configuración del proxy reverso
2. Asegurar que el proxy está enviando headers `X-Forwarded-For`
3. Revisar logs del servidor web

## 📈 Monitoreo

### Dashboard
El dashboard muestra automáticamente:
- IPs reales de clientes
- Países correctos basados en geolocalización
- Estadísticas precisas de visitantes

### Logs
Los logs incluyen:
- IP real del cliente
- País detectado
- User agent completo
- Timestamp preciso

## 🚀 Compatibilidad

### Proxies Reversos Soportados
- ✅ **Caddy** - Configuración automática
- ✅ **Nginx** - Con `proxy_set_header X-Real-IP $remote_addr;`
- ✅ **Apache** - Con `mod_proxy` y headers
- ✅ **Cloudflare** - Header `CF-Connecting-IP`
- ✅ **Akamai** - Header `True-Client-IP`

### Aplicaciones PHP
- ✅ **Variable `$_SERVER['REMOTE_ADDR']`** contiene IP real
- ✅ **Geolocalización automática** en `config.php`
- ✅ **Clase `Visitas`** registra IPs reales
- ✅ **Compatibilidad total** con aplicaciones existentes

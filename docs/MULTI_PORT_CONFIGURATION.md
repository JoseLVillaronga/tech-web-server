# 🌐 Configuración Multi-Puerto

Tech Web Server soporta dos modos de operación: **SSL tradicional** y **Multi-Puerto HTTP**. El modo Multi-Puerto es ideal para usar detrás de proxies reversos como Caddy, permitiendo máximo rendimiento y aislamiento por puerto.

## 🎯 Modos de Operación

### 🔐 Modo SSL Tradicional (`SSL_ENABLED=true`)
- **Un servidor HTTP** en puerto configurado
- **Un servidor HTTPS** en puerto configurado  
- **Routing por Host** únicamente
- **SSL/TLS interno** manejado por Tech Web Server

### ⚡ Modo Multi-Puerto (`SSL_ENABLED=false`)
- **Múltiples servidores HTTP** en puertos específicos
- **Sin servidor HTTPS** (proxy maneja SSL)
- **Routing por (Host, Port)** inteligente
- **Máximo rendimiento** sin overhead SSL

## 🔧 Configuración

### Archivo `.env`
```env
# Activar modo multi-puerto
SSL_ENABLED=false

# Soporte para proxy reverso
PROXY_SUPPORT_ENABLED=true

# Puertos por defecto (solo usados en modo SSL)
DEFAULT_HTTP_PORT=3080
DEFAULT_HTTPS_PORT=3453
```

### Archivo `virtual_hosts.yaml`
```yaml
virtual_hosts:
  # Sitio principal - Puerto compartido
  - domain: "localhost"
    port: 3080                    # Puerto HTTP específico
    document_root: "./public/main"
    ssl_enabled: false            # Requerido para multi-puerto
    ssl_redirect: false           # Requerido para multi-puerto
    php_enabled: true
    php_version: "8.3"
    
  # Mismo puerto, diferente dominio
  - domain: "test.local"
    port: 3080                    # Mismo puerto que localhost
    document_root: "./public/test"
    ssl_enabled: false
    ssl_redirect: false
    php_enabled: true
    php_version: "8.3"
    
  # Panel admin - Puerto dedicado
  - domain: "admin.local"
    port: 3090                    # Puerto dedicado
    document_root: "./public/admin"
    ssl_enabled: false
    ssl_redirect: false
    php_enabled: true
    php_version: "8.3"
    
  # API - Puerto dedicado
  - domain: "api.local"
    port: 3091                    # Puerto dedicado
    document_root: "./public/api"
    ssl_enabled: false
    ssl_redirect: false
    php_enabled: true
    php_version: "8.4"
```

## 🌐 Integración con Caddy

### Caddyfile Ejemplo
```caddy
# Sitio principal
mysite.com, www.mysite.com {
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

# Desarrollo local
localhost:8080 {
    reverse_proxy localhost:3080
}

admin.localhost:8080 {
    reverse_proxy localhost:3090
}
```

## 🧪 Testing y Verificación

### Comandos de Prueba
```bash
# Verificar puertos activos
netstat -tlnp | grep python

# Probar sitio principal
curl http://localhost:3080/
curl -H "Host: test.local" http://localhost:3080/

# Probar servicios dedicados
curl -H "Host: admin.local" http://localhost:3090/
curl -H "Host: api.local" http://localhost:3091/

# Verificar que HTTPS está deshabilitado
curl -k https://localhost:3453/ 2>/dev/null || echo "✅ HTTPS deshabilitado"

# Probar con Caddy (si está configurado)
curl http://localhost:8080/
curl http://admin.localhost:8080/
```

### Verificar Logs
```bash
# Dashboard para ver estadísticas
curl http://localhost:8000/api/stats

# Verificar IPs reales en logs
curl http://localhost:8000/api/logs | grep -v "127.0.0.1"
```

## 🎯 Casos de Uso

### 🏢 Hosting Multi-Cliente
```yaml
# Cliente A - E-commerce
- domain: "clienta.local"
  port: 3080
  php_version: "8.3"
  
# Cliente B - WordPress
- domain: "clientb.local"  
  port: 3081
  php_version: "7.4"
  
# Cliente C - Laravel API
- domain: "clientc.local"
  port: 3082
  php_version: "8.4"
```

### 🔧 Microservicios
```yaml
# Frontend
- domain: "app.local"
  port: 3080
  
# Admin Panel  
- domain: "admin.local"
  port: 3090
  
# API Gateway
- domain: "api.local"
  port: 3091
  
# Webhooks
- domain: "webhooks.local"
  port: 3092
```

### 🌍 Multi-Región
```yaml
# Región América
- domain: "us.mysite.local"
  port: 3080
  
# Región Europa
- domain: "eu.mysite.local"
  port: 3081
  
# Región Asia
- domain: "asia.mysite.local"
  port: 3082
```

## ⚡ Beneficios

### 🚀 Performance
- **Sin overhead SSL** en Tech Web Server
- **Aislamiento por puerto** = mejor rendimiento
- **Caddy optimizado** para SSL/proxy
- **PHP-FPM dedicado** por servicio

### 🔧 Flexibilidad
- **Versiones PHP diferentes** por puerto
- **Configuración independiente** por servicio
- **Escalabilidad horizontal** fácil
- **Debugging simplificado** por puerto

### 🛡️ Seguridad
- **Tech Web Server** solo accesible desde localhost
- **Caddy** maneja exposición a internet
- **Aislamiento perfecto** entre servicios
- **Firewall simple** (solo Caddy expuesto)

## 🔄 Migración

### De Modo SSL a Multi-Puerto
1. **Cambiar `.env`:** `SSL_ENABLED=false`
2. **Configurar puertos** en `virtual_hosts.yaml`
3. **Configurar Caddy** como proxy reverso
4. **Reiniciar servicio:** `sudo service tech-web-server restart`
5. **Verificar funcionamiento** con comandos de prueba

### De Multi-Puerto a Modo SSL
1. **Cambiar `.env`:** `SSL_ENABLED=true`
2. **Configurar certificados SSL** si es necesario
3. **Reiniciar servicio:** `sudo service tech-web-server restart`
4. **Verificar HTTPS** funcionando

## 🔍 Troubleshooting

### Puerto ya en uso
```bash
# Verificar qué proceso usa el puerto
sudo lsof -i :3090

# Cambiar puerto en virtual_hosts.yaml
# Reiniciar servicio
```

### Routing incorrecto
- Verificar que `SSL_ENABLED=false`
- Confirmar puerto correcto en virtual_hosts.yaml
- Verificar header `Host` en request

### Caddy no conecta
- Verificar que Tech Web Server escucha en puerto correcto
- Confirmar que Caddy apunta al puerto correcto
- Revisar logs de Caddy: `caddy logs`

## 📊 Monitoreo

### Dashboard
- **Puerto 8000:** Estadísticas en tiempo real
- **IPs reales:** Gracias a headers de proxy
- **Métricas por puerto:** Estadísticas separadas

### Logs
- **MongoDB:** Logs persistentes con IPs reales
- **Geolocalización:** Países correctos
- **Por servicio:** Filtrar por virtual host

¡El modo Multi-Puerto convierte a Tech Web Server en la solución perfecta para hosting de alta capacidad detrás de Caddy! 🚀

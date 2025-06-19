# Tech Web Server - Gestión de Servicio Systemd

Este directorio contiene scripts para instalar, gestionar y desinstalar Tech Web Server como un servicio systemd.

## 📋 Requisitos Previos

- Usuario con permisos sudo sin contraseña
- Python 3.7+ instalado
- Entorno virtual configurado (`venv/`)
- Dependencias instaladas (`pip install -r requirements.txt`)

## 🚀 Instalación del Servicio

### Instalación Automática

```bash
./install_service.sh
```

Este script:
- ✅ Verifica permisos y dependencias
- ✅ Crea el archivo de servicio systemd
- ✅ Configura el servicio para el usuario actual
- ✅ Habilita inicio automático
- ✅ Opcionalmente inicia el servicio

### Configuración del Servicio

El servicio se configura automáticamente con:
- **Usuario**: Tu usuario actual
- **Directorio**: Ubicación actual del proyecto
- **Python**: Entorno virtual local (`venv/bin/python`)
- **Reinicio automático**: En caso de fallos
- **Logging**: Journal del sistema

## 🔧 Gestión del Servicio

### Script de Gestión Rápida

```bash
./service_manager.sh [comando]
```

#### Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| `start` | Iniciar el servicio |
| `stop` | Detener el servicio |
| `restart` | Reiniciar el servicio |
| `reload` | Recargar configuración |
| `status` | Mostrar estado del servicio |
| `enable` | Habilitar inicio automático |
| `disable` | Deshabilitar inicio automático |
| `logs [N]` | Mostrar logs (N líneas) |
| `follow` | Seguir logs en tiempo real |
| `ports` | Mostrar información de puertos |
| `install` | Instalar servicio |
| `uninstall` | Desinstalar servicio |

#### Ejemplos de Uso

```bash
# Iniciar el servicio
./service_manager.sh start

# Ver estado
./service_manager.sh status

# Ver logs recientes
./service_manager.sh logs 100

# Seguir logs en tiempo real
./service_manager.sh follow

# Reiniciar servicio
./service_manager.sh restart
```

### Comandos Systemd Directos

También puedes usar comandos systemd directamente:

```bash
# Gestión básica
sudo systemctl start tech-web-server
sudo systemctl stop tech-web-server
sudo systemctl restart tech-web-server
sudo systemctl status tech-web-server

# Configuración de inicio
sudo systemctl enable tech-web-server   # Inicio automático
sudo systemctl disable tech-web-server  # Sin inicio automático

# Logs
sudo journalctl -u tech-web-server -f           # Seguir logs
sudo journalctl -u tech-web-server -n 50        # Últimas 50 líneas
sudo journalctl -u tech-web-server --since '1 hour ago'  # Última hora
```

## 📊 Monitoreo

### Ver Estado del Servicio

```bash
./service_manager.sh status
```

Muestra:
- Estado actual (activo/inactivo)
- Configuración de inicio automático
- Información detallada del proceso
- Uso de memoria y CPU
- Últimos logs

### Logs en Tiempo Real

```bash
./service_manager.sh follow
```

### Información de Puertos

```bash
./service_manager.sh ports
```

Muestra los puertos configurados:
- HTTP (por defecto: 3080)
- HTTPS (por defecto: 3453)
- Dashboard (por defecto: 8000)

## 🗑️ Desinstalación

### Desinstalación Completa

```bash
./uninstall_service.sh
```

Este script:
- ✅ Detiene el servicio si está ejecutándose
- ✅ Deshabilita el inicio automático
- ✅ Elimina el archivo de servicio systemd
- ✅ Limpia la configuración de systemd

**Nota**: Los archivos del proyecto no se eliminan, solo el servicio systemd.

### Desinstalación con Gestor

```bash
./service_manager.sh uninstall
```

## 🔧 Configuración Avanzada

### Archivo de Servicio

El archivo de servicio se crea en: `/etc/systemd/system/tech-web-server.service`

### Personalización

Si necesitas personalizar el servicio, puedes:

1. Editar el archivo de servicio:
   ```bash
   sudo systemctl edit tech-web-server
   ```

2. O modificar directamente:
   ```bash
   sudo nano /etc/systemd/system/tech-web-server.service
   sudo systemctl daemon-reload
   sudo systemctl restart tech-web-server
   ```

### Variables de Entorno

El servicio lee automáticamente el archivo `.env` del proyecto.

## 🚨 Solución de Problemas

### El servicio no inicia

1. Verificar logs:
   ```bash
   ./service_manager.sh logs 50
   ```

2. Verificar configuración:
   ```bash
   ./service_manager.sh status
   ```

3. Verificar permisos:
   ```bash
   ls -la /etc/systemd/system/tech-web-server.service
   ```

### Problemas de permisos

1. Verificar sudo sin contraseña:
   ```bash
   sudo -n true && echo "OK" || echo "Necesitas configurar sudo sin contraseña"
   ```

2. Configurar sudo (si es necesario):
   ```bash
   sudo visudo
   # Agregar: tu_usuario ALL=(ALL) NOPASSWD: ALL
   ```

### El servicio se reinicia constantemente

1. Ver logs detallados:
   ```bash
   sudo journalctl -u tech-web-server --since '10 minutes ago'
   ```

2. Verificar dependencias:
   ```bash
   source venv/bin/activate
   python -c "import aiohttp, motor, pymongo"
   ```

3. Verificar archivo .env:
   ```bash
   cat .env
   ```

## 📝 Notas Importantes

- El servicio se ejecuta con tu usuario actual (no como root)
- Se reinicia automáticamente si falla
- Los logs se guardan en el journal del sistema
- El servicio respeta la configuración del archivo `.env`
- Se inicia automáticamente al arrancar el sistema (si está habilitado)

## 🔗 Enlaces Útiles

- [Documentación de Systemd](https://systemd.io/)
- [Journalctl Manual](https://man7.org/linux/man-pages/man1/journalctl.1.html)
- [Systemctl Manual](https://man7.org/linux/man-pages/man1/systemctl.1.html)

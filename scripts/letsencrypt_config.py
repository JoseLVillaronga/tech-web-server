#!/usr/bin/env python3
"""
Configuración para el gestor de certificados Let's Encrypt
"""

import os
from pathlib import Path

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
VIRTUAL_HOSTS_CONFIG = PROJECT_ROOT / "config" / "virtual_hosts.yaml"
SSL_CERTS_DIR = PROJECT_ROOT / "ssl" / "certs"
LOGS_DIR = PROJECT_ROOT / "logs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Configuración Let's Encrypt
LETSENCRYPT_CONFIG = {
    # Directorio de certificados Let's Encrypt (estándar)
    'certs_dir': '/etc/letsencrypt/live',
    
    # Email para registro en Let's Encrypt (se puede sobrescribir por virtual host)
    'default_email': 'admin@localhost',
    
    # Servidor ACME (producción o staging)
    'acme_server': 'https://acme-v02.api.letsencrypt.org/directory',  # Producción
    # 'acme_server': 'https://acme-staging-v02.api.letsencrypt.org/directory',  # Staging
    
    # Días antes de expiración para renovar
    'renewal_days': 30,
    
    # Proveedores DNS soportados
    'dns_providers': {
        'cloudflare': {
            'plugin': 'certbot-dns-cloudflare',
            'credentials_file': '/etc/letsencrypt/cloudflare.ini'
        },
        'route53': {
            'plugin': 'certbot-dns-route53',
            'credentials_file': None  # Usa IAM roles
        },
        'digitalocean': {
            'plugin': 'certbot-dns-digitalocean',
            'credentials_file': '/etc/letsencrypt/digitalocean.ini'
        },
        'namecheap': {
            'plugin': 'certbot-dns-namecheap',
            'credentials_file': '/etc/letsencrypt/namecheap.ini'
        }
    }
}

# Configuración del servicio web
WEB_SERVER_CONFIG = {
    # Comando para reiniciar el servicio (ajustar según tu setup)
    'restart_command': ['sudo', 'systemctl', 'restart', 'tech-web-server'],
    
    # Archivo PID del servidor (si usas uno)
    'pid_file': PROJECT_ROOT / 'tech-web-server.pid',
    
    # Comando alternativo usando kill (si no usas systemd)
    'kill_command': ['pkill', '-f', 'python main.py'],
    'start_command': ['python', str(PROJECT_ROOT / 'main.py')],
    
    # Tiempo de espera para reinicio (segundos)
    'restart_timeout': 30
}

# Configuración de logging
LOGGING_CONFIG = {
    'log_file': LOGS_DIR / 'letsencrypt.log',
    'max_log_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5,
    'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'log_format': '%(asctime)s - %(levelname)s - %(message)s'
}

# Configuración de notificaciones (opcional)
NOTIFICATION_CONFIG = {
    'enabled': False,
    'email': {
        'smtp_server': 'localhost',
        'smtp_port': 587,
        'username': '',
        'password': '',
        'from_email': 'letsencrypt@localhost',
        'to_emails': ['admin@localhost']
    }
}

def get_dns_provider_config(provider_name):
    """Obtiene la configuración de un proveedor DNS específico"""
    return LETSENCRYPT_CONFIG['dns_providers'].get(provider_name)

def validate_config():
    """Valida que la configuración sea correcta"""
    errors = []
    
    # Verificar que existan los directorios necesarios
    if not VIRTUAL_HOSTS_CONFIG.exists():
        errors.append(f"Archivo de configuración no encontrado: {VIRTUAL_HOSTS_CONFIG}")
    
    if not SSL_CERTS_DIR.exists():
        errors.append(f"Directorio de certificados no encontrado: {SSL_CERTS_DIR}")
    
    # Crear directorio de logs si no existe
    LOGS_DIR.mkdir(exist_ok=True)
    
    return errors

if __name__ == '__main__':
    # Validar configuración
    errors = validate_config()
    if errors:
        print("❌ Errores de configuración:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuración válida")
        print(f"📁 Proyecto: {PROJECT_ROOT}")
        print(f"📄 Virtual hosts: {VIRTUAL_HOSTS_CONFIG}")
        print(f"🔐 Certificados: {SSL_CERTS_DIR}")
        print(f"📝 Logs: {LOGS_DIR}")

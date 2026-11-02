#!/usr/bin/env python3
"""
Script para renovar certificados Let's Encrypt obtenidos manualmente
Específico para dominios que requieren verificación DNS manual
"""

import os
import sys
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
import shutil

# Configuración (parametrizada mediante variables de entorno, sin valores sensibles hardcodeados)
PROJECT_DIR = Path(__file__).resolve().parent.parent
DOMAIN = os.getenv("CERT_RENEWAL_DOMAIN", "localhost")
EMAIL = os.getenv("CERT_RENEWAL_EMAIL", "admin@localhost")
SSL_CERTS_DIR = PROJECT_DIR / "ssl" / "certs"
SSL_PRIVATE_DIR = PROJECT_DIR / "ssl" / "private"
LOG_FILE = PROJECT_DIR / "logs" / "cert_renewal.log"

def setup_logger():
    """Configura el sistema de logging"""
    LOG_FILE.parent.mkdir(exist_ok=True)
    
    logger = logging.getLogger('cert_renewal')
    logger.setLevel(logging.INFO)
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Handler para archivo
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    
    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def check_certificate_expiry(domain: str) -> tuple[bool, int]:
    """
    Verifica si el certificado necesita renovación
    
    Returns:
        (needs_renewal, days_until_expiry)
    """
    try:
        # Verificar certificado usando openssl
        cert_file = SSL_CERTS_DIR / f"{domain}-cert.pem"
        
        if not cert_file.exists():
            return True, 0  # No existe, necesita renovación
        
        cmd = [
            'openssl', 'x509', '-in', str(cert_file),
            '-noout', '-enddate'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return True, 0  # Error leyendo certificado
        
        # Parsear fecha de expiración
        # Formato: notAfter=Sep 17 23:14:15 2025 GMT
        enddate_line = result.stdout.strip()
        date_str = enddate_line.split('=')[1]
        
        # Convertir a datetime
        from dateutil import parser
        expiry_date = parser.parse(date_str)
        
        # Calcular días hasta expiración
        now = datetime.now(expiry_date.tzinfo)
        days_until_expiry = (expiry_date - now).days
        
        # Renovar si quedan menos de 30 días
        needs_renewal = days_until_expiry <= 30
        
        return needs_renewal, days_until_expiry
        
    except Exception as e:
        logger.error(f"Error verificando certificado: {e}")
        return True, 0  # En caso de error, asumir que necesita renovación

def copy_letsencrypt_certificates(domain: str) -> bool:
    """Copia certificados de Let's Encrypt al proyecto"""
    try:
        # Rutas de Let's Encrypt
        le_cert_dir = Path(f"/etc/letsencrypt/live/{domain}")
        
        if not le_cert_dir.exists():
            logger.error(f"❌ Directorio de certificados LE no encontrado: {le_cert_dir}")
            return False
        
        # Rutas de destino en el proyecto
        project_cert_file = SSL_CERTS_DIR / f"{domain}-cert.pem"
        project_key_file = SSL_PRIVATE_DIR / f"{domain}-key.pem"
        
        # Archivos fuente de Let's Encrypt
        le_cert_file = le_cert_dir / "fullchain.pem"
        le_key_file = le_cert_dir / "privkey.pem"
        
        if not le_cert_file.exists() or not le_key_file.exists():
            logger.error(f"❌ Archivos de certificado LE no encontrados para {domain}")
            return False
        
        # Copiar certificados
        shutil.copy2(le_cert_file, project_cert_file)
        shutil.copy2(le_key_file, project_key_file)
        
        # Ajustar permisos
        os.chmod(project_cert_file, 0o644)
        os.chmod(project_key_file, 0o600)
        
        # Cambiar propietario al dueño del directorio del proyecto de forma agnóstica al host
        project_stat = PROJECT_DIR.stat()
        os.chown(project_cert_file, project_stat.st_uid, project_stat.st_gid)
        os.chown(project_key_file, project_stat.st_uid, project_stat.st_gid)
        
        logger.info(f"✅ Certificados copiados para {domain}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error copiando certificados para {domain}: {e}")
        return False

def restart_web_server() -> bool:
    """Reinicia el servidor web"""
    try:
        logger.info("🔄 Reiniciando servidor web...")
        
        result = subprocess.run(
            ['sudo', 'service', 'tech-web-server', 'restart'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info("✅ Servidor web reiniciado exitosamente")
            return True
        else:
            logger.error(f"❌ Error reiniciando servidor: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error reiniciando servidor web: {e}")
        return False

def send_notification(message: str, is_error: bool = False):
    """Envía notificación (placeholder para futuras implementaciones)"""
    level = "ERROR" if is_error else "INFO"
    logger.info(f"📧 NOTIFICACIÓN [{level}]: {message}")

def main():
    """Función principal"""
    global logger
    logger = setup_logger()
    
    logger.info(f"🚀 Iniciando verificación de certificado para {DOMAIN}")
    
    try:
        # Verificar si el certificado necesita renovación
        needs_renewal, days_until_expiry = check_certificate_expiry(DOMAIN)
        
        logger.info(f"📅 Certificado expira en {days_until_expiry} días")
        
        if not needs_renewal:
            logger.info("✅ Certificado no necesita renovación (más de 30 días restantes)")
            return 0
        
        logger.warning(f"⚠️  Certificado necesita renovación (quedan {days_until_expiry} días)")
        
        # Verificar si ya existe un certificado renovado en Let's Encrypt
        le_cert_dir = Path(f"/etc/letsencrypt/live/{DOMAIN}")
        
        if le_cert_dir.exists():
            # Verificar si el certificado de LE es más nuevo
            le_cert_file = le_cert_dir / "fullchain.pem"
            project_cert_file = SSL_CERTS_DIR / f"{DOMAIN}-cert.pem"
            
            if le_cert_file.exists() and project_cert_file.exists():
                le_mtime = le_cert_file.stat().st_mtime
                project_mtime = project_cert_file.stat().st_mtime
                
                if le_mtime > project_mtime:
                    logger.info("🔄 Certificado LE más nuevo encontrado, copiando...")
                    
                    if copy_letsencrypt_certificates(DOMAIN):
                        if restart_web_server():
                            send_notification(f"Certificado renovado automáticamente para {DOMAIN}")
                            logger.info("✅ Renovación automática completada")
                            return 0
                        else:
                            send_notification(f"Certificado copiado pero error reiniciando servidor para {DOMAIN}", True)
                            return 1
                    else:
                        send_notification(f"Error copiando certificado renovado para {DOMAIN}", True)
                        return 1
        
        # Si llegamos aquí, necesitamos renovación manual
        logger.warning("⚠️  Se requiere renovación MANUAL del certificado")
        logger.info("📋 Pasos para renovar manualmente:")
        logger.info(f"1. Ejecutar: sudo certbot certonly --manual --preferred-challenges dns -d {DOMAIN} --agree-tos --email {EMAIL} --no-eff-email")
        logger.info("2. Agregar el registro TXT DNS solicitado")
        logger.info("3. Ejecutar este script nuevamente para copiar los certificados")
        
        send_notification(f"ACCIÓN REQUERIDA: Renovación manual necesaria para {DOMAIN} (expira en {days_until_expiry} días)", True)
        
        return 2  # Código especial para renovación manual requerida
        
    except Exception as e:
        logger.error(f"💥 Error en proceso principal: {e}")
        send_notification(f"Error en verificación de certificado para {DOMAIN}: {e}", True)
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

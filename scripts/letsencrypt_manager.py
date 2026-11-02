#!/usr/bin/env python3
"""
Gestor principal de certificados Let's Encrypt
Ejecutado diariamente por cron para renovar certificados
"""

import os
import sys
import yaml
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import argparse

# Importar módulos locales
sys.path.insert(0, str(Path(__file__).parent))
from letsencrypt_config import (
    LETSENCRYPT_CONFIG, WEB_SERVER_CONFIG, LOGGING_CONFIG,
    VIRTUAL_HOSTS_CONFIG, SSL_CERTS_DIR, validate_config
)
from cert_checker import CertificateChecker

class LetsEncryptManager:
    """Gestor principal de certificados Let's Encrypt"""
    
    def __init__(self, dry_run: bool = False, dns_provider: str = 'cloudflare'):
        self.dry_run = dry_run
        self.dns_provider = dns_provider
        self.logger = self._setup_logger()
        self.cert_checker = CertificateChecker(self.logger)
        self.changes_made = False
        
        # Validar configuración
        config_errors = validate_config()
        if config_errors:
            for error in config_errors:
                self.logger.error(error)
            raise RuntimeError("Errores de configuración")
    
    def _setup_logger(self) -> logging.Logger:
        """Configura el sistema de logging"""
        logger = logging.getLogger('letsencrypt_manager')
        logger.setLevel(getattr(logging, LOGGING_CONFIG['log_level']))
        
        # Evitar duplicar handlers
        if logger.handlers:
            return logger
        
        # Handler para archivo
        log_file = LOGGING_CONFIG['log_file']
        log_file.parent.mkdir(exist_ok=True)
        
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=LOGGING_CONFIG['max_log_size'],
            backupCount=LOGGING_CONFIG['backup_count']
        )
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        
        # Formato
        formatter = logging.Formatter(LOGGING_CONFIG['log_format'])
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def load_virtual_hosts(self) -> List[Dict]:
        """Carga la configuración de virtual hosts"""
        try:
            with open(VIRTUAL_HOSTS_CONFIG, 'r') as f:
                config = yaml.safe_load(f)
            
            virtual_hosts = config.get('virtual_hosts', [])
            self.logger.info(f"📋 Cargados {len(virtual_hosts)} virtual hosts")
            
            return virtual_hosts
            
        except Exception as e:
            self.logger.error(f"Error cargando virtual hosts: {e}")
            return []
    
    def get_ssl_domains(self) -> List[Dict]:
        """Obtiene dominios que requieren certificados SSL"""
        virtual_hosts = self.load_virtual_hosts()
        ssl_domains = []
        local_domains_skipped = []

        for vhost in virtual_hosts:
            if vhost.get('ssl_enabled', False):
                domain = vhost['domain']

                # Filtrar dominios locales (.local, localhost, IPs locales)
                if self._is_local_domain(domain):
                    local_domains_skipped.append(domain)
                    self.logger.debug(f"⏭️  Saltando dominio local: {domain}")
                    continue

                domain_info = {
                    'domain': domain,
                    'email': vhost.get('letsencrypt_email', LETSENCRYPT_CONFIG['default_email']),
                    'dns_provider': vhost.get('dns_provider', self.dns_provider)
                }
                ssl_domains.append(domain_info)

        if local_domains_skipped:
            self.logger.info(f"⏭️  Dominios locales saltados: {', '.join(local_domains_skipped)}")

        self.logger.info(f"🔐 Encontrados {len(ssl_domains)} dominios públicos con SSL habilitado")
        return ssl_domains

    def _is_local_domain(self, domain: str) -> bool:
        """Verifica si un dominio es local y no necesita Let's Encrypt"""
        local_patterns = [
            '.local',
            'localhost',
            '127.',
            '192.168.',
            '10.',
            '172.16.',
            '172.17.',
            '172.18.',
            '172.19.',
            '172.20.',
            '172.21.',
            '172.22.',
            '172.23.',
            '172.24.',
            '172.25.',
            '172.26.',
            '172.27.',
            '172.28.',
            '172.29.',
            '172.30.',
            '172.31.'
        ]

        domain_lower = domain.lower()

        # Verificar patrones locales
        for pattern in local_patterns:
            if pattern in domain_lower:
                return True

        # Verificar si es una IP
        import re
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ip_pattern, domain):
            return True

        return False
    
    def check_certbot_installation(self) -> bool:
        """Verifica que certbot esté instalado"""
        try:
            result = subprocess.run(['certbot', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.logger.info(f"✅ Certbot instalado: {version}")
                return True
            else:
                self.logger.error("❌ Certbot no responde correctamente")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"❌ Certbot no encontrado: {e}")
            return False
    
    def check_dns_plugin(self, dns_provider: str) -> bool:
        """Verifica que el plugin DNS esté instalado"""
        provider_config = LETSENCRYPT_CONFIG['dns_providers'].get(dns_provider)
        if not provider_config:
            self.logger.error(f"❌ Proveedor DNS no soportado: {dns_provider}")
            return False
        
        plugin_name = provider_config['plugin']
        
        try:
            # Verificar si el plugin está instalado
            result = subprocess.run(['pip', 'show', plugin_name], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.logger.info(f"✅ Plugin DNS instalado: {plugin_name}")
                return True
            else:
                self.logger.warning(f"⚠️  Plugin DNS no instalado: {plugin_name}")
                self.logger.info(f"💡 Instalar con: pip install {plugin_name}")
                return False
        except Exception as e:
            self.logger.error(f"Error verificando plugin DNS: {e}")
            return False
    
    def get_certbot_command(self, domain: str, email: str, dns_provider: str) -> List[str]:
        """Construye el comando certbot para un dominio"""
        provider_config = LETSENCRYPT_CONFIG['dns_providers'][dns_provider]
        
        cmd = [
            'certbot', 'certonly',
            '--non-interactive',
            '--agree-tos',
            '--email', email,
            '--dns-' + dns_provider.replace('_', '-'),
            '-d', domain
        ]
        
        # Agregar archivo de credenciales si es necesario
        if provider_config.get('credentials_file'):
            cmd.extend(['--dns-' + dns_provider.replace('_', '-') + '-credentials', 
                       provider_config['credentials_file']])
        
        # Usar servidor de staging si es dry-run
        if self.dry_run:
            cmd.extend(['--dry-run'])
            self.logger.info(f"🧪 Modo dry-run activado para {domain}")
        
        return cmd
    
    def request_certificate(self, domain_info: Dict) -> bool:
        """Solicita un certificado para un dominio"""
        domain = domain_info['domain']
        email = domain_info['email']
        dns_provider = domain_info['dns_provider']
        
        self.logger.info(f"🔄 Solicitando certificado para {domain} (DNS: {dns_provider})")
        
        # Verificar plugin DNS
        if not self.check_dns_plugin(dns_provider):
            return False
        
        # Construir comando
        cmd = self.get_certbot_command(domain, email, dns_provider)
        
        try:
            self.logger.debug(f"Ejecutando: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f"✅ Certificado obtenido exitosamente para {domain}")
                if not self.dry_run:
                    self.changes_made = True
                return True
            else:
                self.logger.error(f"❌ Error obteniendo certificado para {domain}")
                self.logger.error(f"STDOUT: {result.stdout}")
                self.logger.error(f"STDERR: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"⏰ Timeout obteniendo certificado para {domain}")
            return False
        except Exception as e:
            self.logger.error(f"💥 Error ejecutando certbot para {domain}: {e}")
            return False
    
    def copy_certificates_to_project(self, domain: str) -> bool:
        """Copia certificados de Let's Encrypt al directorio del proyecto"""
        if self.dry_run:
            self.logger.info(f"🧪 [DRY-RUN] Copiando certificados para {domain}")
            return True
        
        try:
            # Rutas de Let's Encrypt
            le_cert_dir = Path(f"/etc/letsencrypt/live/{domain}")
            
            if not le_cert_dir.exists():
                self.logger.error(f"❌ Directorio de certificados LE no encontrado: {le_cert_dir}")
                return False
            
            # Rutas de destino en el proyecto (compatibles con SSLManager)
            ssl_private_dir = SSL_CERTS_DIR.parent / "private"
            ssl_private_dir.mkdir(parents=True, exist_ok=True)
            project_cert_file = SSL_CERTS_DIR / f"{domain}-cert.pem"
            project_key_file = ssl_private_dir / f"{domain}-key.pem"
            
            # Copiar certificado
            le_cert_file = le_cert_dir / "fullchain.pem"
            le_key_file = le_cert_dir / "privkey.pem"
            
            if le_cert_file.exists() and le_key_file.exists():
                import shutil
                shutil.copy2(le_cert_file, project_cert_file)
                shutil.copy2(le_key_file, project_key_file)
                
                # Ajustar permisos
                os.chmod(project_cert_file, 0o644)
                os.chmod(project_key_file, 0o600)
                
                self.logger.info(f"📋 Certificados copiados para {domain}")
                return True
            else:
                self.logger.error(f"❌ Archivos de certificado LE no encontrados para {domain}")
                return False
                
        except Exception as e:
            self.logger.error(f"💥 Error copiando certificados para {domain}: {e}")
            return False
    
    def process_domain_renewals(self) -> int:
        """Procesa renovaciones de dominios que lo necesiten"""
        ssl_domains = self.get_ssl_domains()
        if not ssl_domains:
            self.logger.info("ℹ️  No hay dominios SSL configurados")
            return 0
        
        # Verificar certificados existentes
        domain_names = [d['domain'] for d in ssl_domains]
        cert_results = self.cert_checker.check_multiple_domains(domain_names)
        summary = self.cert_checker.get_renewal_summary(cert_results)
        
        self.logger.info(f"📊 Resumen: {summary['domains_needing_renewal']} de {summary['total_domains']} dominios necesitan renovación")
        
        if not summary['domains_to_renew']:
            self.logger.info("✅ Todos los certificados están actualizados")
            return 0
        
        # Verificar certbot
        if not self.check_certbot_installation():
            self.logger.error("❌ Certbot no está disponible")
            return 0
        
        # Procesar renovaciones
        renewed_count = 0
        for domain_info in ssl_domains:
            domain = domain_info['domain']
            
            if domain in summary['domains_to_renew']:
                self.logger.info(f"🔄 Procesando renovación para {domain}")
                
                if self.request_certificate(domain_info):
                    if self.copy_certificates_to_project(domain):
                        renewed_count += 1
                    else:
                        self.logger.warning(f"⚠️  Certificado obtenido pero no copiado para {domain}")
                else:
                    self.logger.error(f"❌ Falló renovación para {domain}")
        
        return renewed_count

    def restart_web_server(self) -> bool:
        """Reinicia el servidor web si hubo cambios"""
        if self.dry_run:
            self.logger.info("🧪 [DRY-RUN] Reiniciando servidor web")
            return True

        if not self.changes_made:
            self.logger.info("ℹ️  No hay cambios, no se reinicia el servidor")
            return True

        self.logger.info("🔄 Reiniciando servidor web...")

        try:
            # Intentar con systemctl primero
            restart_cmd = WEB_SERVER_CONFIG['restart_command']
            result = subprocess.run(
                restart_cmd,
                capture_output=True,
                text=True,
                timeout=WEB_SERVER_CONFIG['restart_timeout']
            )

            if result.returncode == 0:
                self.logger.info("✅ Servidor web reiniciado exitosamente")
                return True
            else:
                self.logger.warning(f"⚠️  Comando systemctl falló: {result.stderr}")

                # Intentar método alternativo (kill + start)
                self.logger.info("🔄 Intentando método alternativo...")

                # Matar proceso existente
                subprocess.run(
                    WEB_SERVER_CONFIG['kill_command'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                # Esperar un momento
                import time
                time.sleep(2)

                # Iniciar de nuevo
                start_result = subprocess.run(
                    WEB_SERVER_CONFIG['start_command'],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=str(Path(__file__).parent.parent)  # Directorio del proyecto
                )

                if start_result.returncode == 0:
                    self.logger.info("✅ Servidor web reiniciado con método alternativo")
                    return True
                else:
                    self.logger.error(f"❌ Error reiniciando servidor: {start_result.stderr}")
                    return False

        except subprocess.TimeoutExpired:
            self.logger.error("⏰ Timeout reiniciando servidor web")
            return False
        except Exception as e:
            self.logger.error(f"💥 Error reiniciando servidor web: {e}")
            return False

    def run(self) -> Dict:
        """Ejecuta el proceso completo de renovación"""
        start_time = datetime.now()
        self.logger.info(f"🚀 Iniciando gestor Let's Encrypt - {start_time}")

        if self.dry_run:
            self.logger.info("🧪 MODO DRY-RUN ACTIVADO - No se harán cambios reales")

        try:
            # Procesar renovaciones
            renewed_count = self.process_domain_renewals()

            # Reiniciar servidor si hubo cambios
            restart_success = True
            if self.changes_made or renewed_count > 0:
                restart_success = self.restart_web_server()

            # Resumen final
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                'success': True,
                'renewed_count': renewed_count,
                'changes_made': self.changes_made,
                'restart_success': restart_success,
                'duration_seconds': duration,
                'start_time': start_time,
                'end_time': end_time
            }

            self.logger.info(f"✅ Proceso completado en {duration:.1f}s")
            self.logger.info(f"📊 Certificados renovados: {renewed_count}")

            return result

        except Exception as e:
            self.logger.error(f"💥 Error en proceso principal: {e}")
            return {
                'success': False,
                'error': str(e),
                'renewed_count': 0,
                'changes_made': False,
                'restart_success': False
            }

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Gestor de certificados Let\'s Encrypt')
    parser.add_argument('--dry-run', action='store_true',
                       help='Modo prueba - no hace cambios reales')
    parser.add_argument('--dns-provider', default='cloudflare',
                       choices=['cloudflare', 'route53', 'digitalocean', 'namecheap'],
                       help='Proveedor DNS para verificación')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Logging detallado')

    args = parser.parse_args()

    # Ajustar nivel de logging si es verbose
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        manager = LetsEncryptManager(
            dry_run=args.dry_run,
            dns_provider=args.dns_provider
        )

        result = manager.run()

        # Código de salida
        exit_code = 0 if result['success'] else 1
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n⚠️  Proceso interrumpido por usuario")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Error fatal: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

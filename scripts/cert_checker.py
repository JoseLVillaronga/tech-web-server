#!/usr/bin/env python3
"""
Verificador de certificados SSL
Verifica fechas de expiración y estado de certificados
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Importar cryptography para manejo de certificados
try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("❌ Error: Instalar cryptography: pip install cryptography")
    sys.exit(1)

# Importar configuración
sys.path.insert(0, str(Path(__file__).parent))
from letsencrypt_config import LETSENCRYPT_CONFIG, SSL_CERTS_DIR

class CertificateChecker:
    """Verificador de certificados SSL"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.renewal_days = LETSENCRYPT_CONFIG['renewal_days']
    
    def _setup_logger(self) -> logging.Logger:
        """Configura logger básico"""
        logger = logging.getLogger('cert_checker')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def load_certificate(self, cert_path: Path) -> Optional[x509.Certificate]:
        """Carga un certificado desde archivo"""
        try:
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
            
            # Intentar cargar como PEM
            try:
                cert = x509.load_pem_x509_certificate(cert_data, default_backend())
                return cert
            except ValueError:
                # Intentar cargar como DER
                cert = x509.load_der_x509_certificate(cert_data, default_backend())
                return cert
                
        except Exception as e:
            self.logger.error(f"Error cargando certificado {cert_path}: {e}")
            return None
    
    def get_certificate_info(self, cert: x509.Certificate) -> Dict:
        """Extrae información del certificado"""
        try:
            # Obtener fechas
            not_before = cert.not_valid_before
            not_after = cert.not_valid_after
            
            # Obtener subject y SAN
            subject = cert.subject.rfc4514_string()
            
            # Obtener Subject Alternative Names
            san_domains = []
            try:
                san_ext = cert.extensions.get_extension_for_oid(x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                san_domains = [name.value for name in san_ext.value]
            except x509.ExtensionNotFound:
                pass
            
            # Calcular días hasta expiración
            days_until_expiry = (not_after - datetime.now()).days
            
            return {
                'subject': subject,
                'san_domains': san_domains,
                'not_before': not_before,
                'not_after': not_after,
                'days_until_expiry': days_until_expiry,
                'is_expired': datetime.now() > not_after,
                'needs_renewal': days_until_expiry <= self.renewal_days
            }
            
        except Exception as e:
            self.logger.error(f"Error extrayendo información del certificado: {e}")
            return {}
    
    def check_certificate_file(self, cert_path: Path) -> Optional[Dict]:
        """Verifica un archivo de certificado específico"""
        if not cert_path.exists():
            return None
        
        cert = self.load_certificate(cert_path)
        if not cert:
            return None
        
        info = self.get_certificate_info(cert)
        info['cert_path'] = str(cert_path)
        
        return info
    
    def find_certificate_for_domain(self, domain: str) -> Optional[Path]:
        """Busca el certificado para un dominio específico"""
        # Buscar en directorio SSL del proyecto
        project_cert_paths = [
            SSL_CERTS_DIR / f"{domain}.crt",
            SSL_CERTS_DIR / f"{domain}.pem",
            SSL_CERTS_DIR / f"{domain}-cert.pem"
        ]
        
        # Buscar en Let's Encrypt estándar
        letsencrypt_paths = [
            Path(f"/etc/letsencrypt/live/{domain}/cert.pem"),
            Path(f"/etc/letsencrypt/live/{domain}/fullchain.pem")
        ]
        
        all_paths = project_cert_paths + letsencrypt_paths
        
        for cert_path in all_paths:
            if cert_path.exists():
                self.logger.debug(f"Certificado encontrado para {domain}: {cert_path}")
                return cert_path
        
        self.logger.warning(f"No se encontró certificado para dominio: {domain}")
        return None
    
    def check_domain_certificate(self, domain: str) -> Dict:
        """Verifica el certificado de un dominio específico"""
        result = {
            'domain': domain,
            'has_certificate': False,
            'certificate_info': None,
            'needs_renewal': True,  # Por defecto necesita renovación si no hay cert
            'error': None
        }
        
        try:
            cert_path = self.find_certificate_for_domain(domain)
            if not cert_path:
                result['error'] = 'Certificado no encontrado'
                return result
            
            cert_info = self.check_certificate_file(cert_path)
            if not cert_info:
                result['error'] = 'Error leyendo certificado'
                return result
            
            result['has_certificate'] = True
            result['certificate_info'] = cert_info
            result['needs_renewal'] = cert_info.get('needs_renewal', True)
            
            # Log del estado
            if cert_info.get('is_expired'):
                self.logger.warning(f"🔴 Certificado EXPIRADO para {domain}")
            elif cert_info.get('needs_renewal'):
                days = cert_info.get('days_until_expiry', 0)
                self.logger.info(f"🟡 Certificado para {domain} expira en {days} días - RENOVAR")
            else:
                days = cert_info.get('days_until_expiry', 0)
                self.logger.info(f"🟢 Certificado para {domain} válido ({days} días restantes)")
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Error verificando certificado para {domain}: {e}")
        
        return result
    
    def check_multiple_domains(self, domains: List[str]) -> Dict[str, Dict]:
        """Verifica certificados para múltiples dominios"""
        results = {}
        
        self.logger.info(f"🔍 Verificando certificados para {len(domains)} dominios...")
        
        for domain in domains:
            results[domain] = self.check_domain_certificate(domain)
        
        return results
    
    def get_renewal_summary(self, results: Dict[str, Dict]) -> Dict:
        """Genera resumen de renovaciones necesarias"""
        summary = {
            'total_domains': len(results),
            'domains_with_certs': 0,
            'domains_needing_renewal': 0,
            'expired_domains': 0,
            'domains_to_renew': []
        }
        
        for domain, result in results.items():
            if result['has_certificate']:
                summary['domains_with_certs'] += 1
                
                cert_info = result.get('certificate_info', {})
                if cert_info.get('is_expired'):
                    summary['expired_domains'] += 1
                
                if result.get('needs_renewal'):
                    summary['domains_needing_renewal'] += 1
                    summary['domains_to_renew'].append(domain)
        
        return summary

if __name__ == '__main__':
    # Prueba del verificador
    checker = CertificateChecker()
    
    # Dominios de prueba
    test_domains = ['localhost', 'test.local', 'tech-support.local', 'intranet.local']
    
    results = checker.check_multiple_domains(test_domains)
    summary = checker.get_renewal_summary(results)
    
    print("\n📊 Resumen de certificados:")
    print(f"  Total dominios: {summary['total_domains']}")
    print(f"  Con certificados: {summary['domains_with_certs']}")
    print(f"  Necesitan renovación: {summary['domains_needing_renewal']}")
    print(f"  Expirados: {summary['expired_domains']}")
    
    if summary['domains_to_renew']:
        print(f"\n🔄 Dominios a renovar: {', '.join(summary['domains_to_renew'])}")

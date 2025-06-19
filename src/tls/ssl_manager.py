"""
🔐 SSL Manager para Tech Web Server

Este módulo maneja la configuración SSL/TLS para el servidor web,
incluyendo la carga de certificados y configuración de contextos SSL.
"""

import ssl
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class SSLManager:
    """Gestor de certificados SSL y configuración TLS"""
    
    def __init__(self, ssl_base_path: str = "ssl"):
        """
        Inicializar el gestor SSL
        
        Args:
            ssl_base_path: Ruta base donde están los certificados SSL
        """
        self.ssl_base_path = Path(ssl_base_path)
        self.certs_path = self.ssl_base_path / "certs"
        self.private_path = self.ssl_base_path / "private"
        self.ssl_contexts: Dict[str, ssl.SSLContext] = {}
        
        # Verificar que existan los directorios SSL
        if not self.ssl_base_path.exists():
            logger.warning(f"Directorio SSL no encontrado: {self.ssl_base_path}")
        
        if not self.certs_path.exists():
            logger.warning(f"Directorio de certificados no encontrado: {self.certs_path}")
            
        if not self.private_path.exists():
            logger.warning(f"Directorio de claves privadas no encontrado: {self.private_path}")
    
    def load_certificate(self, domain: str) -> Optional[Tuple[str, str]]:
        """
        Cargar certificado y clave privada para un dominio
        
        Args:
            domain: Nombre del dominio
            
        Returns:
            Tupla (cert_file, key_file) o None si no se encuentra
        """
        cert_file = self.certs_path / f"{domain}-cert.pem"
        key_file = self.private_path / f"{domain}-key.pem"
        
        if cert_file.exists() and key_file.exists():
            logger.info(f"✅ Certificado encontrado para {domain}")
            return str(cert_file), str(key_file)
        
        # Intentar con certificado wildcard
        wildcard_cert = self.certs_path / "wildcard-local-cert.pem"
        wildcard_key = self.private_path / "wildcard-local-key.pem"
        
        if domain.endswith('.local') and wildcard_cert.exists() and wildcard_key.exists():
            logger.info(f"✅ Usando certificado wildcard para {domain}")
            return str(wildcard_cert), str(wildcard_key)
        
        logger.warning(f"⚠️ No se encontró certificado para {domain}")
        return None
    
    def create_ssl_context(self, domain: str) -> Optional[ssl.SSLContext]:
        """
        Crear contexto SSL para un dominio específico
        
        Args:
            domain: Nombre del dominio
            
        Returns:
            Contexto SSL configurado o None si falla
        """
        if domain in self.ssl_contexts:
            return self.ssl_contexts[domain]
        
        cert_info = self.load_certificate(domain)
        if not cert_info:
            return None
        
        cert_file, key_file = cert_info
        
        try:
            # Crear contexto SSL con configuración segura
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            
            # Configurar protocolos seguros
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.maximum_version = ssl.TLSVersion.TLSv1_3
            
            # Cargar certificado y clave privada
            context.load_cert_chain(cert_file, key_file)
            
            # Configuraciones de seguridad adicionales
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3
            context.options |= ssl.OP_NO_TLSv1
            context.options |= ssl.OP_NO_TLSv1_1
            context.options |= ssl.OP_SINGLE_DH_USE
            context.options |= ssl.OP_SINGLE_ECDH_USE
            
            # Cache del contexto
            self.ssl_contexts[domain] = context
            
            logger.info(f"🔐 Contexto SSL creado para {domain}")
            return context
            
        except Exception as e:
            logger.error(f"❌ Error creando contexto SSL para {domain}: {e}")
            return None
    
    def get_ssl_context(self, domain: str) -> Optional[ssl.SSLContext]:
        """
        Obtener contexto SSL para un dominio (con cache)
        
        Args:
            domain: Nombre del dominio
            
        Returns:
            Contexto SSL o None si no está disponible
        """
        return self.create_ssl_context(domain)
    
    def is_ssl_available(self, domain: str) -> bool:
        """
        Verificar si SSL está disponible para un dominio
        
        Args:
            domain: Nombre del dominio
            
        Returns:
            True si SSL está disponible
        """
        return self.load_certificate(domain) is not None
    
    def list_available_certificates(self) -> Dict[str, Dict[str, str]]:
        """
        Listar todos los certificados disponibles
        
        Returns:
            Diccionario con información de certificados
        """
        certificates = {}
        
        if not self.certs_path.exists():
            return certificates
        
        for cert_file in self.certs_path.glob("*-cert.pem"):
            domain = cert_file.stem.replace("-cert", "")
            key_file = self.private_path / f"{domain}-key.pem"
            
            if key_file.exists():
                certificates[domain] = {
                    "cert_file": str(cert_file),
                    "key_file": str(key_file),
                    "available": True
                }
            else:
                certificates[domain] = {
                    "cert_file": str(cert_file),
                    "key_file": "NOT_FOUND",
                    "available": False
                }
        
        return certificates
    
    def validate_certificate(self, domain: str) -> Dict[str, any]:
        """
        Validar un certificado específico
        
        Args:
            domain: Nombre del dominio
            
        Returns:
            Información de validación del certificado
        """
        cert_info = self.load_certificate(domain)
        if not cert_info:
            return {"valid": False, "error": "Certificate not found"}
        
        cert_file, key_file = cert_info
        
        try:
            # Verificar que los archivos existen y son legibles
            with open(cert_file, 'r') as f:
                cert_content = f.read()
            
            with open(key_file, 'r') as f:
                key_content = f.read()
            
            # Intentar crear contexto SSL para validar
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(cert_file, key_file)
            
            return {
                "valid": True,
                "cert_file": cert_file,
                "key_file": key_file,
                "cert_size": len(cert_content),
                "key_size": len(key_content)
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "cert_file": cert_file,
                "key_file": key_file
            }
    
    def get_certificate_info(self, domain: str) -> Optional[Dict[str, str]]:
        """
        Obtener información detallada de un certificado
        
        Args:
            domain: Nombre del dominio
            
        Returns:
            Información del certificado o None
        """
        cert_info = self.load_certificate(domain)
        if not cert_info:
            return None
        
        cert_file, _ = cert_info
        
        try:
            import subprocess
            
            # Usar openssl para obtener información del certificado
            result = subprocess.run([
                'openssl', 'x509', '-in', cert_file, '-noout', '-text'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    "domain": domain,
                    "cert_file": cert_file,
                    "info": result.stdout
                }
            else:
                return {
                    "domain": domain,
                    "cert_file": cert_file,
                    "error": result.stderr
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo info del certificado {domain}: {e}")
            return None
    
    def cleanup_ssl_contexts(self):
        """Limpiar contextos SSL cacheados"""
        self.ssl_contexts.clear()
        logger.info("🧹 Contextos SSL limpiados")


# Instancia global del gestor SSL
ssl_manager = SSLManager()

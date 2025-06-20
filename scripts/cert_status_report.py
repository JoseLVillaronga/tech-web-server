#!/usr/bin/env python3
"""
Generador de reportes de estado de certificados
Crea reportes detallados del estado de todos los certificados
"""

import sys
import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import argparse

# Importar módulos locales
sys.path.insert(0, str(Path(__file__).parent))
from letsencrypt_config import VIRTUAL_HOSTS_CONFIG, LOGS_DIR
from cert_checker import CertificateChecker

class CertificateStatusReport:
    """Generador de reportes de estado de certificados"""
    
    def __init__(self):
        self.cert_checker = CertificateChecker()
        self.report_time = datetime.now()
    
    def load_virtual_hosts(self) -> List[Dict]:
        """Carga configuración de virtual hosts"""
        try:
            with open(VIRTUAL_HOSTS_CONFIG, 'r') as f:
                config = yaml.safe_load(f)
            return config.get('virtual_hosts', [])
        except Exception as e:
            print(f"Error cargando virtual hosts: {e}")
            return []
    
    def get_ssl_domains(self) -> List[str]:
        """Obtiene lista de dominios con SSL habilitado (excluyendo locales)"""
        virtual_hosts = self.load_virtual_hosts()
        ssl_domains = []

        for vhost in virtual_hosts:
            if vhost.get('ssl_enabled', False):
                domain = vhost['domain']

                # Filtrar dominios locales
                if not self._is_local_domain(domain):
                    ssl_domains.append(domain)

        return ssl_domains

    def _is_local_domain(self, domain: str) -> bool:
        """Verifica si un dominio es local"""
        local_patterns = ['.local', 'localhost', '127.', '192.168.', '10.']
        domain_lower = domain.lower()

        for pattern in local_patterns:
            if pattern in domain_lower:
                return True

        # Verificar si es una IP
        import re
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ip_pattern, domain):
            return True

        return False
    
    def generate_text_report(self, results: Dict[str, Dict], summary: Dict) -> str:
        """Genera reporte en formato texto"""
        report = []
        report.append("=" * 60)
        report.append("📊 REPORTE DE ESTADO DE CERTIFICADOS SSL")
        report.append("=" * 60)
        report.append(f"📅 Fecha: {self.report_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Resumen
        report.append("📋 RESUMEN:")
        report.append(f"  • Total dominios: {summary['total_domains']}")
        report.append(f"  • Con certificados: {summary['domains_with_certs']}")
        report.append(f"  • Necesitan renovación: {summary['domains_needing_renewal']}")
        report.append(f"  • Expirados: {summary['expired_domains']}")
        report.append("")
        
        # Estado por dominio
        report.append("🔐 ESTADO POR DOMINIO:")
        report.append("-" * 40)
        
        for domain, result in results.items():
            if result['has_certificate']:
                cert_info = result['certificate_info']
                days_left = cert_info.get('days_until_expiry', 0)
                expiry_date = cert_info.get('not_after', 'Desconocida')
                
                if cert_info.get('is_expired'):
                    status = "🔴 EXPIRADO"
                elif cert_info.get('needs_renewal'):
                    status = f"🟡 RENOVAR ({days_left} días)"
                else:
                    status = f"🟢 VÁLIDO ({days_left} días)"
                
                report.append(f"  {domain}:")
                report.append(f"    Estado: {status}")
                report.append(f"    Expira: {expiry_date}")
                
                # SAN domains si existen
                san_domains = cert_info.get('san_domains', [])
                if san_domains and len(san_domains) > 1:
                    report.append(f"    SAN: {', '.join(san_domains[:3])}{'...' if len(san_domains) > 3 else ''}")
                
            else:
                report.append(f"  {domain}:")
                report.append(f"    Estado: ❌ SIN CERTIFICADO")
                if result.get('error'):
                    report.append(f"    Error: {result['error']}")
            
            report.append("")
        
        # Acciones recomendadas
        if summary['domains_to_renew']:
            report.append("🔄 ACCIONES RECOMENDADAS:")
            report.append("-" * 30)
            for domain in summary['domains_to_renew']:
                report.append(f"  • Renovar certificado para: {domain}")
            report.append("")
        
        # Próximas expiraciones (30 días)
        upcoming_expirations = []
        for domain, result in results.items():
            if result['has_certificate']:
                cert_info = result['certificate_info']
                days_left = cert_info.get('days_until_expiry', 999)
                if 0 < days_left <= 30 and not cert_info.get('is_expired'):
                    upcoming_expirations.append((domain, days_left, cert_info.get('not_after')))
        
        if upcoming_expirations:
            report.append("⏰ PRÓXIMAS EXPIRACIONES (30 días):")
            report.append("-" * 35)
            upcoming_expirations.sort(key=lambda x: x[1])  # Ordenar por días restantes
            for domain, days, expiry_date in upcoming_expirations:
                report.append(f"  • {domain}: {days} días ({expiry_date})")
            report.append("")
        
        report.append("=" * 60)
        report.append("🤖 Generado por Let's Encrypt Manager")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def generate_json_report(self, results: Dict[str, Dict], summary: Dict) -> str:
        """Genera reporte en formato JSON"""
        report_data = {
            'timestamp': self.report_time.isoformat(),
            'summary': summary,
            'domains': results,
            'metadata': {
                'generator': 'Let\'s Encrypt Manager',
                'version': '1.0',
                'report_type': 'certificate_status'
            }
        }
        
        return json.dumps(report_data, indent=2, default=str)
    
    def save_report(self, content: str, filename: str) -> Path:
        """Guarda reporte en archivo"""
        LOGS_DIR.mkdir(exist_ok=True)
        report_file = LOGS_DIR / filename
        
        with open(report_file, 'w') as f:
            f.write(content)
        
        return report_file
    
    def generate_report(self, format_type: str = 'text', save_to_file: bool = True) -> str:
        """Genera reporte completo"""
        # Obtener dominios SSL
        ssl_domains = self.get_ssl_domains()
        
        if not ssl_domains:
            return "ℹ️  No hay dominios SSL configurados"
        
        # Verificar certificados
        results = self.cert_checker.check_multiple_domains(ssl_domains)
        summary = self.cert_checker.get_renewal_summary(results)
        
        # Generar reporte según formato
        if format_type.lower() == 'json':
            content = self.generate_json_report(results, summary)
            extension = 'json'
        else:
            content = self.generate_text_report(results, summary)
            extension = 'txt'
        
        # Guardar en archivo si se solicita
        if save_to_file:
            timestamp = self.report_time.strftime('%Y%m%d_%H%M%S')
            filename = f"cert_status_report_{timestamp}.{extension}"
            report_file = self.save_report(content, filename)
            print(f"📄 Reporte guardado en: {report_file}")
        
        return content

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Generador de reportes de certificados SSL')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Formato del reporte (text o json)')
    parser.add_argument('--output', '-o', help='Archivo de salida (opcional)')
    parser.add_argument('--no-save', action='store_true',
                       help='No guardar en archivo, solo mostrar en pantalla')
    
    args = parser.parse_args()
    
    try:
        reporter = CertificateStatusReport()
        
        # Generar reporte
        content = reporter.generate_report(
            format_type=args.format,
            save_to_file=not args.no_save
        )
        
        # Guardar en archivo específico si se proporciona
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                f.write(content)
            print(f"📄 Reporte guardado en: {output_path}")
        
        # Mostrar en pantalla si no se guarda o si es formato texto
        if args.no_save or args.format == 'text':
            print(content)
        
    except KeyboardInterrupt:
        print("\n⚠️  Proceso interrumpido por usuario")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Error generando reporte: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

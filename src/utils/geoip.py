import ipaddress
import os
from typing import Optional

try:
    import geoip2.database
    import geoip2.errors
    GEOIP2_AVAILABLE = True
except ImportError:
    GEOIP2_AVAILABLE = False

from config.config_manager import config

class GeoIPManager:
    """Gestor de geolocalización de IPs"""
    
    def __init__(self):
        self.reader = None
        self._init_geoip()
    
    def _init_geoip(self):
        """Inicializa el lector de GeoIP"""
        if not GEOIP2_AVAILABLE:
            print("⚠️  geoip2 no disponible, usando geolocalización básica")
            return
        
        geoip_path = config.get('geoip_database_path', '/var/lib/geoip/GeoLite2-Country.mmdb')
        
        if os.path.exists(geoip_path):
            try:
                self.reader = geoip2.database.Reader(geoip_path)
                print(f"✅ Base de datos GeoIP cargada: {geoip_path}")
            except Exception as e:
                print(f"⚠️  Error cargando GeoIP: {e}")
        else:
            print(f"⚠️  Base de datos GeoIP no encontrada: {geoip_path}")
    
    def get_country_code(self, ip_address: str) -> str:
        """Obtiene el código de país de una IP"""
        try:
            # Verificar si es IP local
            if self._is_local_ip(ip_address):
                return "LOCAL"
            
            # Si tenemos GeoIP2, usarlo
            if self.reader:
                try:
                    response = self.reader.country(ip_address)
                    return response.country.iso_code or "UNKNOWN"
                except geoip2.errors.AddressNotFoundError:
                    return "UNKNOWN"
                except Exception as e:
                    print(f"Error GeoIP: {e}")
                    return "ERROR"
            
            # Fallback: geolocalización básica por rangos conocidos
            return self._basic_geolocation(ip_address)
            
        except Exception as e:
            print(f"Error en geolocalización: {e}")
            return "ERROR"
    
    def _is_local_ip(self, ip_address: str) -> bool:
        """Verifica si una IP es local/privada"""
        try:
            ip = ipaddress.ip_address(ip_address)
            return ip.is_private or ip.is_loopback or ip.is_link_local
        except:
            return False
    
    def _basic_geolocation(self, ip_address: str) -> str:
        """Geolocalización básica por rangos conocidos"""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Algunos rangos conocidos (muy básico)
            ip_int = int(ip)
            
            # Rangos aproximados para algunos países (solo ejemplos)
            if 167772160 <= ip_int <= 184549375:  # 10.0.0.0/8 - Privado
                return "PRIVATE"
            elif 3232235520 <= ip_int <= 3232301055:  # 192.168.0.0/16 - Privado
                return "PRIVATE"
            elif 2886729728 <= ip_int <= 2887778303:  # 172.16.0.0/12 - Privado
                return "PRIVATE"
            else:
                # Para IPs públicas sin base de datos, retornar código genérico
                return "XX"
                
        except:
            return "UNKNOWN"
    
    def get_country_name(self, country_code: str) -> str:
        """Obtiene el nombre del país desde el código"""
        country_names = {
            "LOCAL": "Local",
            "PRIVATE": "Red Privada",
            "AR": "Argentina",
            "US": "Estados Unidos",
            "BR": "Brasil",
            "CL": "Chile",
            "UY": "Uruguay",
            "PY": "Paraguay",
            "BO": "Bolivia",
            "PE": "Perú",
            "CO": "Colombia",
            "VE": "Venezuela",
            "EC": "Ecuador",
            "MX": "México",
            "ES": "España",
            "FR": "Francia",
            "DE": "Alemania",
            "IT": "Italia",
            "GB": "Reino Unido",
            "CN": "China",
            "JP": "Japón",
            "KR": "Corea del Sur",
            "IN": "India",
            "RU": "Rusia",
            "CA": "Canadá",
            "AU": "Australia",
            "UNKNOWN": "Desconocido",
            "ERROR": "Error",
            "XX": "Público"
        }
        
        return country_names.get(country_code, country_code)
    
    def close(self):
        """Cierra el lector de GeoIP"""
        if self.reader:
            self.reader.close()

# Instancia global del gestor GeoIP
geoip_manager = GeoIPManager()

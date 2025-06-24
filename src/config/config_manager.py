import os
import yaml
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional

class ConfigManager:
    """Maneja la configuración del servidor web desde .env y virtual_hosts.yaml"""
    
    def __init__(self, env_file: str = ".env", virtual_hosts_file: Optional[str] = None):
        # Cargar variables de entorno
        load_dotenv(env_file)
        
        # Archivo de virtual hosts
        self.virtual_hosts_file = virtual_hosts_file or os.getenv('VIRTUAL_HOSTS_CONFIG', 'config/virtual_hosts.yaml')
        
        # Configuración cargada
        self._config = self._load_config()
        self._virtual_hosts = self._load_virtual_hosts()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga configuración desde variables de entorno"""
        return {
            # Base de datos
            'mongo_user': os.getenv('MONGO_USER'),
            'mongo_pass': os.getenv('MONGO_PASS'),
            'mongo_host': os.getenv('MONGO_HOST', 'localhost'),
            'mongo_db': os.getenv('MONGO_DB'),
            
            # Servidor
            'dashboard_port': int(os.getenv('PORT', 8000)),
            'max_concurrent_connections': int(os.getenv('MAX_CONCURRENT_CONNECTIONS', 300)),
            'compression_enabled': os.getenv('COMPRESSION_ENABLED', 'true').lower() == 'true',
            'ssl_enabled': os.getenv('SSL_ENABLED', 'true').lower() == 'true',
            'default_http_port': int(os.getenv('DEFAULT_HTTP_PORT', 3080)),
            'default_https_port': int(os.getenv('DEFAULT_HTTPS_PORT', 3453)),
            
            # Logging
            'logs_enabled': os.getenv('LOGS', 'true').lower() == 'true',
            'log_file_path': os.getenv('LOG_FILE_PATH', '/var/log/webserver/access.log'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            
            # GeoIP
            'geoip_database_path': os.getenv('GEOIP_DATABASE_PATH', '/var/lib/geoip/GeoLite2-Country.mmdb'),
            'geoip_auto_update': os.getenv('GEOIP_AUTO_UPDATE', 'true').lower() == 'true',
            'geoip_update_interval_days': int(os.getenv('GEOIP_UPDATE_INTERVAL_DAYS', 7)),
            
            # PHP-FPM
            'php_fpm_default_socket': os.getenv('PHP_FPM_DEFAULT_SOCKET', '/run/php/php8.3-fpm.sock'),
            'php_fpm_timeout': int(os.getenv('PHP_FPM_TIMEOUT', 30)),
            'php_fpm_sockets_71': os.getenv('PHP_FPM_SOCKETS_71'),
            'php_fpm_sockets_74': os.getenv('PHP_FPM_SOCKETS_74'),
            'php_fpm_sockets_82': os.getenv('PHP_FPM_SOCKETS_82'),
            'php_fpm_sockets_83': os.getenv('PHP_FPM_SOCKETS_83'),
            'php_fpm_sockets_84': os.getenv('PHP_FPM_SOCKETS_84'),
            
            # SSL
            'ssl_protocols': os.getenv('SSL_PROTOCOLS', 'TLSv1.2,TLSv1.3').split(','),
            'ssl_ciphers': os.getenv('SSL_CIPHERS', 'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS'),
            
            # Seguridad
            'rate_limit_enabled': os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true',
            'rate_limit_requests_per_minute': int(os.getenv('RATE_LIMIT_REQUESTS_PER_MINUTE', 60)),
            'hide_server_header': os.getenv('HIDE_SERVER_HEADER', 'true').lower() == 'true',
        }
    
    def _load_virtual_hosts(self) -> List[Dict[str, Any]]:
        """Carga configuración de virtual hosts desde YAML"""
        try:
            with open(self.virtual_hosts_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get('virtual_hosts', [])
        except FileNotFoundError:
            print(f"Archivo de virtual hosts no encontrado: {self.virtual_hosts_file}")
            return []
        except yaml.YAMLError as e:
            print(f"Error al cargar virtual hosts: {e}")
            return []
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración"""
        return self._config.get(key, default)
    
    def get_virtual_hosts(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de virtual hosts"""
        return self._virtual_hosts
    
    def get_virtual_host_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Obtiene un virtual host por dominio"""
        for vhost in self._virtual_hosts:
            if vhost.get('domain') == domain:
                return vhost
        return None

    def get_virtual_host_by_domain_and_port(self, domain: str, port: int) -> Optional[Dict[str, Any]]:
        """Obtiene un virtual host por dominio y puerto (para modo multi-puerto)"""
        for vhost in self._virtual_hosts:
            if vhost.get('domain') == domain and vhost.get('port') == port:
                return vhost
        return None

    def get_unique_http_ports(self) -> List[int]:
        """Obtiene lista de puertos HTTP únicos cuando SSL_ENABLED=false"""
        if self.get('ssl_enabled', True):
            # Modo SSL habilitado: usar puerto por defecto
            return [self.get('default_http_port', 3080)]

        # Modo multi-puerto: obtener puertos únicos de virtual hosts
        ports = set()
        for vhost in self._virtual_hosts:
            port = vhost.get('port', self.get('default_http_port', 3080))
            ports.add(port)

        return sorted(list(ports))
    
    def reload(self):
        """Recarga la configuración"""
        self._config = self._load_config()
        self._virtual_hosts = self._load_virtual_hosts()
        print("Configuración recargada")

# Instancia global del gestor de configuración
config = ConfigManager()

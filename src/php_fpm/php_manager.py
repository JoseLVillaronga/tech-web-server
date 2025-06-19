import os
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import parse_qs

from .fastcgi_client import FastCGIClient
from config.config_manager import config

class PHPManager:
    """Gestor de PHP-FPM para diferentes versiones"""
    
    def __init__(self):
        self.clients: Dict[str, FastCGIClient] = {}
        self._init_php_clients()
    
    def _init_php_clients(self):
        """Inicializa clientes FastCGI para cada versión de PHP"""
        php_versions = {
            '7.1': config.get('php_fpm_sockets_71'),
            '7.4': config.get('php_fpm_sockets_74'),
            '8.2': config.get('php_fpm_sockets_82'),
            '8.3': config.get('php_fpm_sockets_83'),
            '8.4': config.get('php_fpm_sockets_84'),
        }
        
        timeout = config.get('php_fpm_timeout', 30)
        
        for version, socket_path in php_versions.items():
            if socket_path and os.path.exists(socket_path):
                self.clients[version] = FastCGIClient(socket_path, timeout)
                print(f"✅ PHP {version} disponible: {socket_path}")
            else:
                print(f"⚠️  PHP {version} no disponible: {socket_path}")
    
    def get_client(self, php_version: str) -> Optional[FastCGIClient]:
        """Obtiene el cliente FastCGI para una versión específica de PHP"""
        return self.clients.get(php_version)
    
    def get_available_versions(self) -> list:
        """Obtiene las versiones de PHP disponibles"""
        return list(self.clients.keys())
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """Prueba todas las conexiones PHP-FPM"""
        results = {}
        for version, client in self.clients.items():
            results[version] = await client.test_connection()
        return results
    
    def _parse_headers(self, stdout_data: bytes) -> Tuple[Dict[str, str], bytes]:
        """Separa headers y contenido de la respuesta PHP"""
        if b'\r\n\r\n' in stdout_data:
            headers_part, content = stdout_data.split(b'\r\n\r\n', 1)
        elif b'\n\n' in stdout_data:
            headers_part, content = stdout_data.split(b'\n\n', 1)
        else:
            return {}, stdout_data
        
        headers = {}
        for line in headers_part.decode('utf-8', errors='ignore').split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()
        
        return headers, content
    
    def _build_fcgi_params(self, request, vhost: Dict, script_path: str, 
                          query_string: str = '') -> Dict[str, str]:
        """Construye parámetros FastCGI desde el request HTTP"""
        
        # Headers HTTP como variables CGI
        params = {}
        for header_name, header_value in request.headers.items():
            # Convertir header HTTP a variable CGI
            cgi_name = f"HTTP_{header_name.upper().replace('-', '_')}"
            params[cgi_name] = header_value
        
        # Parámetros básicos
        params.update({
            'SCRIPT_FILENAME': script_path,
            'REQUEST_METHOD': request.method,
            'REQUEST_URI': request.path_qs,
            'QUERY_STRING': query_string,
            'CONTENT_TYPE': request.headers.get('Content-Type', ''),
            'CONTENT_LENGTH': request.headers.get('Content-Length', '0'),
            'SERVER_SOFTWARE': 'TechWebServer/1.0',
            'SERVER_NAME': vhost.get('domain', 'localhost'),
            'SERVER_PORT': str(vhost.get('port', 3080)),
            'REMOTE_ADDR': request.remote or '127.0.0.1',
            'GATEWAY_INTERFACE': 'CGI/1.1',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'REDIRECT_STATUS': '200',
            'DOCUMENT_ROOT': str(Path(vhost['document_root']).resolve()),
        })
        
        return params
    
    async def execute_php_file(self, request, vhost: Dict, file_path: Path) -> Tuple[int, Dict[str, str], bytes]:
        """Ejecuta un archivo PHP y retorna status, headers y contenido"""
        
        php_version = vhost.get('php_version', '8.3')
        client = self.get_client(php_version)
        
        if not client:
            return 500, {'content-type': 'text/plain'}, b'PHP version not available'
        
        if not file_path.exists():
            return 404, {'content-type': 'text/plain'}, b'PHP file not found'
        
        try:
            # Separar query string
            query_string = ''
            if '?' in request.path_qs:
                query_string = request.path_qs.split('?', 1)[1]
            
            # Construir parámetros FastCGI
            fcgi_params = self._build_fcgi_params(request, vhost, str(file_path), query_string)
            
            # Leer datos POST si existen
            post_data = b''
            if request.method in ['POST', 'PUT', 'PATCH']:
                if request.can_read_body:
                    post_data = await request.read()
            
            # Ejecutar PHP
            stdout_data, stderr_data = await client.execute_php(
                str(file_path), 
                fcgi_params, 
                post_data
            )
            
            if stderr_data:
                print(f"PHP stderr: {stderr_data.decode('utf-8', errors='ignore')}")
            
            # Parsear respuesta
            headers, content = self._parse_headers(stdout_data)
            
            # Status code (por defecto 200)
            status = 200
            if 'status' in headers:
                try:
                    status = int(headers['status'].split()[0])
                except:
                    status = 200
            
            # Content-Type por defecto
            if 'content-type' not in headers:
                headers['content-type'] = 'text/html; charset=UTF-8'
            
            return status, headers, content
            
        except Exception as e:
            print(f"Error ejecutando PHP: {e}")
            return 500, {'content-type': 'text/plain'}, f'PHP execution error: {str(e)}'.encode()

# Instancia global del gestor PHP
php_manager = PHPManager()

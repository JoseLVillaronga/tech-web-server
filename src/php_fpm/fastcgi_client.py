import asyncio
import struct
import socket
import os
from typing import Dict, Optional, Tuple

class FastCGIClient:
    """Cliente FastCGI simple para comunicarse con PHP-FPM"""
    
    # Constantes FastCGI
    FCGI_VERSION_1 = 1
    FCGI_BEGIN_REQUEST = 1
    FCGI_ABORT_REQUEST = 2
    FCGI_END_REQUEST = 3
    FCGI_PARAMS = 4
    FCGI_STDIN = 5
    FCGI_STDOUT = 6
    FCGI_STDERR = 7
    FCGI_DATA = 8
    FCGI_GET_VALUES = 9
    FCGI_GET_VALUES_RESULT = 10
    
    FCGI_RESPONDER = 1
    FCGI_AUTHORIZER = 2
    FCGI_FILTER = 3
    
    def __init__(self, socket_path: str, timeout: int = 30):
        self.socket_path = socket_path
        self.timeout = timeout
    
    def _pack_fcgi_record(self, req_type: int, req_id: int, content: bytes) -> bytes:
        """Empaqueta un registro FastCGI"""
        content_length = len(content)
        padding_length = (8 - (content_length % 8)) % 8
        
        header = struct.pack(
            '!BBHHBx',
            self.FCGI_VERSION_1,
            req_type,
            req_id,
            content_length,
            padding_length
        )
        
        return header + content + b'\x00' * padding_length
    
    def _pack_params(self, params: Dict[str, str]) -> bytes:
        """Empaqueta parámetros FastCGI"""
        result = b''
        for key, value in params.items():
            key_bytes = key.encode('utf-8')
            value_bytes = value.encode('utf-8')
            
            key_len = len(key_bytes)
            value_len = len(value_bytes)
            
            # Longitud de la clave
            if key_len < 128:
                result += struct.pack('!B', key_len)
            else:
                result += struct.pack('!I', key_len | 0x80000000)
            
            # Longitud del valor
            if value_len < 128:
                result += struct.pack('!B', value_len)
            else:
                result += struct.pack('!I', value_len | 0x80000000)
            
            result += key_bytes + value_bytes
        
        return result
    
    def _unpack_fcgi_record(self, data: bytes) -> Tuple[int, int, bytes]:
        """Desempaqueta un registro FastCGI"""
        if len(data) < 8:
            return 0, 0, b''
        
        version, req_type, req_id, content_length, padding_length = struct.unpack('!BBHHBx', data[:8])
        
        if len(data) < 8 + content_length + padding_length:
            return 0, 0, b''
        
        content = data[8:8 + content_length]
        return req_type, req_id, content
    
    async def execute_php(self, script_path: str, params: Dict[str, str], 
                         post_data: bytes = b'') -> Tuple[bytes, bytes]:
        """Ejecuta un script PHP a través de FastCGI"""
        
        # Verificar que el socket existe
        if not os.path.exists(self.socket_path):
            raise FileNotFoundError(f"Socket PHP-FPM no encontrado: {self.socket_path}")
        
        # Preparar parámetros FastCGI
        fcgi_params = {
            'SCRIPT_FILENAME': script_path,
            'REQUEST_METHOD': params.get('REQUEST_METHOD', 'GET'),
            'REQUEST_URI': params.get('REQUEST_URI', '/'),
            'QUERY_STRING': params.get('QUERY_STRING', ''),
            'CONTENT_TYPE': params.get('CONTENT_TYPE', ''),
            'CONTENT_LENGTH': str(len(post_data)),
            'SERVER_SOFTWARE': 'TechWebServer/1.0',
            'SERVER_NAME': params.get('SERVER_NAME', 'localhost'),
            'SERVER_PORT': params.get('SERVER_PORT', '3080'),
            'REMOTE_ADDR': params.get('REMOTE_ADDR', '127.0.0.1'),
            'REMOTE_HOST': params.get('REMOTE_HOST', ''),
            'HTTP_HOST': params.get('HTTP_HOST', 'localhost'),
            'HTTP_USER_AGENT': params.get('HTTP_USER_AGENT', ''),
            'HTTP_ACCEPT': params.get('HTTP_ACCEPT', '*/*'),
            'GATEWAY_INTERFACE': 'CGI/1.1',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'REDIRECT_STATUS': '200',
        }
        
        # Agregar parámetros adicionales
        for key, value in params.items():
            if key.startswith('HTTP_') or key not in fcgi_params:
                fcgi_params[key] = value
        
        req_id = 1
        
        try:
            # Conectar al socket Unix
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(self.socket_path),
                timeout=self.timeout
            )
            
            # 1. Enviar BEGIN_REQUEST
            begin_request = struct.pack('!HB5x', self.FCGI_RESPONDER, 0)
            writer.write(self._pack_fcgi_record(self.FCGI_BEGIN_REQUEST, req_id, begin_request))
            
            # 2. Enviar PARAMS
            params_data = self._pack_params(fcgi_params)
            if params_data:
                writer.write(self._pack_fcgi_record(self.FCGI_PARAMS, req_id, params_data))
            
            # Enviar PARAMS vacío para indicar fin de parámetros
            writer.write(self._pack_fcgi_record(self.FCGI_PARAMS, req_id, b''))
            
            # 3. Enviar STDIN (datos POST)
            if post_data:
                writer.write(self._pack_fcgi_record(self.FCGI_STDIN, req_id, post_data))
            
            # Enviar STDIN vacío para indicar fin de datos
            writer.write(self._pack_fcgi_record(self.FCGI_STDIN, req_id, b''))
            
            await writer.drain()
            
            # Leer respuesta
            stdout_data = b''
            stderr_data = b''
            
            while True:
                header = await asyncio.wait_for(reader.read(8), timeout=self.timeout)
                if len(header) < 8:
                    break
                
                version, req_type, response_req_id, content_length, padding_length = struct.unpack('!BBHHBx', header)
                
                if content_length > 0:
                    content = await asyncio.wait_for(reader.read(content_length), timeout=self.timeout)
                else:
                    content = b''
                
                if padding_length > 0:
                    await asyncio.wait_for(reader.read(padding_length), timeout=self.timeout)
                
                if req_type == self.FCGI_STDOUT:
                    if content:
                        stdout_data += content
                elif req_type == self.FCGI_STDERR:
                    if content:
                        stderr_data += content
                elif req_type == self.FCGI_END_REQUEST:
                    break
            
            writer.close()
            await writer.wait_closed()
            
            return stdout_data, stderr_data
            
        except asyncio.TimeoutError:
            raise TimeoutError(f"Timeout al comunicarse con PHP-FPM: {self.socket_path}")
        except Exception as e:
            raise RuntimeError(f"Error al ejecutar PHP: {e}")
    
    async def test_connection(self) -> bool:
        """Prueba la conexión con PHP-FPM"""
        try:
            if not os.path.exists(self.socket_path):
                return False
            
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(self.socket_path),
                timeout=5
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False

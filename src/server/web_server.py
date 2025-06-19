import asyncio
import os
from aiohttp import web, web_request
from aiofiles import open as aio_open
import mimetypes
from pathlib import Path
from typing import Optional

from config.config_manager import config
from php_fpm.php_manager import php_manager

class TechWebServer:
    """Servidor web principal con soporte para virtual hosts"""
    
    def __init__(self):
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        """Configura las rutas del servidor"""
        # Ruta catch-all para manejar todos los requests
        self.app.router.add_route('*', '/{path:.*}', self.handle_request)
    
    async def handle_request(self, request: web_request.Request) -> web.Response:
        """Maneja todas las peticiones HTTP"""
        try:
            # Obtener el host del request
            host = request.headers.get('Host', 'localhost').split(':')[0]
            
            # Buscar virtual host correspondiente
            vhost = config.get_virtual_host_by_domain(host)
            if not vhost:
                # Si no se encuentra, usar el primer virtual host como default
                virtual_hosts = config.get_virtual_hosts()
                if virtual_hosts:
                    vhost = virtual_hosts[0]
                else:
                    return web.Response(text="No virtual hosts configured", status=500)
            
            # Obtener la ruta del archivo
            path = request.path.lstrip('/')
            if not path:
                path = 'index.html'
            
            # Construir ruta completa del archivo
            document_root = Path(vhost['document_root'])
            file_path = document_root / path
            
            # Verificar que el archivo existe y está dentro del document_root
            try:
                file_path = file_path.resolve()
                document_root = document_root.resolve()
                
                if not str(file_path).startswith(str(document_root)):
                    return web.Response(text="Forbidden", status=403)
                
                if not file_path.exists():
                    return web.Response(text="Not Found", status=404)
                
                if file_path.is_dir():
                    # Si es directorio, buscar index.html
                    index_file = file_path / 'index.html'
                    if index_file.exists():
                        file_path = index_file
                    else:
                        return web.Response(text="Directory listing not allowed", status=403)
                
            except (OSError, ValueError):
                return web.Response(text="Bad Request", status=400)
            
            # Verificar si es un archivo PHP
            if file_path.suffix.lower() == '.php' and vhost.get('php_enabled', False):
                try:
                    # Ejecutar PHP a través de FastCGI
                    status, headers, content = await php_manager.execute_php_file(request, vhost, file_path)

                    # Crear respuesta
                    response = web.Response(
                        body=content,
                        status=status
                    )

                    # Agregar headers de PHP
                    for header_name, header_value in headers.items():
                        if header_name.lower() != 'status':
                            response.headers[header_name] = header_value

                    # Agregar headers de seguridad básicos
                    if not config.get('hide_server_header', True):
                        response.headers['Server'] = 'TechWebServer/1.0'

                    return response

                except Exception as e:
                    print(f"Error ejecutando PHP: {e}")
                    return web.Response(text="PHP execution error", status=500)

            else:
                # Servir archivo estático
                # Determinar tipo MIME
                content_type, _ = mimetypes.guess_type(str(file_path))
                if content_type is None:
                    content_type = 'application/octet-stream'

                # Leer y servir el archivo
                try:
                    async with aio_open(file_path, 'rb') as f:
                        content = await f.read()

                    # Crear respuesta
                    response = web.Response(
                        body=content,
                        content_type=content_type
                    )

                    # Agregar headers de seguridad básicos
                    if not config.get('hide_server_header', True):
                        response.headers['Server'] = 'TechWebServer/1.0'

                    return response

                except IOError:
                    return web.Response(text="Internal Server Error", status=500)
            
        except Exception as e:
            print(f"Error handling request: {e}")
            return web.Response(text="Internal Server Error", status=500)
    
    async def start_server(self):
        """Inicia el servidor web"""
        http_port = config.get('default_http_port', 3080)
        
        print(f"🚀 Iniciando Tech Web Server...")
        print(f"📡 Puerto HTTP: {http_port}")
        print(f"📊 Dashboard: http://localhost:{config.get('dashboard_port', 8000)}")

        # Mostrar versiones PHP disponibles
        php_versions = php_manager.get_available_versions()
        if php_versions:
            print(f"🐘 PHP disponible: {', '.join(php_versions)}")
        else:
            print("⚠️  No hay versiones de PHP disponibles")

        print(f"🌐 Virtual hosts configurados:")
        for vhost in config.get_virtual_hosts():
            php_info = f" (PHP {vhost.get('php_version', 'N/A')})" if vhost.get('php_enabled') else " (solo HTML)"
            print(f"   - {vhost['domain']} -> {vhost['document_root']}{php_info}")
        
        # Crear runner
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        # Crear site HTTP
        site = web.TCPSite(
            runner, 
            '0.0.0.0', 
            http_port,
            backlog=config.get('max_concurrent_connections', 300)
        )
        
        await site.start()
        print(f"✅ Servidor iniciado en http://localhost:{http_port}")
        
        return runner

async def main():
    """Función principal para ejecutar el servidor"""
    server = TechWebServer()
    runner = await server.start_server()
    
    try:
        # Mantener el servidor corriendo
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servidor...")
    finally:
        await runner.cleanup()
        print("✅ Servidor detenido")

if __name__ == '__main__':
    asyncio.run(main())

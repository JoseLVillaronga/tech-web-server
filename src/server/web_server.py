import asyncio
import os
import time
import ssl
from aiohttp import web, web_request
from aiofiles import open as aio_open
import mimetypes
from pathlib import Path
from typing import Optional, List, Tuple

from config.config_manager import config
from php_fpm.php_manager import php_manager
from dashboard.dashboard_server import DashboardServer
from utils.geoip import geoip_manager
from database.mongodb_client import mongodb_client
from tls.ssl_manager import ssl_manager

class TechWebServer:
    """Servidor web principal con soporte para virtual hosts"""

    def __init__(self):
        self.app = web.Application()
        self.dashboard = DashboardServer()
        self.setup_routes()
        
    def setup_routes(self):
        """Configura las rutas del servidor"""
        # Ruta catch-all para manejar todos los requests
        self.app.router.add_route('*', '/{path:.*}', self.handle_request)
    
    async def handle_request(self, request: web_request.Request) -> web.Response:
        """Maneja todas las peticiones HTTP"""
        start_time = asyncio.get_event_loop().time()

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

            # Verificar si necesita redirección HTTP → HTTPS
            if self._should_redirect_to_https(request, vhost):
                return self._create_https_redirect(request, vhost)
            
            # Obtener la ruta del archivo
            path = request.path.lstrip('/')
            if not path:
                path = ''  # Dejar vacío para que se resuelva como directorio

            # Verificar rutas bloqueadas antes de construir el path completo
            if path:
                blocked_directories = ['.git', '.svn', '.hg', '.bzr', 'node_modules', '.vscode', '.idea']
                path_parts = path.split('/')
                for part in path_parts:
                    if part.lower() in blocked_directories:
                        return web.Response(text="Forbidden", status=403)

            # Construir ruta completa del archivo
            document_root = Path(vhost['document_root'])

            # Si path está vacío, usar directamente el document_root
            if not path:
                file_path = document_root
            else:
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
                    # Si es directorio, buscar archivos index en orden de prioridad
                    index_files = ['index.html', 'index.php', 'index.htm']
                    index_found = False

                    for index_name in index_files:
                        index_file = file_path / index_name
                        if index_file.exists():
                            file_path = index_file
                            index_found = True
                            break

                    if not index_found:
                        return web.Response(text="Directory listing not allowed", status=403)
                
            except (OSError, ValueError):
                return web.Response(text="Bad Request", status=400)

            # Bloquear acceso a archivos sensibles específicos
            blocked_files = ['.env', '.htaccess', '.htpasswd', 'config.php', 'wp-config.php',
                           '.gitignore', '.gitattributes', '.gitmodules']
            blocked_extensions = ['.bak', '.backup', '.old', '.orig', '.tmp', '.log', '.swp', '.swo']

            # Archivos que empiezan con . que están específicamente bloqueados
            blocked_dot_files = ['.env', '.htaccess', '.htpasswd', '.gitignore', '.gitattributes',
                               '.gitmodules', '.git', '.svn', '.hg', '.bzr']

            # Verificar si el archivo final está bloqueado
            filename = file_path.name.lower()
            if (filename in blocked_files or
                any(filename.endswith(ext) for ext in blocked_extensions) or
                any(filename.startswith(blocked) for blocked in blocked_dot_files)):
                return web.Response(text="Forbidden", status=403)

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

                    # Registrar estadísticas
                    self._log_request(request, status, 'php', start_time, vhost)

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

                    # Registrar estadísticas
                    self._log_request(request, 200, 'static', start_time, vhost)

                    return response

                except IOError:
                    return web.Response(text="Internal Server Error", status=500)
            
        except Exception as e:
            print(f"Error handling request: {e}")
            response = web.Response(text="Internal Server Error", status=500)
            self._log_request(request, 500, 'error', start_time, None)
            return response

    def _should_redirect_to_https(self, request: web_request.Request, vhost: dict) -> bool:
        """Determina si la petición HTTP debe ser redirigida a HTTPS"""
        # Solo redirigir si:
        # 1. El virtual host tiene SSL habilitado
        # 2. El virtual host tiene redirección SSL habilitada
        # 3. La petición actual es HTTP (no HTTPS)
        return (
            vhost.get('ssl_enabled', False) and
            vhost.get('ssl_redirect', False) and
            request.scheme == 'http'
        )

    def _create_https_redirect(self, request: web_request.Request, vhost: dict) -> web.Response:
        """Crea una respuesta de redirección HTTP → HTTPS"""
        # Obtener puerto HTTPS del .env
        https_port = config.get('default_https_port', 3453)

        # Construir URL HTTPS
        host = request.headers.get('Host', vhost['domain']).split(':')[0]

        # Si el puerto HTTPS es estándar (443), no incluirlo en la URL
        if https_port == 443:
            https_url = f"https://{host}{request.path_qs}"
        else:
            https_url = f"https://{host}:{https_port}{request.path_qs}"

        # Crear respuesta de redirección 301 (permanente)
        response = web.Response(
            status=301,
            headers={'Location': https_url}
        )

        # Registrar la redirección en logs
        self._log_request(request, 301, 'ssl_redirect', asyncio.get_event_loop().time(), vhost)

        return response

    def _log_request(self, request: web_request.Request, status_code: int,
                    request_type: str, start_time: float, vhost: dict = None):
        """Registra estadísticas de la request"""
        try:
            ip = request.remote or '127.0.0.1'
            user_agent = request.headers.get('User-Agent', '')
            path = request.path
            response_time = time.time() - start_time

            # Obtener código de país
            country_code = geoip_manager.get_country_code(ip)

            # Obtener dominio del virtual host
            virtual_host_domain = vhost.get('domain', 'unknown') if vhost else 'unknown'

            # Actualizar dashboard en tiempo real
            self.dashboard.update_stats(
                request_type=request_type,
                status_code=status_code,
                path=path,
                user_agent=user_agent,
                ip=ip,
                country_code=country_code,
                virtual_host=virtual_host_domain
            )

            # Logging persistente a MongoDB (si está habilitado)
            if config.get('logs_enabled', True):
                asyncio.create_task(self._log_to_mongodb(
                    request, status_code, request_type, response_time,
                    country_code, virtual_host_domain, user_agent
                ))

        except Exception as e:
            print(f"Error logging request: {e}")

    async def _log_to_mongodb(self, request: web_request.Request, status_code: int,
                             request_type: str, response_time: float, country_code: str,
                             virtual_host: str, user_agent: str):
        """Registra la request en MongoDB de forma asíncrona"""
        try:
            request_data = {
                'ip': request.remote or '127.0.0.1',
                'country_code': country_code,
                'method': request.method,
                'path': request.path,
                'query_string': request.query_string,
                'status_code': status_code,
                'request_type': request_type,
                'virtual_host': virtual_host,
                'user_agent': user_agent,
                'response_time': response_time,
                'content_length': 0,  # Se puede calcular si es necesario
                'referer': request.headers.get('Referer', ''),
                'protocol': f"{request.scheme.upper()}/{request.version.major}.{request.version.minor}"
            }

            await mongodb_client.log_request(request_data)

        except Exception as e:
            print(f"Error logging to MongoDB: {e}")

    async def start_server(self):
        """Inicia el servidor web con soporte HTTP y HTTPS"""
        # Inicializar MongoDB si el logging está habilitado
        if config.get('logs_enabled', True):
            print("🔌 Inicializando conexión a MongoDB...")
            await mongodb_client.connect()

        http_port = config.get('default_http_port', 3080)
        https_port = config.get('default_https_port', 3453)

        print(f"🚀 Iniciando Tech Web Server...")
        print(f"📡 Puerto HTTP: {http_port}")
        print(f"🔐 Puerto HTTPS: {https_port}")
        print(f"📊 Dashboard: http://localhost:{config.get('dashboard_port', 8000)}")

        # Mostrar versiones PHP disponibles
        php_versions = php_manager.get_available_versions()
        if php_versions:
            print(f"🐘 PHP disponible: {', '.join(php_versions)}")
        else:
            print("⚠️  No hay versiones de PHP disponibles")

        # Verificar certificados SSL disponibles
        ssl_certificates = ssl_manager.list_available_certificates()
        if ssl_certificates:
            print(f"🔐 Certificados SSL disponibles:")
            for domain, cert_info in ssl_certificates.items():
                status = "✅" if cert_info['available'] else "❌"
                print(f"   {status} {domain}")
        else:
            print("⚠️  No hay certificados SSL disponibles")

        print(f"🌐 Virtual hosts configurados:")
        for vhost in config.get_virtual_hosts():
            php_info = f" (PHP {vhost.get('php_version', 'N/A')})" if vhost.get('php_enabled') else " (solo HTML)"
            ssl_info = " [SSL]" if vhost.get('ssl_enabled', False) else ""
            print(f"   - {vhost['domain']} -> {vhost['document_root']}{php_info}{ssl_info}")

        # Crear runner
        runner = web.AppRunner(self.app)
        await runner.setup()

        # Lista para almacenar todos los sites
        sites = []

        # Crear site HTTP
        http_site = web.TCPSite(
            runner,
            '0.0.0.0',
            http_port,
            backlog=config.get('max_concurrent_connections', 300)
        )

        await http_site.start()
        sites.append(http_site)
        print(f"✅ Servidor HTTP iniciado en http://localhost:{http_port}")

        # Crear servidor HTTPS - priorizar dominios públicos
        ssl_enabled_hosts = [vhost for vhost in config.get_virtual_hosts() if vhost.get('ssl_enabled', False)]

        if ssl_enabled_hosts:
            # Buscar certificado principal (preferir dominios públicos)
            ssl_context = None
            cert_used = None

            # Prioridad 1: Dominios públicos (no .local, no localhost)
            for vhost in ssl_enabled_hosts:
                domain = vhost['domain']
                if not domain.endswith('.local') and domain != 'localhost':
                    if ssl_manager.is_ssl_available(domain):
                        ssl_context = ssl_manager.get_ssl_context(domain)
                        cert_used = domain
                        break

            # Prioridad 2: Certificado wildcard para .local
            if not ssl_context and ssl_manager.is_ssl_available('wildcard-local'):
                ssl_context = ssl_manager.get_ssl_context('wildcard-local')
                cert_used = 'wildcard-local (*.local)'

            # Prioridad 3: localhost
            if not ssl_context and ssl_manager.is_ssl_available('localhost'):
                ssl_context = ssl_manager.get_ssl_context('localhost')
                cert_used = 'localhost'

            # Prioridad 4: Cualquier certificado disponible
            if not ssl_context:
                for vhost in ssl_enabled_hosts:
                    domain = vhost['domain']
                    if ssl_manager.is_ssl_available(domain):
                        ssl_context = ssl_manager.get_ssl_context(domain)
                        cert_used = domain
                        break

            if ssl_context:
                try:
                    https_site = web.TCPSite(
                        runner,
                        '0.0.0.0',
                        https_port,
                        ssl_context=ssl_context,
                        backlog=config.get('max_concurrent_connections', 300)
                    )

                    await https_site.start()
                    sites.append(https_site)

                    ssl_domains = [vhost['domain'] for vhost in ssl_enabled_hosts]
                    print(f"✅ Servidor HTTPS iniciado en puerto {https_port}")
                    print(f"🔐 Certificado principal: {cert_used}")
                    print(f"🌐 Dominios SSL configurados: {', '.join(ssl_domains)}")

                except Exception as e:
                    print(f"❌ Error iniciando servidor HTTPS: {e}")
            else:
                print("⚠️  No se encontraron certificados SSL válidos")
        else:
            print("ℹ️  No se inició servidor HTTPS (no hay virtual hosts con SSL habilitado)")

        # Iniciar dashboard
        dashboard_port = config.get('dashboard_port', 8000)
        dashboard_bind_ip = config.get('dashboard_bind_ip', '0.0.0.0')

        dashboard_runner = web.AppRunner(self.dashboard.app)
        await dashboard_runner.setup()

        dashboard_site = web.TCPSite(
            dashboard_runner,
            dashboard_bind_ip,
            dashboard_port
        )

        await dashboard_site.start()
        print(f"📊 Dashboard iniciado en http://{dashboard_bind_ip}:{dashboard_port}")

        return runner, dashboard_runner, sites

async def main():
    """Función principal para ejecutar el servidor"""
    server = TechWebServer()
    runner, dashboard_runner, sites = await server.start_server()

    try:
        # Mantener el servidor corriendo
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servidor...")
    finally:
        await runner.cleanup()
        await dashboard_runner.cleanup()

        # Limpiar contextos SSL
        ssl_manager.cleanup_ssl_contexts()

        print("✅ Servidor detenido")

if __name__ == '__main__':
    asyncio.run(main())

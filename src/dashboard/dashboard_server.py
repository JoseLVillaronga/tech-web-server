import asyncio
import json
import time
from datetime import datetime
from aiohttp import web, web_request
from aiohttp.web_ws import WebSocketResponse
import aiofiles
from pathlib import Path
from typing import Dict, List, Any

from config.config_manager import config
from database.mongodb_client import mongodb_client
from php_fpm.php_manager import php_manager

STATIC_DIR = Path(__file__).resolve().parent / 'static'


class DashboardServer:
    """Servidor del dashboard de administración"""
    
    def __init__(self):
        self.app = web.Application()
        self.websockets: List[WebSocketResponse] = []
        self.stats = {
            'requests_total': 0,
            'requests_per_minute': 0,
            'active_connections': 0,
            'php_requests': 0,
            'static_requests': 0,
            'errors': 0,
            'start_time': time.time(),
            'last_requests': []
        }
        self.setup_routes()
    
    def setup_routes(self):
        """Configura las rutas del dashboard"""
        # Rutas estáticas y API
        self.app.router.add_get('/', self.dashboard_home)
        self.app.router.add_get('/api/stats', self.api_stats)
        self.app.router.add_get('/api/virtual-hosts', self.api_virtual_hosts)
        self.app.router.add_get('/api/php-status', self.api_php_status)
        self.app.router.add_get('/api/logs', self.api_logs)
        self.app.router.add_get('/api/logs/historical', self.api_historical_logs)
        self.app.router.add_get('/api/logs/filter-options', self.api_filter_options)
        self.app.router.add_get('/ws', self.websocket_handler)
        
        # Archivos estáticos del dashboard
        self.app.router.add_get('/static/{filename}', self.serve_static)
    
    async def dashboard_home(self, request: web_request.Request) -> web.Response:
        """Página principal del dashboard"""
        html_content = await self._get_dashboard_html()
        return web.Response(text=html_content, content_type='text/html')
    
    async def api_stats(self, request: web_request.Request) -> web.Response:
        """API de estadísticas del servidor"""
        uptime = time.time() - self.stats['start_time']
        
        stats_data = {
            **self.stats,
            'uptime': uptime,
            'uptime_formatted': self._format_uptime(uptime),
            'timestamp': datetime.now().isoformat()
        }
        
        return web.json_response(stats_data)
    
    async def api_virtual_hosts(self, request: web_request.Request) -> web.Response:
        """API de información de virtual hosts sin mutar la configuración global"""
        virtual_hosts = config.get_virtual_hosts()
        
        vhosts_response = []
        for vhost in virtual_hosts:
            vhosts_response.append({
                **vhost,
                'status': 'active',
                'document_root_exists': Path(vhost['document_root']).exists()
            })
        
        return web.json_response({
            'virtual_hosts': vhosts_response,
            'total': len(vhosts_response)
        })
    
    async def api_php_status(self, request: web_request.Request) -> web.Response:
        """API de estado de PHP-FPM"""
        php_versions = php_manager.get_available_versions()
        php_status = await php_manager.test_all_connections()
        
        php_info = []
        for version in php_versions:
            php_info.append({
                'version': version,
                'status': 'online' if php_status.get(version, False) else 'offline',
                'socket': config.get(f'php_fpm_sockets_{version.replace(".", "")}', 'N/A')
            })
        
        return web.json_response({
            'php_versions': php_info,
            'total_versions': len(php_versions)
        })

    async def api_logs(self, request: web_request.Request) -> web.Response:
        """API de logs desde MongoDB"""
        try:
            # Parámetros de consulta
            limit = int(request.query.get('limit', 50))
            virtual_host = request.query.get('virtual_host', None)

            # Obtener logs desde MongoDB
            logs = await mongodb_client.get_recent_logs(limit=limit, virtual_host=virtual_host)

            # Si MongoDB no está disponible, usar logs en memoria
            if not logs and hasattr(self, 'recent_requests'):
                logs = self.recent_requests[-limit:] if self.recent_requests else []

            return web.json_response({
                'logs': logs,
                'total': len(logs),
                'source': 'mongodb' if mongodb_client.connected else 'memory'
            })

        except Exception as e:
            print(f"Error obteniendo logs: {e}")
            return web.json_response({
                'logs': [],
                'total': 0,
                'error': str(e)
            }, status=500)

    async def api_historical_logs(self, request: web_request.Request) -> web.Response:
        """API de logs históricos con filtros avanzados"""
        page = 1
        try:
            # Parámetros de consulta
            page = int(request.query.get('page', 1))
            limit = int(request.query.get('limit', 50))

            # Filtros opcionales
            filters = {}
            if request.query.get('start_date'):
                filters['start_date'] = request.query.get('start_date')
            if request.query.get('end_date'):
                filters['end_date'] = request.query.get('end_date')
            if request.query.get('ip'):
                filters['ip'] = request.query.get('ip')
            if request.query.get('virtual_host'):
                filters['virtual_host'] = request.query.get('virtual_host')
            if request.query.get('status_code'):
                filters['status_code'] = request.query.get('status_code')
            if request.query.get('method'):
                filters['method'] = request.query.get('method')
            if request.query.get('search_text'):
                filters['search_text'] = request.query.get('search_text')

            # Obtener logs históricos desde MongoDB
            result = await mongodb_client.get_historical_logs(
                page=page,
                limit=limit,
                filters=filters if filters else None
            )

            return web.json_response({
                'success': True,
                'data': result,
                'source': 'mongodb'
            })

        except Exception as e:
            print(f"Error obteniendo logs históricos: {e}")
            return web.json_response({
                'success': False,
                'error': str(e),
                'data': {
                    'logs': [],
                    'total_count': 0,
                    'page': page,
                    'total_pages': 0
                }
            }, status=500)

    async def api_filter_options(self, request: web_request.Request) -> web.Response:
        """API para obtener opciones disponibles para filtros"""
        try:
            options = await mongodb_client.get_filter_options()

            return web.json_response({
                'success': True,
                'options': options
            })

        except Exception as e:
            print(f"Error obteniendo opciones de filtro: {e}")
            return web.json_response({
                'success': False,
                'error': str(e),
                'options': {}
            }, status=500)

    async def websocket_handler(self, request: web_request.Request) -> WebSocketResponse:
        """Maneja conexiones WebSocket para actualizaciones en tiempo real"""
        ws = WebSocketResponse()
        await ws.prepare(request)
        
        self.websockets.append(ws)
        
        try:
            async for msg in ws:
                if msg.type == web.MsgType.TEXT:
                    # Echo para mantener conexión viva
                    await ws.send_str(json.dumps({'type': 'pong'}))
                elif msg.type == web.MsgType.ERROR:
                    print(f'WebSocket error: {ws.exception()}')
        except Exception as e:
            print(f'WebSocket error: {e}')
        finally:
            if ws in self.websockets:
                self.websockets.remove(ws)
        
        return ws
    
    async def serve_static(self, request: web_request.Request) -> web.Response:
        """Sirve archivos estáticos del dashboard desde el directorio static/"""
        filename = request.match_info['filename']
        
        if filename == 'dashboard.css':
            css_content = await self._get_dashboard_css()
            return web.Response(text=css_content, content_type='text/css')
        elif filename == 'dashboard.js':
            js_content = await self._get_dashboard_js()
            return web.Response(text=js_content, content_type='application/javascript')
        
        return web.Response(text="Not Found", status=404)
    
    def update_stats(self, request_type: str = 'static', status_code: int = 200,
                    path: str = '/', user_agent: str = '', ip: str = '127.0.0.1',
                    country_code: str = 'XX', virtual_host: str = 'unknown'):
        """Actualiza estadísticas del servidor"""
        self.stats['requests_total'] += 1
        
        if request_type == 'php':
            self.stats['php_requests'] += 1
        else:
            self.stats['static_requests'] += 1
        
        if status_code >= 400:
            self.stats['errors'] += 1
        
        # Agregar a últimas requests (mantener solo las últimas 10)
        request_info = {
            'timestamp': datetime.now().isoformat(),
            'path': path,
            'status': status_code,
            'type': request_type,
            'ip': ip,
            'user_agent': user_agent[:50] + '...' if len(user_agent) > 50 else user_agent,
            'country_code': country_code,
            'virtual_host': virtual_host
        }
        
        self.stats['last_requests'].insert(0, request_info)
        if len(self.stats['last_requests']) > 10:
            self.stats['last_requests'] = self.stats['last_requests'][:10]
        
        # Enviar actualización a WebSockets
        asyncio.create_task(self._broadcast_stats())
    
    async def _broadcast_stats(self):
        """Envía estadísticas a todos los WebSockets conectados"""
        if not self.websockets:
            return
        
        stats_data = await self._get_stats_for_broadcast()
        message = json.dumps({
            'type': 'stats_update',
            'data': stats_data
        })
        
        # Enviar a todos los WebSockets activos
        disconnected = []
        for ws in self.websockets:
            try:
                await ws.send_str(message)
            except Exception:
                disconnected.append(ws)
        
        # Remover WebSockets desconectados
        for ws in disconnected:
            if ws in self.websockets:
                self.websockets.remove(ws)
    
    async def _get_stats_for_broadcast(self) -> Dict[str, Any]:
        """Obtiene estadísticas para broadcast"""
        uptime = time.time() - self.stats['start_time']
        return {
            **self.stats,
            'uptime': uptime,
            'uptime_formatted': self._format_uptime(uptime),
            'timestamp': datetime.now().isoformat()
        }
    
    def _format_uptime(self, uptime_seconds: float) -> str:
        """Formatea el tiempo de actividad"""
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    async def _get_dashboard_css(self) -> str:
        """Carga el CSS del dashboard desde archivo estático"""
        async with aiofiles.open(STATIC_DIR / 'dashboard.css', 'r', encoding='utf-8') as f:
            return await f.read()

    async def _get_dashboard_js(self) -> str:
        """Carga el JavaScript del dashboard desde archivo estático"""
        async with aiofiles.open(STATIC_DIR / 'dashboard.js', 'r', encoding='utf-8') as f:
            return await f.read()

    async def _get_dashboard_html(self) -> str:
        """Carga el HTML del dashboard desde archivo estático"""
        async with aiofiles.open(STATIC_DIR / 'index.html', 'r', encoding='utf-8') as f:
            return await f.read()

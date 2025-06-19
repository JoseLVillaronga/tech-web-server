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
from php_fpm.php_manager import php_manager

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
        # Rutas estáticas
        self.app.router.add_get('/', self.dashboard_home)
        self.app.router.add_get('/api/stats', self.api_stats)
        self.app.router.add_get('/api/virtual-hosts', self.api_virtual_hosts)
        self.app.router.add_get('/api/php-status', self.api_php_status)
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
        """API de información de virtual hosts"""
        virtual_hosts = config.get_virtual_hosts()
        
        # Agregar información adicional a cada virtual host
        for vhost in virtual_hosts:
            vhost['status'] = 'active'  # TODO: verificar estado real
            vhost['document_root_exists'] = Path(vhost['document_root']).exists()
        
        return web.json_response({
            'virtual_hosts': virtual_hosts,
            'total': len(virtual_hosts)
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
        """Sirve archivos estáticos del dashboard"""
        filename = request.match_info['filename']
        
        # Archivos CSS/JS embebidos para simplicidad
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
            except:
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
        """Genera el CSS del dashboard"""
        return '''
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f5f7fa;
    color: #333;
    line-height: 1.6;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    padding: 20px;
    background: white;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

h1 {
    color: #2c3e50;
    font-size: 2rem;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
}

.dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
}

.dot.online {
    background: #27ae60;
    box-shadow: 0 0 10px rgba(39, 174, 96, 0.5);
}

.dot.offline {
    background: #e74c3c;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}

.card {
    background: white;
    padding: 25px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.card h2 {
    margin-bottom: 20px;
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 10px;
}

.full-width {
    grid-column: 1 / -1;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
}

.stat {
    text-align: center;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 8px;
}

.stat-value {
    font-size: 2rem;
    font-weight: bold;
    color: #3498db;
}

.stat-label {
    font-size: 0.9rem;
    color: #7f8c8d;
    margin-top: 5px;
}

.uptime {
    text-align: center;
    padding: 15px;
    background: #e8f5e8;
    border-radius: 8px;
    color: #27ae60;
}

.vhost-item, .php-item {
    padding: 15px;
    margin-bottom: 10px;
    background: #f8f9fa;
    border-radius: 8px;
    border-left: 4px solid #3498db;
}

.vhost-item.error, .php-item.offline {
    border-left-color: #e74c3c;
}

.vhost-domain, .php-version {
    font-weight: bold;
    color: #2c3e50;
}

.vhost-details, .php-details {
    font-size: 0.9rem;
    color: #7f8c8d;
    margin-top: 5px;
}

.requests-table {
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

th {
    background: #f8f9fa;
    font-weight: 600;
    color: #2c3e50;
}

.status-200 { color: #27ae60; }
.status-300 { color: #f39c12; }
.status-400 { color: #e74c3c; }
.status-500 { color: #8e44ad; }

.loading {
    text-align: center;
    color: #7f8c8d;
    padding: 20px;
}

@media (max-width: 768px) {
    .container {
        padding: 10px;
    }

    header {
        flex-direction: column;
        gap: 15px;
        text-align: center;
    }

    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}
'''

    async def _get_dashboard_js(self) -> str:
        """Genera el JavaScript del dashboard"""
        return '''
class Dashboard {
    constructor() {
        this.ws = null;
        this.reconnectInterval = 5000;
        this.init();
    }

    init() {
        this.connectWebSocket();
        this.loadInitialData();

        // Actualizar cada 30 segundos si no hay WebSocket
        setInterval(() => {
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                this.loadStats();
            }
        }, 30000);
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket conectado');
            this.updateStatus(true);
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'stats_update') {
                this.updateStats(data.data);
            }
        };

        this.ws.onclose = () => {
            console.log('WebSocket desconectado');
            this.updateStatus(false);
            setTimeout(() => this.connectWebSocket(), this.reconnectInterval);
        };

        this.ws.onerror = (error) => {
            console.error('Error WebSocket:', error);
        };
    }

    async loadInitialData() {
        await Promise.all([
            this.loadStats(),
            this.loadVirtualHosts(),
            this.loadPhpStatus()
        ]);
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            this.updateStats(data);
        } catch (error) {
            console.error('Error cargando estadísticas:', error);
        }
    }

    async loadVirtualHosts() {
        try {
            const response = await fetch('/api/virtual-hosts');
            const data = await response.json();
            this.updateVirtualHosts(data.virtual_hosts);
        } catch (error) {
            console.error('Error cargando virtual hosts:', error);
        }
    }

    async loadPhpStatus() {
        try {
            const response = await fetch('/api/php-status');
            const data = await response.json();
            this.updatePhpStatus(data.php_versions);
        } catch (error) {
            console.error('Error cargando estado PHP:', error);
        }
    }

    updateStatus(online) {
        const statusEl = document.getElementById('status');
        const dot = statusEl.querySelector('.dot');
        const text = statusEl.querySelector('span:last-child');

        if (online) {
            dot.className = 'dot online';
            text.textContent = 'Online';
        } else {
            dot.className = 'dot offline';
            text.textContent = 'Offline';
        }
    }

    updateStats(stats) {
        document.getElementById('total-requests').textContent = stats.requests_total;
        document.getElementById('php-requests').textContent = stats.php_requests;
        document.getElementById('static-requests').textContent = stats.static_requests;
        document.getElementById('errors').textContent = stats.errors;
        document.getElementById('uptime').textContent = stats.uptime_formatted;

        this.updateRecentRequests(stats.last_requests);
    }

    updateVirtualHosts(vhosts) {
        const container = document.getElementById('virtual-hosts-list');

        if (vhosts.length === 0) {
            container.innerHTML = '<div class="loading">No hay virtual hosts configurados</div>';
            return;
        }

        container.innerHTML = vhosts.map(vhost => `
            <div class="vhost-item ${vhost.document_root_exists ? '' : 'error'}">
                <div class="vhost-domain">${vhost.domain}</div>
                <div class="vhost-details">
                    📁 ${vhost.document_root}<br>
                    🐘 PHP ${vhost.php_version} ${vhost.php_enabled ? '(Habilitado)' : '(Deshabilitado)'}<br>
                    🔒 SSL ${vhost.ssl_enabled ? 'Habilitado' : 'Deshabilitado'}
                </div>
            </div>
        `).join('');
    }

    updatePhpStatus(phpVersions) {
        const container = document.getElementById('php-status-list');

        if (phpVersions.length === 0) {
            container.innerHTML = '<div class="loading">No hay versiones PHP disponibles</div>';
            return;
        }

        container.innerHTML = phpVersions.map(php => `
            <div class="php-item ${php.status === 'online' ? '' : 'offline'}">
                <div class="php-version">PHP ${php.version}</div>
                <div class="php-details">
                    Estado: ${php.status === 'online' ? '🟢 Online' : '🔴 Offline'}<br>
                    Socket: ${php.socket}
                </div>
            </div>
        `).join('');
    }

    updateRecentRequests(requests) {
        const tbody = document.querySelector('#recent-requests tbody');

        if (!requests || requests.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="loading">No hay requests recientes</td></tr>';
            return;
        }

        tbody.innerHTML = requests.map(req => {
            const time = new Date(req.timestamp).toLocaleTimeString();
            const statusClass = `status-${Math.floor(req.status / 100) * 100}`;

            return `
                <tr>
                    <td>${time}</td>
                    <td>${req.path}</td>
                    <td class="${statusClass}">${req.status}</td>
                    <td>${req.type}</td>
                    <td>${req.ip}</td>
                    <td>${req.country_code || 'XX'}</td>
                    <td>${req.virtual_host || 'unknown'}</td>
                    <td>${req.user_agent}</td>
                </tr>
            `;
        }).join('');
    }
}

// Inicializar dashboard cuando se carga la página
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});
'''

    async def _get_dashboard_html(self) -> str:
        """Genera el HTML del dashboard"""
        return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tech Web Server - Dashboard</title>
    <link rel="stylesheet" href="/static/dashboard.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 Tech Web Server Dashboard</h1>
            <div class="status-indicator" id="status">
                <span class="dot online"></span>
                <span>Online</span>
            </div>
        </header>
        
        <div class="grid">
            <!-- Estadísticas principales -->
            <div class="card">
                <h2>📊 Estadísticas</h2>
                <div class="stats-grid">
                    <div class="stat">
                        <div class="stat-value" id="total-requests">0</div>
                        <div class="stat-label">Total Requests</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="php-requests">0</div>
                        <div class="stat-label">PHP Requests</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="static-requests">0</div>
                        <div class="stat-label">Static Requests</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="errors">0</div>
                        <div class="stat-label">Errors</div>
                    </div>
                </div>
                <div class="uptime">
                    <strong>Uptime:</strong> <span id="uptime">00:00:00</span>
                </div>
            </div>
            
            <!-- Virtual Hosts -->
            <div class="card">
                <h2>🌐 Virtual Hosts</h2>
                <div id="virtual-hosts-list">
                    <div class="loading">Cargando...</div>
                </div>
            </div>
            
            <!-- Estado PHP -->
            <div class="card">
                <h2>🐘 Estado PHP-FPM</h2>
                <div id="php-status-list">
                    <div class="loading">Cargando...</div>
                </div>
            </div>
            
            <!-- Últimas requests -->
            <div class="card full-width">
                <h2>📝 Últimas Requests</h2>
                <div class="requests-table">
                    <table id="recent-requests">
                        <thead>
                            <tr>
                                <th>Tiempo</th>
                                <th>Path</th>
                                <th>Status</th>
                                <th>Tipo</th>
                                <th>IP</th>
                                <th>País</th>
                                <th>Virtual Host</th>
                                <th>User Agent</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td colspan="8" class="loading">Cargando...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <script src="/static/dashboard.js"></script>
</body>
</html>'''

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

/* Filtros de logs históricos */
.filters-section {
    margin-bottom: 25px;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
}

.filters-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    align-items: end;
}

.filter-group {
    display: flex;
    flex-direction: column;
}

.filter-group label {
    font-weight: 500;
    margin-bottom: 5px;
    color: #2c3e50;
    font-size: 0.9rem;
}

.filter-input {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 0.9rem;
    background: white;
}

.filter-input:focus {
    outline: none;
    border-color: #3498db;
    box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.btn-primary, .btn-secondary {
    padding: 10px 15px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
    transition: background-color 0.2s;
}

.btn-primary {
    background: #3498db;
    color: white;
}

.btn-primary:hover {
    background: #2980b9;
}

.btn-secondary {
    background: #95a5a6;
    color: white;
}

.btn-secondary:hover:not(:disabled) {
    background: #7f8c8d;
}

.btn-secondary:disabled {
    background: #bdc3c7;
    cursor: not-allowed;
}

/* Resultados históricos */
.historical-results {
    margin-top: 20px;
}

.results-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    padding: 10px 0;
    border-bottom: 1px solid #e9ecef;
}

.results-info span {
    font-weight: 500;
    color: #2c3e50;
}

.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 15px;
    margin-top: 20px;
    padding: 15px 0;
}

.pagination button {
    min-width: 100px;
}

#page-numbers {
    display: flex;
    gap: 5px;
    align-items: center;
}

.page-number {
    padding: 5px 10px;
    border: 1px solid #ddd;
    background: white;
    cursor: pointer;
    border-radius: 3px;
    font-size: 0.9rem;
}

.page-number.active {
    background: #3498db;
    color: white;
    border-color: #3498db;
}

.page-number:hover:not(.active) {
    background: #f8f9fa;
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

    .filters-grid {
        grid-template-columns: 1fr;
    }

    .results-info {
        flex-direction: column;
        gap: 10px;
        text-align: center;
    }

    .pagination {
        flex-direction: column;
        gap: 10px;
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
        this.currentPage = 1;
        this.currentFilters = {};
        this.init();
    }

    init() {
        this.connectWebSocket();
        this.loadInitialData();
        this.setupHistoricalLogsHandlers();

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
            this.loadPhpStatus(),
            this.loadFilterOptions()
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

    async loadFilterOptions() {
        try {
            const response = await fetch('/api/logs/filter-options');
            const data = await response.json();

            if (data.success) {
                this.populateFilterOptions(data.options);
            }
        } catch (error) {
            console.error('Error cargando opciones de filtro:', error);
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

    setupHistoricalLogsHandlers() {
        // Botón aplicar filtros
        document.getElementById('apply-filters').addEventListener('click', () => {
            this.currentPage = 1;
            this.loadHistoricalLogs();
        });

        // Botón limpiar filtros
        document.getElementById('clear-filters').addEventListener('click', () => {
            this.clearFilters();
        });

        // Paginación
        document.getElementById('prev-page').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.loadHistoricalLogs();
            }
        });

        document.getElementById('next-page').addEventListener('click', () => {
            this.currentPage++;
            this.loadHistoricalLogs();
        });
    }

    populateFilterOptions(options) {
        // Poblar select de IPs
        const ipSelect = document.getElementById('filter-ip');
        ipSelect.innerHTML = '<option value="">Todas las IPs</option>';
        (options.top_ips || []).forEach(ip => {
            ipSelect.innerHTML += `<option value="${ip}">${ip}</option>`;
        });

        // Poblar select de virtual hosts
        const vhostSelect = document.getElementById('filter-vhost');
        vhostSelect.innerHTML = '<option value="">Todos los hosts</option>';
        (options.virtual_hosts || []).forEach(vhost => {
            vhostSelect.innerHTML += `<option value="${vhost}">${vhost}</option>`;
        });

        // Poblar select de status codes
        const statusSelect = document.getElementById('filter-status');
        statusSelect.innerHTML = '<option value="">Todos los códigos</option>';
        (options.status_codes || []).forEach(status => {
            statusSelect.innerHTML += `<option value="${status}">${status}</option>`;
        });

        // Poblar select de métodos HTTP
        const methodSelect = document.getElementById('filter-method');
        methodSelect.innerHTML = '<option value="">Todos los métodos</option>';
        (options.methods || []).forEach(method => {
            methodSelect.innerHTML += `<option value="${method}">${method}</option>`;
        });
    }

    async loadHistoricalLogs() {
        const tbody = document.querySelector('#historical-logs tbody');
        tbody.innerHTML = '<tr><td colspan="9" class="loading">Cargando logs históricos...</td></tr>';

        try {
            // Recopilar filtros
            const filters = this.getFilters();

            // Construir URL con parámetros
            const params = new URLSearchParams({
                page: this.currentPage,
                limit: 50,
                ...filters
            });

            const response = await fetch(`/api/logs/historical?${params}`);
            const result = await response.json();

            if (result.success) {
                this.displayHistoricalLogs(result.data);
            } else {
                tbody.innerHTML = `<tr><td colspan="9" class="loading">Error: ${result.error}</td></tr>`;
            }
        } catch (error) {
            console.error('Error cargando logs históricos:', error);
            tbody.innerHTML = '<tr><td colspan="9" class="loading">Error cargando logs históricos</td></tr>';
        }
    }

    getFilters() {
        const filters = {};

        const startDate = document.getElementById('start-date').value;
        if (startDate) filters.start_date = new Date(startDate).toISOString();

        const endDate = document.getElementById('end-date').value;
        if (endDate) filters.end_date = new Date(endDate).toISOString();

        const ip = document.getElementById('filter-ip').value;
        if (ip) filters.ip = ip;

        const vhost = document.getElementById('filter-vhost').value;
        if (vhost) filters.virtual_host = vhost;

        const status = document.getElementById('filter-status').value;
        if (status) filters.status_code = status;

        const method = document.getElementById('filter-method').value;
        if (method) filters.method = method;

        const searchText = document.getElementById('search-text').value;
        if (searchText) filters.search_text = searchText;

        return filters;
    }

    displayHistoricalLogs(data) {
        const tbody = document.querySelector('#historical-logs tbody');
        const { logs, total_count, page, total_pages, has_next, has_prev } = data;

        // Actualizar información de resultados
        document.getElementById('results-count').textContent = `${total_count} resultados`;
        document.getElementById('pagination-info').textContent = `Página ${page} de ${total_pages}`;

        // Actualizar botones de paginación
        document.getElementById('prev-page').disabled = !has_prev;
        document.getElementById('next-page').disabled = !has_next;

        // Mostrar logs
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="loading">No se encontraron logs con los filtros aplicados</td></tr>';
            return;
        }

        tbody.innerHTML = logs.map(log => {
            const timestamp = new Date(log.timestamp).toLocaleString();
            const statusClass = this.getStatusClass(log.status_code);

            return `
                <tr>
                    <td>${timestamp}</td>
                    <td>${log.ip}</td>
                    <td>${log.country_name || log.country_code}</td>
                    <td>${log.method}</td>
                    <td title="${log.path}">${this.truncateText(log.path, 30)}</td>
                    <td class="${statusClass}">${log.status_code}</td>
                    <td>${log.virtual_host}</td>
                    <td title="${log.user_agent}">${this.truncateText(log.user_agent, 40)}</td>
                    <td>${log.response_time ? log.response_time.toFixed(3) + 's' : 'N/A'}</td>
                </tr>
            `;
        }).join('');
    }

    clearFilters() {
        document.getElementById('start-date').value = '';
        document.getElementById('end-date').value = '';
        document.getElementById('filter-ip').value = '';
        document.getElementById('filter-vhost').value = '';
        document.getElementById('filter-status').value = '';
        document.getElementById('filter-method').value = '';
        document.getElementById('search-text').value = '';

        // Limpiar tabla
        const tbody = document.querySelector('#historical-logs tbody');
        tbody.innerHTML = '<tr><td colspan="9" class="loading">Haga clic en "Aplicar Filtros" para cargar logs históricos</td></tr>';

        // Resetear paginación
        this.currentPage = 1;
        document.getElementById('results-count').textContent = '0 resultados';
        document.getElementById('pagination-info').textContent = 'Página 1 de 1';
    }

    truncateText(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    getStatusClass(statusCode) {
        if (statusCode >= 200 && statusCode < 300) return 'status-200';
        if (statusCode >= 300 && statusCode < 400) return 'status-300';
        if (statusCode >= 400 && statusCode < 500) return 'status-400';
        if (statusCode >= 500) return 'status-500';
        return '';
    }
}

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
                <h2>📝 Últimas Requests (Tiempo Real)</h2>
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

            <!-- Logs Históricos -->
            <div class="card full-width">
                <h2>🗄️ Logs Históricos (MongoDB)</h2>

                <!-- Filtros -->
                <div class="filters-section">
                    <div class="filters-grid">
                        <div class="filter-group">
                            <label for="start-date">Fecha Inicio:</label>
                            <input type="datetime-local" id="start-date" class="filter-input">
                        </div>
                        <div class="filter-group">
                            <label for="end-date">Fecha Fin:</label>
                            <input type="datetime-local" id="end-date" class="filter-input">
                        </div>
                        <div class="filter-group">
                            <label for="filter-ip">IP:</label>
                            <select id="filter-ip" class="filter-input">
                                <option value="">Todas las IPs</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <label for="filter-vhost">Virtual Host:</label>
                            <select id="filter-vhost" class="filter-input">
                                <option value="">Todos los hosts</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <label for="filter-status">Status Code:</label>
                            <select id="filter-status" class="filter-input">
                                <option value="">Todos los códigos</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <label for="filter-method">Método HTTP:</label>
                            <select id="filter-method" class="filter-input">
                                <option value="">Todos los métodos</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <label for="search-text">Buscar en Path/User-Agent:</label>
                            <input type="text" id="search-text" class="filter-input" placeholder="Texto a buscar...">
                        </div>
                        <div class="filter-group">
                            <button id="apply-filters" class="btn-primary">🔍 Aplicar Filtros</button>
                            <button id="clear-filters" class="btn-secondary">🗑️ Limpiar</button>
                        </div>
                    </div>
                </div>

                <!-- Resultados -->
                <div class="historical-results">
                    <div class="results-info">
                        <span id="results-count">0 resultados</span>
                        <div class="pagination-info">
                            <span id="pagination-info">Página 1 de 1</span>
                        </div>
                    </div>

                    <div class="requests-table">
                        <table id="historical-logs">
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>IP</th>
                                    <th>País</th>
                                    <th>Método</th>
                                    <th>Path</th>
                                    <th>Status</th>
                                    <th>Virtual Host</th>
                                    <th>User Agent</th>
                                    <th>Tiempo Resp.</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr><td colspan="9" class="loading">Haga clic en "Aplicar Filtros" para cargar logs históricos</td></tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Paginación -->
                    <div class="pagination">
                        <button id="prev-page" class="btn-secondary" disabled>← Anterior</button>
                        <span id="page-numbers"></span>
                        <button id="next-page" class="btn-secondary" disabled>Siguiente →</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="/static/dashboard.js"></script>
</body>
</html>'''

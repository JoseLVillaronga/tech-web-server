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

    escapeHtml(value) {
        if (value === null || value === undefined) return '';
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
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
                <div class="vhost-domain">${this.escapeHtml(vhost.domain)}</div>
                <div class="vhost-details">
                    📁 ${this.escapeHtml(vhost.document_root)}<br>
                    🐘 PHP ${this.escapeHtml(vhost.php_version)} ${vhost.php_enabled ? '(Habilitado)' : '(Deshabilitado)'}<br>
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
                <div class="php-version">PHP ${this.escapeHtml(php.version)}</div>
                <div class="php-details">
                    Estado: ${php.status === 'online' ? '🟢 Online' : '🔴 Offline'}<br>
                    Socket: ${this.escapeHtml(php.socket)}
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
            const statusNum = Number(req.status) || 0;
            const statusClass = `status-${Math.floor(statusNum / 100) * 100}`;

            return `
                <tr>
                    <td>${this.escapeHtml(time)}</td>
                    <td>${this.escapeHtml(req.path)}</td>
                    <td class="${statusClass}">${this.escapeHtml(statusNum)}</td>
                    <td>${this.escapeHtml(req.type)}</td>
                    <td>${this.escapeHtml(req.ip)}</td>
                    <td>${this.escapeHtml(req.country_code || 'XX')}</td>
                    <td>${this.escapeHtml(req.virtual_host || 'unknown')}</td>
                    <td>${this.escapeHtml(req.user_agent)}</td>
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
            const safeIp = this.escapeHtml(ip);
            ipSelect.innerHTML += `<option value="${safeIp}">${safeIp}</option>`;
        });

        // Poblar select de virtual hosts
        const vhostSelect = document.getElementById('filter-vhost');
        vhostSelect.innerHTML = '<option value="">Todos los hosts</option>';
        (options.virtual_hosts || []).forEach(vhost => {
            const safeVhost = this.escapeHtml(vhost);
            vhostSelect.innerHTML += `<option value="${safeVhost}">${safeVhost}</option>`;
        });

        // Poblar select de status codes
        const statusSelect = document.getElementById('filter-status');
        statusSelect.innerHTML = '<option value="">Todos los códigos</option>';
        (options.status_codes || []).forEach(status => {
            const safeStatus = this.escapeHtml(status);
            statusSelect.innerHTML += `<option value="${safeStatus}">${safeStatus}</option>`;
        });

        // Poblar select de métodos HTTP
        const methodSelect = document.getElementById('filter-method');
        methodSelect.innerHTML = '<option value="">Todos los métodos</option>';
        (options.methods || []).forEach(method => {
            const safeMethod = this.escapeHtml(method);
            methodSelect.innerHTML += `<option value="${safeMethod}">${safeMethod}</option>`;
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
                tbody.innerHTML = `<tr><td colspan="9" class="loading">Error: ${this.escapeHtml(result.error)}</td></tr>`;
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

        // Actualizar números de página
        this.updatePageNumbers(page, total_pages);

        // Mostrar logs
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="loading">No se encontraron logs con los filtros aplicados</td></tr>';
            return;
        }

        tbody.innerHTML = logs.map(log => {
            const timestamp = new Date(log.timestamp).toLocaleString();
            const statusClass = this.getStatusClass(log.status_code);
            const rawPath = log.path || '';
            const rawUa = log.user_agent || '';

            return `
                <tr>
                    <td>${this.escapeHtml(timestamp)}</td>
                    <td>${this.escapeHtml(log.ip)}</td>
                    <td>${this.escapeHtml(log.country_name || log.country_code)}</td>
                    <td>${this.escapeHtml(log.method)}</td>
                    <td title="${this.escapeHtml(rawPath)}">${this.escapeHtml(this.truncateText(rawPath, 30))}</td>
                    <td class="${statusClass}">${this.escapeHtml(log.status_code)}</td>
                    <td>${this.escapeHtml(log.virtual_host)}</td>
                    <td title="${this.escapeHtml(rawUa)}">${this.escapeHtml(this.truncateText(rawUa, 40))}</td>
                    <td>${log.response_time ? Number(log.response_time).toFixed(3) + 's' : 'N/A'}</td>
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

    updatePageNumbers(currentPage, totalPages) {
        const pageNumbersContainer = document.getElementById('page-numbers');

        if (totalPages <= 1) {
            pageNumbersContainer.innerHTML = '';
            return;
        }

        const pageNumbers = this.generatePageNumbers(currentPage, totalPages);

        pageNumbersContainer.innerHTML = pageNumbers.map(item => {
            if (item === '...') {
                return '<span class="page-ellipsis">...</span>';
            } else {
                const isActive = item === currentPage ? 'active' : '';
                return `<button class="page-number ${isActive}" data-page="${item}">${item}</button>`;
            }
        }).join('');

        // Agregar event listeners a los números de página
        pageNumbersContainer.querySelectorAll('.page-number').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const page = parseInt(e.target.dataset.page);
                if (page !== this.currentPage) {
                    this.currentPage = page;
                    this.loadHistoricalLogs();
                }
            });
        });
    }

    generatePageNumbers(current, total) {
        const pages = [];
        const maxVisible = window.innerWidth < 768 ? 5 : 7;

        if (total <= maxVisible) {
            for (let i = 1; i <= total; i++) {
                pages.push(i);
            }
        } else {
            pages.push(1);

            let start = Math.max(2, current - 1);
            let end = Math.min(total - 1, current + 1);

            if (current <= 3) {
                end = Math.min(total - 1, 4);
            } else if (current >= total - 2) {
                start = Math.max(2, total - 3);
            }

            if (start > 2) {
                pages.push('...');
            }

            for (let i = start; i <= end; i++) {
                pages.push(i);
            }

            if (end < total - 1) {
                pages.push('...');
            }

            if (total > 1) {
                pages.push(total);
            }
        }

        return pages;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});


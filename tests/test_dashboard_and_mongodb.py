"""
Tests unitarios para la modularización del Dashboard y blindaje de MongoDB (Etapa 5).
"""

import re
import unittest
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from dashboard.dashboard_server import DashboardServer
from config.config_manager import config


class TestDashboardModularization(unittest.IsolatedAsyncioTestCase):
    """Verifica carga de assets estáticos externos, anti-XSS y no-mutación de vhosts."""

    async def test_static_assets_load_from_files(self):
        dashboard = DashboardServer()
        html = await dashboard._get_dashboard_html()
        css = await dashboard._get_dashboard_css()
        js = await dashboard._get_dashboard_js()

        self.assertIn('Tech Web Server Dashboard', html)
        self.assertIn('.stats-grid', css)
        self.assertIn('escapeHtml(value)', js)

    async def test_api_virtual_hosts_does_not_mutate_global_config(self):
        dashboard = DashboardServer()
        vhosts_before = [dict(vh) for vh in config.get_virtual_hosts()]

        req = SimpleNamespace()
        response = await dashboard.api_virtual_hosts(req)
        self.assertEqual(response.status, 200)

        # Verificar que los diccionarios originales en config no fueron mutados con 'status' o 'document_root_exists'
        for original, current in zip(vhosts_before, config.get_virtual_hosts()):
            self.assertEqual(set(original.keys()), set(current.keys()))


if __name__ == '__main__':
    unittest.main()


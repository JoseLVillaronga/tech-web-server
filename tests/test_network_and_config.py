"""
Tests unitarios para utilidades de red y gestor de configuración (Etapa 1).
"""

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from utils.network import get_real_client_ip, is_valid_ip
from config.config_manager import ConfigManager


class TestNetworkUtils(unittest.TestCase):
    """Pruebas unitarias para resolución de IP y validación."""

    def test_is_valid_ip(self):
        self.assertTrue(is_valid_ip('127.0.0.1'))
        self.assertTrue(is_valid_ip('192.168.1.50'))
        self.assertTrue(is_valid_ip('::1'))
        self.assertFalse(is_valid_ip('not-an-ip'))
        self.assertFalse(is_valid_ip('999.999.999.999'))
        self.assertFalse(is_valid_ip(''))

    def test_get_real_client_ip_with_proxy_headers(self):
        req = SimpleNamespace(
            remote='127.0.0.1',
            headers={'X-Forwarded-For': '203.0.113.195, 70.41.3.18'}
        )
        self.assertEqual(get_real_client_ip(req, proxy_support_enabled=True), '203.0.113.195')

    def test_get_real_client_ip_proxy_disabled(self):
        req = SimpleNamespace(
            remote='10.0.0.5',
            headers={'X-Forwarded-For': '203.0.113.195'}
        )
        self.assertEqual(get_real_client_ip(req, proxy_support_enabled=False), '10.0.0.5')

    def test_get_real_client_ip_invalid_header_fallback(self):
        req = SimpleNamespace(
            remote='10.0.0.8',
            headers={'X-Forwarded-For': 'malicious_input'}
        )
        self.assertEqual(get_real_client_ip(req, proxy_support_enabled=True), '10.0.0.8')


class TestConfigManagerKeys(unittest.TestCase):
    """Verifica que ConfigManager cargue las claves de proxy y bind IP."""

    def test_config_loads_bind_ip_and_proxy_support(self):
        cfg = ConfigManager()
        self.assertIsNotNone(cfg.get('dashboard_bind_ip'))
        self.assertIsInstance(cfg.get('proxy_support_enabled'), bool)


if __name__ == '__main__':
    unittest.main()


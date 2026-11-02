"""
Tests unitarios para SSLManager (Etapa 4).
"""

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from tls.ssl_manager import SSLManager


class TestSSLManager(unittest.TestCase):
    """Pruebas de resolución de certificados en ambos formatos (-cert.pem y .crt)."""

    def test_load_certificate_supports_both_naming_conventions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            (base / 'certs').mkdir()
            (base / 'private').mkdir()

            # Formato 1: {domain}-cert.pem y private/{domain}-key.pem
            (base / 'certs' / 'app1.local-cert.pem').write_text('dummy-cert')
            (base / 'private' / 'app1.local-key.pem').write_text('dummy-key')

            # Formato 2: {domain}.crt y private/{domain}.key
            (base / 'certs' / 'app2.local.crt').write_text('dummy-cert')
            (base / 'private' / 'app2.local.key').write_text('dummy-key')

            mgr = SSLManager(ssl_base_path=str(base))
            self.assertIsNotNone(mgr.load_certificate('app1.local'))
            self.assertIsNotNone(mgr.load_certificate('app2.local'))
            self.assertIsNone(mgr.load_certificate('nonexistent.local'))


if __name__ == '__main__':
    unittest.main()


"""
Tests unitarios para el protocolo binario FastCGI y PHPManager (Etapa 3).
"""

import asyncio
import struct
import tempfile
import unittest
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from php_fpm.fastcgi_client import FastCGIClient
from php_fpm.php_manager import PHPManager


class TestFastCGIProtocol(unittest.IsolatedAsyncioTestCase):
    """Pruebas de empaquetado, fragmentación y lectura exacta de tramas FastCGI."""

    def test_pack_and_unpack_fcgi_record(self):
        client = FastCGIClient('/tmp/nonexistent.sock')
        payload = b'Hello FastCGI'
        record = client._pack_fcgi_record(FastCGIClient.FCGI_STDOUT, 1, payload)
        req_type, req_id, unpacked = client._unpack_fcgi_record(record)
        self.assertEqual(req_type, FastCGIClient.FCGI_STDOUT)
        self.assertEqual(req_id, 1)
        self.assertEqual(unpacked, payload)
        # El registro total debe ser múltiplo de 8 bytes
        self.assertEqual(len(record) % 8, 0)

    def test_pack_params_long_values(self):
        client = FastCGIClient('/tmp/nonexistent.sock')
        long_val = 'A' * 300
        packed = client._pack_params({'SHORT': 'ok', 'LONG_PARAM': long_val})
        self.assertGreater(len(packed), 300)

    async def test_execute_php_handles_fragmented_unix_stream(self):
        """Verifica que readexactly ensamble correctamente tramas enviadas en fragmentos pequeños."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sock_path = str(Path(tmpdir) / 'test-fpm.sock')
            client = FastCGIClient(sock_path, timeout=5)

            response_body = b"Content-type: text/html\r\n\r\n<h1>OK</h1>"
            stdout_record = client._pack_fcgi_record(FastCGIClient.FCGI_STDOUT, 1, response_body)
            end_record = client._pack_fcgi_record(FastCGIClient.FCGI_END_REQUEST, 1, b'\x00' * 8)
            full_stream = stdout_record + end_record

            async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
                # Leer hasta recibir STDIN vacío
                await reader.read(1024)
                # Enviar la respuesta fragmentada de a 3 bytes para forzar lecturas parciales
                for i in range(0, len(full_stream), 3):
                    writer.write(full_stream[i:i + 3])
                    await writer.drain()
                    await asyncio.sleep(0.001)
                writer.close()
                await writer.wait_closed()

            server = await asyncio.start_unix_server(handle_client, path=sock_path)
            try:
                stdout_data, stderr_data = await client.execute_php(
                    '/var/www/index.php',
                    {'REQUEST_METHOD': 'GET', 'REQUEST_URI': '/'}
                )
                self.assertEqual(stdout_data, response_body)
                self.assertEqual(stderr_data, b'')
            finally:
                server.close()
                await server.wait_closed()


class TestPHPManagerParams(unittest.TestCase):
    """Pruebas de construcción de variables CGI tras RewriteEngine."""

    def test_script_name_uses_resolved_rewritten_target(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docroot = Path(tmpdir)
            index_php = docroot / 'index.php'
            index_php.touch()

            vhost = {
                'domain': 'example.local',
                'port': 3080,
                'document_root': str(docroot)
            }
            req = SimpleNamespace(
                headers={'Host': 'example.local'},
                path='/usuarios/123',
                path_qs='/usuarios/123?foo=bar',
                method='GET',
                scheme='http',
                remote='127.0.0.1'
            )

            manager = PHPManager()
            params = manager._build_fcgi_params(req, vhost, str(index_php), 'url=/usuarios/123&foo=bar')

            self.assertEqual(params['SCRIPT_NAME'], '/index.php')
            self.assertEqual(params['PHP_SELF'], '/index.php')
            self.assertEqual(params['REQUEST_URI'], '/usuarios/123?foo=bar')
            self.assertEqual(params['QUERY_STRING'], 'url=/usuarios/123&foo=bar')

    def test_x_forwarded_proto_sets_https_on(self):
        """Verifica que detrás de Caddy (X-Forwarded-Proto: https) se establezca HTTPS=on en PHP."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docroot = Path(tmpdir)
            index_php = docroot / 'index.php'
            index_php.touch()

            vhost = {
                'domain': 'example.local',
                'port': 3080,
                'document_root': str(docroot)
            }
            req = SimpleNamespace(
                headers={'Host': 'example.local', 'X-Forwarded-Proto': 'https'},
                path='/',
                path_qs='/',
                method='GET',
                scheme='http',
                remote='127.0.0.1'
            )

            manager = PHPManager()
            params = manager._build_fcgi_params(req, vhost, str(index_php), '')
            self.assertEqual(params.get('HTTPS'), 'on')


if __name__ == '__main__':
    unittest.main()

